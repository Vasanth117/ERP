"""Fee concession policies, applications, awards and waivers."""

from typing import Any
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.financial_aid_posting import post_concession_credit, post_waiver_credit
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase5_enums import ConcessionApplicationStatus
from app.modules.accounts_finance.phase5_models import (
    FeeConcessionApprovalHistory,
    FeeConcessionCategory,
    FeeConcessionPolicy,
    StudentFeeConcessionApplication,
    StudentFeeConcessionAward,
    StudentFeeWaiver,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_concession_approve,
    authorize_finance_concession_manage,
    authorize_finance_concession_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_models import FeeConcession, StudentFeeInvoice
from app.modules.accounts_finance.phase5_models import StudentScholarshipAward
from app.modules.students.integrations.student_finance_reader import student_programme_code


async def list_categories(scope: AccessScope) -> list[dict[str, Any]]:
    authorize_finance_concession_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rows = await FeeConcessionCategory.find(Eq(FeeConcessionCategory.tenant_id, tenant_id)).to_list()
    return [{"category_id": r.category_id, "code": r.code, "name": r.name, "description": r.description, "active": r.active} for r in rows]


async def upsert_category(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_concession_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    category_id = payload.get("category_id") or f"fcc_{uuid4().hex[:10]}"
    row = await FeeConcessionCategory.find_one(
        Eq(FeeConcessionCategory.tenant_id, tenant_id),
        Eq(FeeConcessionCategory.category_id, category_id),
    )
    data = {
        "code": payload["code"],
        "name": payload["name"],
        "description": payload.get("description"),
        "active": bool(payload.get("active", True)),
    }
    if row:
        for k, v in data.items():
            setattr(row, k, v)
        await row.save()
    else:
        row = await FeeConcessionCategory(tenant_id=tenant_id, category_id=category_id, **data).insert()
    return {"category_id": row.category_id, "code": row.code, "name": row.name, "active": row.active}


async def upsert_policy(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_concession_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    policy_id = payload.get("policy_id") or f"fcp_{uuid4().hex[:10]}"
    row = await FeeConcessionPolicy.find_one(
        Eq(FeeConcessionPolicy.tenant_id, tenant_id),
        Eq(FeeConcessionPolicy.policy_id, policy_id),
    )
    data = {
        "policy_code": payload["policy_code"],
        "name": payload["name"],
        "description": payload.get("description"),
        "category_id": payload.get("category_id"),
        "applicable_programmes": payload.get("applicable_programmes") or [],
        "applicable_fee_categories": payload.get("applicable_fee_categories") or [],
        "concession_type": payload.get("concession_type", "fixed"),
        "fixed_amount": payload.get("fixed_amount"),
        "percent_amount": payload.get("percent_amount"),
        "max_limit": payload.get("max_limit"),
        "academic_year_label": payload.get("academic_year_label"),
        "effective_from": payload.get("effective_from"),
        "effective_to": payload.get("effective_to"),
        "document_required": bool(payload.get("document_required", False)),
        "approval_hierarchy": payload.get("approval_hierarchy") or [],
        "stacking_rules": payload.get("stacking_rules") or {},
        "active": bool(payload.get("active", True)),
        "updated_at": utcnow(),
    }
    if row:
        for k, v in data.items():
            setattr(row, k, v)
        await row.save()
    else:
        row = await FeeConcessionPolicy(tenant_id=tenant_id, policy_id=policy_id, created_at=utcnow(), **data).insert()
    return {"policy_id": row.policy_id, "policy_code": row.policy_code, "name": row.name, "stacking_rules": row.stacking_rules}


async def _validate_stacking(
    tenant_id,
    student_user_id,
    policy: FeeConcessionPolicy,
    proposed_amount: float,
    invoice: StudentFeeInvoice | None,
) -> None:
    rules = policy.stacking_rules or {}
    max_combined = rules.get("max_combined_amount")
    max_percent = rules.get("max_combined_percent")
    base = invoice.amount if invoice else proposed_amount

    scholarships = await StudentScholarshipAward.find(
        Eq(StudentScholarshipAward.tenant_id, tenant_id),
        Eq(StudentScholarshipAward.student_user_id, student_user_id),
    ).to_list()
    active_scholarship = sum(a.approved_amount for a in scholarships if a.status.value in ("active", "approved"))

    concessions = await StudentFeeConcessionAward.find(
        Eq(StudentFeeConcessionAward.tenant_id, tenant_id),
        Eq(StudentFeeConcessionAward.student_user_id, student_user_id),
    ).to_list()
    active_concession = sum(c.approved_amount for c in concessions if c.status in (ConcessionApplicationStatus.ACTIVE, ConcessionApplicationStatus.APPROVED))

    waivers = await StudentFeeWaiver.find(
        Eq(StudentFeeWaiver.tenant_id, tenant_id),
        Eq(StudentFeeWaiver.student_user_id, student_user_id),
    ).to_list()
    active_waiver = sum(w.waived_amount for w in waivers if w.status == "approved")

    total_aid = round_money(active_scholarship + active_concession + active_waiver + proposed_amount)
    if max_combined is not None and total_aid > float(max_combined):
        raise AppError(code="CONFLICT", message="Combined aid exceeds policy maximum", status_code=409)
    if max_percent is not None and base > 0:
        if (total_aid / base) * 100 > float(max_percent):
            raise AppError(code="CONFLICT", message="Combined aid percent exceeds policy limit", status_code=409)
    if rules.get("allow_with_scholarship") is False and active_scholarship > 0:
        raise AppError(code="CONFLICT", message="Policy does not allow stacking with scholarships", status_code=409)


async def submit_concession_application(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_concession_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    student_user_id = to_object_id(payload["student_user_id"], "student_user_id")
    policy = await FeeConcessionPolicy.find_one(
        Eq(FeeConcessionPolicy.tenant_id, tenant_id),
        Eq(FeeConcessionPolicy.policy_id, payload["policy_id"]),
    )
    if policy is None or not policy.active:
        raise AppError(code="NOT_FOUND", message="Concession policy not found", status_code=404)
    prog = await student_programme_code(tenant_id, student_user_id)
    if policy.applicable_programmes and prog and prog not in policy.applicable_programmes:
        raise AppError(code="FORBIDDEN", message="Student programme not covered by policy", status_code=403)

    application_id = f"cca_{uuid4().hex[:12]}"
    row = await StudentFeeConcessionApplication(
        tenant_id=tenant_id,
        application_id=application_id,
        student_user_id=student_user_id,
        policy_id=policy.policy_id,
        category_id=policy.category_id,
        assessment_id=payload.get("assessment_id"),
        invoice_id=payload.get("invoice_id"),
        reason=payload["reason"],
        requested_amount=payload.get("requested_amount"),
        requested_percent=payload.get("requested_percent"),
        document_refs=payload.get("document_refs") or [],
        academic_year_label=payload.get("academic_year_label"),
        semester_label=payload.get("semester_label"),
        status=ConcessionApplicationStatus.SUBMITTED,
        requested_by=scope.user_id,
    ).insert()
    await FeeConcessionApprovalHistory(
        tenant_id=tenant_id,
        history_id=f"cah_{uuid4().hex[:8]}",
        target_type="concession_application",
        target_id=application_id,
        action="submit",
        actor_id=scope.user_id,
        note=payload["reason"],
    ).insert()
    return {"application_id": row.application_id, "status": row.status.value}


async def approve_concession_application(
    scope: AccessScope,
    application_id: str,
    *,
    approved_amount: float | None = None,
) -> dict[str, Any]:
    authorize_finance_concession_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    app = await StudentFeeConcessionApplication.find_one(
        Eq(StudentFeeConcessionApplication.tenant_id, tenant_id),
        Eq(StudentFeeConcessionApplication.application_id, application_id),
    )
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    policy = await FeeConcessionPolicy.find_one(
        Eq(FeeConcessionPolicy.tenant_id, tenant_id),
        Eq(FeeConcessionPolicy.policy_id, app.policy_id),
    )
    if policy is None:
        raise AppError(code="NOT_FOUND", message="Policy not found", status_code=404)

    invoice = None
    if app.invoice_id:
        invoice = await StudentFeeInvoice.find_one(
            Eq(StudentFeeInvoice.tenant_id, tenant_id),
            Eq(StudentFeeInvoice.invoice_id, app.invoice_id),
        )

    if approved_amount is not None:
        amount = round_money(approved_amount)
    elif app.requested_amount is not None:
        amount = round_money(app.requested_amount)
    elif policy.concession_type == "percent" and policy.percent_amount and invoice:
        amount = round_money(invoice.amount * policy.percent_amount / 100)
    elif policy.fixed_amount is not None:
        amount = round_money(policy.fixed_amount)
    else:
        raise AppError(code="VALIDATION_ERROR", message="Approved amount required", status_code=422)

    if policy.max_limit is not None and amount > policy.max_limit:
        amount = round_money(policy.max_limit)
    await _validate_stacking(tenant_id, app.student_user_id, policy, amount, invoice)

    award_id = f"fca_{uuid4().hex[:12]}"
    award = await StudentFeeConcessionAward(
        tenant_id=tenant_id,
        award_id=award_id,
        application_id=application_id,
        student_user_id=app.student_user_id,
        policy_id=app.policy_id,
        approved_amount=amount,
        invoice_id=app.invoice_id,
        assessment_id=app.assessment_id,
        status=ConcessionApplicationStatus.ACTIVE,
        approved_by=scope.user_id,
        effective_from=utcnow().date(),
    ).insert()

    await post_concession_credit(
        tenant_id=tenant_id,
        student_user_id=app.student_user_id,
        amount=amount,
        award_id=award_id,
        invoice_id=app.invoice_id,
        academic_year_label=app.academic_year_label,
        semester_label=app.semester_label,
        posted_by=scope.user_id,
    )
    award.ledger_posted = True
    await award.save()

    legacy_id = f"con_{award_id[-12:]}"
    await FeeConcession(
        tenant_id=tenant_id,
        student_user_id=app.student_user_id,
        concession_id=legacy_id,
        title=policy.name,
        amount=amount,
        policy_id=policy.policy_id,
        award_id=award_id,
        published=True,
        effective_from=award.effective_from,
    ).insert()

    app.status = ConcessionApplicationStatus.APPROVED
    app.updated_at = utcnow()
    await app.save()

    await FeeConcessionApprovalHistory(
        tenant_id=tenant_id,
        history_id=f"cah_{uuid4().hex[:8]}",
        target_type="concession_application",
        target_id=application_id,
        action="approve",
        actor_id=scope.user_id,
        note=f"award={award_id}",
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="concession_award_approved",
        module="accounts_finance",
        resource_type="student_fee_concession_award",
        resource_id=award_id,
        metadata={"amount": amount},
    )
    return {"award_id": award_id, "approved_amount": amount, "status": app.status.value}


async def reject_concession_application(scope: AccessScope, application_id: str, reason: str) -> dict[str, Any]:
    authorize_finance_concession_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    app = await StudentFeeConcessionApplication.find_one(
        Eq(StudentFeeConcessionApplication.tenant_id, tenant_id),
        Eq(StudentFeeConcessionApplication.application_id, application_id),
    )
    if app is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    app.status = ConcessionApplicationStatus.REJECTED
    app.updated_at = utcnow()
    await app.save()
    return {"application_id": application_id, "status": app.status.value, "reason": reason}


async def list_concession_applications(scope: AccessScope, pagination: Pagination, student_user_id: str | None = None) -> Page[dict[str, Any]]:
    authorize_finance_concession_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query: dict[str, Any] = {"tenant_id": tenant_id}
    if student_user_id:
        query["student_user_id"] = to_object_id(student_user_id, "student_user_id")
    total = await StudentFeeConcessionApplication.find(query).count()
    rows = (
        await StudentFeeConcessionApplication.find(query)
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [
        {
            "application_id": r.application_id,
            "student_user_id": str(r.student_user_id),
            "policy_id": r.policy_id,
            "status": r.status.value,
            "requested_amount": r.requested_amount,
            "invoice_id": r.invoice_id,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def approve_waiver(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_concession_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    student_user_id = to_object_id(payload["student_user_id"], "student_user_id")
    waiver_id = f"wvr_{uuid4().hex[:12]}"
    original = round_money(payload["original_amount"])
    waived = round_money(payload["waived_amount"])
    if waived > original:
        raise AppError(code="VALIDATION_ERROR", message="Waiver exceeds original amount", status_code=422)
    remaining = round_money(original - waived)

    invoice_id = payload.get("invoice_id")
    policy_id = payload.get("policy_id")
    if policy_id:
        policy = await FeeConcessionPolicy.find_one(
            Eq(FeeConcessionPolicy.tenant_id, tenant_id),
            Eq(FeeConcessionPolicy.policy_id, policy_id),
        )
        if policy:
            invoice = None
            if invoice_id:
                invoice = await StudentFeeInvoice.find_one(
                    Eq(StudentFeeInvoice.tenant_id, tenant_id),
                    Eq(StudentFeeInvoice.invoice_id, invoice_id),
                )
            await _validate_stacking(tenant_id, student_user_id, policy, waived, invoice)

    row = await StudentFeeWaiver(
        tenant_id=tenant_id,
        waiver_id=waiver_id,
        student_user_id=student_user_id,
        waiver_type=payload.get("waiver_type", "partial"),
        original_amount=original,
        waived_amount=waived,
        remaining_amount=remaining,
        invoice_id=invoice_id,
        assessment_id=payload.get("assessment_id"),
        reason=payload["reason"],
        document_refs=payload.get("document_refs") or [],
        requested_by=scope.user_id,
        approved_by=scope.user_id,
        status="approved",
        effective_date=utcnow().date(),
    ).insert()

    await post_waiver_credit(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        amount=waived,
        waiver_id=waiver_id,
        invoice_id=invoice_id,
        academic_year_label=payload.get("academic_year_label"),
        semester_label=payload.get("semester_label"),
        posted_by=scope.user_id,
    )
    row.ledger_posted = True
    await row.save()
    return {"waiver_id": waiver_id, "waived_amount": waived, "remaining_amount": remaining}


async def revoke_concession_award(scope: AccessScope, award_id: str, reason: str) -> dict[str, Any]:
    authorize_finance_concession_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    award = await StudentFeeConcessionAward.find_one(
        Eq(StudentFeeConcessionAward.tenant_id, tenant_id),
        Eq(StudentFeeConcessionAward.award_id, award_id),
    )
    if award is None:
        raise AppError(code="NOT_FOUND", message="Award not found", status_code=404)
    award.status = ConcessionApplicationStatus.REVOKED
    await award.save()
    legacy = await FeeConcession.find_one(
        Eq(FeeConcession.tenant_id, tenant_id),
        Eq(FeeConcession.award_id, award_id),
    )
    if legacy:
        legacy.published = False
        await legacy.save()
    await FeeConcessionApprovalHistory(
        tenant_id=tenant_id,
        history_id=f"cah_{uuid4().hex[:8]}",
        target_type="concession_award",
        target_id=award_id,
        action="revoke",
        actor_id=scope.user_id,
        note=reason,
    ).insert()
    return {"award_id": award_id, "status": award.status.value, "reason": reason}