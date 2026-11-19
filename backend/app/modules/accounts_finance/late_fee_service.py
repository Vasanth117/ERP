"""Late fee policies, assessment, posting and waivers."""

from datetime import date, timedelta
from typing import Any
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.installment_service import mark_overdue_installments
from app.modules.accounts_finance.ledger_posting_service import post_ledger_entry
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.payment_core import demand_outstanding, verified_payments_total
from app.modules.accounts_finance.phase4_enums import LedgerEntryType
from app.modules.accounts_finance.phase6_enums import LateFeeAssessmentStatus, LateFeeCalcType
from app.modules.accounts_finance.phase6_models import (
    LateFeePolicy,
    StudentInstallmentSchedule,
    StudentLateFeeAssessment,
    StudentLateFeeTransaction,
    StudentLateFeeWaiver,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_late_fee_approve,
    authorize_finance_late_fee_manage,
    authorize_finance_late_fee_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand


def _default_buckets() -> list[dict[str, Any]]:
    return [
        {"code": "not_due", "label": "Not Due", "min_days": None, "max_days": 0},
        {"code": "1_30", "label": "1-30 Days", "min_days": 1, "max_days": 30},
        {"code": "31_60", "label": "31-60 Days", "min_days": 31, "max_days": 60},
        {"code": "61_90", "label": "61-90 Days", "min_days": 61, "max_days": 90},
        {"code": "90_plus", "label": ">90 Days", "min_days": 91, "max_days": None},
    ]


def _calculate_fee(policy: LateFeePolicy, principal: float, overdue_days: int) -> float:
    if overdue_days <= policy.grace_days:
        return 0.0
    billable_days = overdue_days - policy.grace_days
    fee = 0.0
    if policy.calc_type == LateFeeCalcType.FIXED.value:
        fee = policy.fixed_amount
    elif policy.calc_type == LateFeeCalcType.PERCENT.value:
        fee = round_money(principal * policy.percent_rate / 100)
    elif policy.calc_type == LateFeeCalcType.DAILY.value:
        fee = round_money(policy.daily_rate * billable_days)
    elif policy.calc_type == LateFeeCalcType.PERIODIC.value:
        periods = max(1, billable_days // 30)
        fee = round_money(policy.fixed_amount * periods)
    if policy.max_late_fee is not None:
        fee = min(fee, round_money(policy.max_late_fee))
    return round_money(fee)


async def upsert_late_fee_policy(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_late_fee_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    policy_id = payload.get("policy_id") or f"lfp_{uuid4().hex[:10]}"
    row = await LateFeePolicy.find_one(Eq(LateFeePolicy.tenant_id, tenant_id), Eq(LateFeePolicy.policy_id, policy_id))
    data = {
        "policy_code": payload["policy_code"],
        "name": payload["name"],
        "calc_type": payload.get("calc_type", LateFeeCalcType.FIXED.value),
        "fixed_amount": float(payload.get("fixed_amount") or 0),
        "percent_rate": float(payload.get("percent_rate") or 0),
        "daily_rate": float(payload.get("daily_rate") or 0),
        "max_late_fee": payload.get("max_late_fee"),
        "grace_days": int(payload.get("grace_days") or 0),
        "fee_categories": payload.get("fee_categories") or [],
        "academic_year_label": payload.get("academic_year_label"),
        "student_categories": payload.get("student_categories") or [],
        "requires_approval": bool(payload.get("requires_approval", False)),
        "rounding_rule": payload.get("rounding_rule", "round_half_up"),
        "ageing_buckets": payload.get("ageing_buckets") or _default_buckets(),
        "effective_from": payload.get("effective_from"),
        "effective_to": payload.get("effective_to"),
        "active": bool(payload.get("active", True)),
        "updated_at": utcnow(),
    }
    if row:
        for k, v in data.items():
            setattr(row, k, v)
        await row.save()
    else:
        row = await LateFeePolicy(tenant_id=tenant_id, policy_id=policy_id, created_at=utcnow(), **data).insert()
    return {"policy_id": row.policy_id, "policy_code": row.policy_code, "active": row.active}


async def _active_policy(tenant_id, academic_year_label: str | None) -> LateFeePolicy | None:
    rows = await LateFeePolicy.find(Eq(LateFeePolicy.tenant_id, tenant_id), Eq(LateFeePolicy.active, True)).to_list()
    today = date.today()
    for row in rows:
        if row.effective_from and row.effective_from > today:
            continue
        if row.effective_to and row.effective_to < today:
            continue
        if academic_year_label and row.academic_year_label and row.academic_year_label != academic_year_label:
            continue
        return row
    return rows[0] if rows else None


async def run_late_fee_processing(scope: AccessScope, *, tenant_wide: bool = True) -> dict[str, Any]:
    authorize_finance_late_fee_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    return await _run_late_fee_for_tenant(tenant_id, actor_id=scope.user_id)


async def _run_late_fee_for_tenant(tenant_id, *, actor_id=None) -> dict[str, Any]:
    await mark_overdue_installments(tenant_id)
    today = date.today()
    generated = 0
    skipped = 0
    demands = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
    ).to_list()
    for demand in demands:
        if demand.status in (FeeDemandStatus.PAID, FeeDemandStatus.WAIVED):
            skipped += 1
            continue
        if demand.due_date >= today:
            skipped += 1
            continue
        outstanding = await demand_outstanding(tenant_id, demand)
        if outstanding <= 0:
            skipped += 1
            continue
        overdue_days = (today - demand.due_date).days
        policy = await _active_policy(tenant_id, demand.academic_year_label)
        if policy is None:
            skipped += 1
            continue
        fee = _calculate_fee(policy, outstanding, overdue_days)
        if fee <= 0:
            skipped += 1
            continue
        period_key = f"{demand.demand_id}:{today.isoformat()[:7]}"
        existing = await StudentLateFeeTransaction.find_one(
            Eq(StudentLateFeeTransaction.tenant_id, tenant_id),
            Eq(StudentLateFeeTransaction.posting_key, f"late_fee:{period_key}"),
        )
        if existing:
            skipped += 1
            continue

        assessment_id = f"lfa_{uuid4().hex[:10]}"
        status = LateFeeAssessmentStatus.PENDING if policy.requires_approval else LateFeeAssessmentStatus.APPROVED
        assessment = await StudentLateFeeAssessment(
            tenant_id=tenant_id,
            assessment_id=assessment_id,
            student_user_id=demand.student_user_id,
            demand_id=demand.demand_id,
            policy_id=policy.policy_id,
            principal_outstanding=outstanding,
            overdue_days=overdue_days,
            calculated_fee=fee,
            period_key=period_key,
            status=status,
        ).insert()

        if status == LateFeeAssessmentStatus.PENDING:
            skipped += 1
            continue

        await _post_late_fee_charge(tenant_id, demand, assessment, fee, actor_id)
        generated += 1

    await append_institution_audit(
        tenant_id,
        actor_id=actor_id,
        action="late_fee_batch_processed",
        module="accounts_finance",
        resource_type="late_fee_job",
        resource_id="tenant",
        metadata={"generated": generated, "skipped": skipped},
    )
    try:
        from app.modules.accounts_finance.finance_notify import enqueue_late_fee_applied

        if generated:
            await enqueue_late_fee_applied(tenant_id, generated)
    except Exception:
        pass
    return {"generated": generated, "skipped": skipped}


async def _post_late_fee_charge(tenant_id, demand: StudentFeeDemand, assessment: StudentLateFeeAssessment, fee: float, actor_id) -> None:
    posting_key = f"late_fee:{assessment.period_key}"
    entry = await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=demand.student_user_id,
        entry_type=LedgerEntryType.LATE_FEE.value,
        description=f"Late fee {assessment.period_key}",
        debit=fee,
        credit=0,
        source_reference=assessment.assessment_id,
        posting_key=posting_key,
        academic_year_label=demand.academic_year_label,
        semester_label=demand.semester_label,
        posted_by=actor_id,
    )
    demand.late_fee = round_money(demand.late_fee + fee)
    if demand.status == FeeDemandStatus.OPEN:
        demand.status = FeeDemandStatus.OVERDUE
    await demand.save()

    tx_ref = f"lftx_{uuid4().hex[:10]}"
    await StudentLateFeeTransaction(
        tenant_id=tenant_id,
        transaction_ref=tx_ref,
        assessment_id=assessment.assessment_id,
        student_user_id=demand.student_user_id,
        demand_id=demand.demand_id,
        amount=fee,
        posting_key=posting_key,
        ledger_entry_id=entry.entry_id,
    ).insert()
    assessment.status = LateFeeAssessmentStatus.POSTED
    await assessment.save()


async def approve_late_fee_assessment(scope: AccessScope, assessment_id: str) -> dict[str, Any]:
    authorize_finance_late_fee_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    assessment = await StudentLateFeeAssessment.find_one(
        Eq(StudentLateFeeAssessment.tenant_id, tenant_id),
        Eq(StudentLateFeeAssessment.assessment_id, assessment_id),
    )
    if assessment is None:
        raise AppError(code="NOT_FOUND", message="Assessment not found", status_code=404)
    if assessment.status != LateFeeAssessmentStatus.PENDING:
        raise AppError(code="CONFLICT", message="Assessment not pending", status_code=409)
    demand = await StudentFeeDemand.find_one(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        Eq(StudentFeeDemand.demand_id, assessment.demand_id),
    )
    if demand is None:
        raise AppError(code="NOT_FOUND", message="Demand not found", status_code=404)
    await _post_late_fee_charge(tenant_id, demand, assessment, assessment.calculated_fee, scope.user_id)
    return {"assessment_id": assessment_id, "status": assessment.status.value, "amount": assessment.calculated_fee}


async def waive_late_fee(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_late_fee_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    student_user_id = to_object_id(payload["student_user_id"], "student_user_id")
    waived = round_money(payload["waived_amount"])
    original = round_money(payload.get("original_late_fee", waived))
    waiver_id = f"lfw_{uuid4().hex[:12]}"
    assessment_id = payload.get("assessment_id")
    transaction_ref = payload.get("transaction_ref")

    row = await StudentLateFeeWaiver(
        tenant_id=tenant_id,
        waiver_id=waiver_id,
        assessment_id=assessment_id,
        transaction_ref=transaction_ref,
        student_user_id=student_user_id,
        original_late_fee=original,
        waived_amount=waived,
        reason=payload["reason"],
        requested_by=scope.user_id,
        approved_by=scope.user_id,
        effective_date=utcnow().date(),
    ).insert()

    entry = await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        entry_type=LedgerEntryType.LATE_FEE_WAIVER.value,
        description=f"Late fee waiver {waiver_id}",
        debit=0,
        credit=waived,
        source_reference=waiver_id,
        posting_key=f"late_fee_waiver:{waiver_id}",
        posted_by=scope.user_id,
    )
    row.ledger_entry_id = entry.entry_id
    await row.save()

    if assessment_id:
        assessment = await StudentLateFeeAssessment.find_one(
            Eq(StudentLateFeeAssessment.tenant_id, tenant_id),
            Eq(StudentLateFeeAssessment.assessment_id, assessment_id),
        )
        if assessment:
            assessment.status = LateFeeAssessmentStatus.WAIVED
            await assessment.save()

    demand_id = payload.get("demand_id")
    if demand_id:
        demand = await StudentFeeDemand.find_one(Eq(StudentFeeDemand.tenant_id, tenant_id), Eq(StudentFeeDemand.demand_id, demand_id))
        if demand:
            demand.late_fee = max(0.0, round_money(demand.late_fee - waived))
            await demand.save()

    return {"waiver_id": waiver_id, "waived_amount": waived, "ledger_entry_id": entry.entry_id}


def classify_ageing(overdue_days: int, buckets: list[dict]) -> str:
    if overdue_days <= 0:
        return "not_due"
    for b in buckets:
        mn = b.get("min_days")
        mx = b.get("max_days")
        if mn is not None and overdue_days < mn:
            continue
        if mx is not None and overdue_days > mx:
            continue
        return b.get("code", "unknown")
    return "90_plus"


async def list_late_fee_policies(scope: AccessScope) -> list[dict[str, Any]]:
    authorize_finance_late_fee_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rows = await LateFeePolicy.find(Eq(LateFeePolicy.tenant_id, tenant_id)).to_list()
    return [{"policy_id": r.policy_id, "policy_code": r.policy_code, "name": r.name, "active": r.active} for r in rows]