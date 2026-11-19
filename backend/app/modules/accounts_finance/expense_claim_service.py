"""Employee expense claims, policies, advances and GL integration."""

import hashlib
import uuid
from datetime import date
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.period_lock_service import assert_period_open_for_date
from app.modules.accounts_finance.phase10_enums import ExpenseClaimStatus
from app.modules.accounts_finance.phase10_models import (
    DepartmentExpenseRecord,
    EmployeeAdvanceRecord,
    EmployeeAdvanceSettlement,
    EmployeeExpenseClaim,
    ExpenseApprovalHistory,
    ExpensePaymentRecord,
    FinanceExpenseCategory,
    FinanceExpensePolicy,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_expense_approve,
    authorize_finance_expense_manage,
    authorize_finance_expense_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit


async def seed_expense_categories(scope: AccessScope) -> dict:
    authorize_finance_expense_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    defaults = ["travel", "accommodation", "administrative", "laboratory", "training", "other"]
    created = 0
    for code in defaults:
        if await FinanceExpenseCategory.find_one(Eq(FinanceExpenseCategory.tenant_id, tenant_id), Eq(FinanceExpenseCategory.category_code, code)):
            continue
        await FinanceExpenseCategory(tenant_id=tenant_id, category_code=code, label=code.replace("_", " ").title()).insert()
        created += 1
    return {"created": created}


async def upsert_expense_policy(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_expense_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    policy_id = payload.get("policy_id") or f"pol_{uuid.uuid4().hex[:8]}"
    doc = await FinanceExpensePolicy.find_one(Eq(FinanceExpensePolicy.tenant_id, tenant_id), Eq(FinanceExpensePolicy.policy_id, policy_id))
    if doc is None:
        doc = FinanceExpensePolicy(
            tenant_id=tenant_id,
            policy_id=policy_id,
            category_code=payload["category_code"],
            max_amount=payload.get("max_amount"),
            per_day_limit=payload.get("per_day_limit"),
            requires_pre_approval=bool(payload.get("requires_pre_approval")),
            requires_documents=bool(payload.get("requires_documents", True)),
            eligible_roles=payload.get("eligible_roles") or [],
        )
        await doc.insert()
    else:
        doc.max_amount = payload.get("max_amount", doc.max_amount)
        doc.per_day_limit = payload.get("per_day_limit", doc.per_day_limit)
        doc.active = bool(payload.get("active", doc.active))
        await doc.save()
    return {"policy_id": policy_id}


async def _validate_policy(tenant_id, category_code: str, amount: float, role: str) -> None:
    policy = await FinanceExpensePolicy.find_one(
        Eq(FinanceExpensePolicy.tenant_id, tenant_id),
        Eq(FinanceExpensePolicy.category_code, category_code),
        Eq(FinanceExpensePolicy.active, True),
    )
    if policy and policy.max_amount is not None and amount > policy.max_amount:
        raise AppError(code="POLICY_LIMIT", message="Amount exceeds category limit", status_code=422)
    if policy and policy.eligible_roles and role not in policy.eligible_roles:
        raise AppError(code="POLICY_LIMIT", message="Role not eligible for category", status_code=403)


def _bill_fingerprint(document_refs: list[str]) -> str | None:
    if not document_refs:
        return None
    key = "|".join(sorted(document_refs))
    return hashlib.sha256(key.encode()).hexdigest()


async def create_expense_claim(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_expense_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    claim_id = payload.get("claim_id") or f"clm_{uuid.uuid4().hex[:10]}"
    requester = to_object_id(payload.get("requester_id") or str(scope.user_id), "requester_id")
    amount = round_money(payload["amount"])
    await _validate_policy(tenant_id, payload["category_code"], amount, scope.role.value if hasattr(scope.role, "value") else str(scope.role))
    fp = _bill_fingerprint(payload.get("document_refs") or [])
    if fp:
        dup = await EmployeeExpenseClaim.find_one(Eq(EmployeeExpenseClaim.tenant_id, tenant_id), Eq(EmployeeExpenseClaim.bill_fingerprint, fp))
        if dup:
            raise AppError(code="DUPLICATE_BILL", message="Duplicate supporting bill detected", status_code=409)
    status = ExpenseClaimStatus.SUBMITTED if payload.get("submit") else ExpenseClaimStatus.DRAFT
    dept = to_object_id(payload.get("department_id"), "department_id") if payload.get("department_id") else None
    claim = EmployeeExpenseClaim(
        tenant_id=tenant_id,
        claim_id=claim_id,
        claim_number=payload.get("claim_number") or claim_id,
        requester_id=requester,
        department_id=dept,
        category_code=payload["category_code"],
        expense_date=payload["expense_date"],
        amount=amount,
        currency=payload.get("currency") or "INR",
        description=payload["description"],
        business_purpose=payload.get("business_purpose"),
        vendor_id=payload.get("vendor_id"),
        document_refs=payload.get("document_refs") or [],
        finance_budget_id=payload.get("finance_budget_id"),
        cost_centre_code=payload.get("cost_centre_code"),
        bill_fingerprint=fp,
        status=status,
    )
    await claim.insert()
    return {"claim_id": claim_id, "status": status.value}


async def approve_expense_claim(scope: AccessScope, claim_id: str, *, approved: bool, note: str | None = None) -> dict:
    authorize_finance_expense_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    claim = await EmployeeExpenseClaim.find_one(Eq(EmployeeExpenseClaim.tenant_id, tenant_id), Eq(EmployeeExpenseClaim.claim_id, claim_id))
    if claim is None or claim.status != ExpenseClaimStatus.SUBMITTED:
        raise AppError(code="CONFLICT", message="Claim not submitted", status_code=409)
    if claim.requester_id == scope.user_id:
        raise AppError(code="FORBIDDEN", message="Cannot approve own expense claim", status_code=403)
    prev = claim.status.value
    claim.status = ExpenseClaimStatus.APPROVED if approved else ExpenseClaimStatus.REJECTED
    claim.approved_by = scope.user_id
    claim.updated_at = utcnow()
    await claim.save()
    await ExpenseApprovalHistory(
        tenant_id=tenant_id,
        history_id=f"eah_{uuid.uuid4().hex[:12]}",
        claim_id=claim_id,
        from_status=prev,
        to_status=claim.status.value,
        actor_id=scope.user_id,
        note=note,
    ).insert()
    if approved:
        claim.status = ExpenseClaimStatus.AWAITING_PAYMENT
        await claim.save()
        await _post_expense_gl(tenant_id, claim, scope.user_id)
    return {"claim_id": claim_id, "status": claim.status.value}


async def _post_expense_gl(tenant_id, claim: EmployeeExpenseClaim, actor_id) -> None:
    from app.modules.accounts_finance.gl_posting_service import post_mapped_event

    await post_mapped_event(
        tenant_id=tenant_id,
        event_type="expense_reimbursement",
        source_reference=claim.claim_id,
        amount=claim.amount,
        journal_date=claim.expense_date,
        narration=claim.description,
        posted_by=actor_id,
    )


async def pay_expense_claim(scope: AccessScope, claim_id: str, payment_reference: str) -> dict:
    authorize_finance_expense_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    await assert_period_open_for_date(tenant_id, date.today())
    claim = await EmployeeExpenseClaim.find_one(Eq(EmployeeExpenseClaim.tenant_id, tenant_id), Eq(EmployeeExpenseClaim.claim_id, claim_id))
    if claim is None or claim.status != ExpenseClaimStatus.AWAITING_PAYMENT:
        raise AppError(code="CONFLICT", message="Claim not awaiting payment", status_code=409)
    if not payment_reference:
        raise AppError(code="VALIDATION_ERROR", message="Payment reference required", status_code=400)
    record_id = f"epr_{uuid.uuid4().hex[:10]}"
    await ExpensePaymentRecord(
        tenant_id=tenant_id,
        payment_record_id=record_id,
        claim_id=claim_id,
        amount=claim.amount,
        payment_reference=payment_reference,
        created_by=scope.user_id,
    ).insert()
    claim.status = ExpenseClaimStatus.PAID
    claim.updated_at = utcnow()
    await claim.save()
    from app.modules.accounts_finance.gl_posting_service import post_mapped_event

    await post_mapped_event(
        tenant_id=tenant_id,
        event_type="expense_payment",
        source_reference=record_id,
        amount=claim.amount,
        journal_date=date.today(),
        narration=f"Reimbursement {claim.claim_number}",
        posted_by=scope.user_id,
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.expense.pay",
        module="accounts_finance",
        resource_type="expense_claim",
        resource_id=claim_id,
    )
    return {"claim_id": claim_id, "status": claim.status.value, "payment_record_id": record_id}


async def record_department_expense(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_expense_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    record_id = f"dexp_{uuid.uuid4().hex[:10]}"
    await DepartmentExpenseRecord(
        tenant_id=tenant_id,
        record_id=record_id,
        department_id=to_object_id(payload["department_id"], "department_id"),
        category_code=payload["category_code"],
        amount=round_money(payload["amount"]),
        expense_date=payload["expense_date"],
        finance_budget_id=payload.get("finance_budget_id"),
        cost_centre_code=payload.get("cost_centre_code"),
        description=payload["description"],
        created_by=scope.user_id,
    ).insert()
    return {"record_id": record_id}


async def create_advance(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_expense_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    advance_id = f"adv_{uuid.uuid4().hex[:10]}"
    await EmployeeAdvanceRecord(
        tenant_id=tenant_id,
        advance_id=advance_id,
        employee_id=to_object_id(payload["employee_id"], "employee_id"),
        amount=round_money(payload["amount"]),
        purpose=payload["purpose"],
        payment_reference=payload.get("payment_reference"),
    ).insert()
    return {"advance_id": advance_id}


async def settle_advance(scope: AccessScope, advance_id: str, claim_id: str, actual_amount: float) -> dict:
    authorize_finance_expense_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    adv = await EmployeeAdvanceRecord.find_one(Eq(EmployeeAdvanceRecord.tenant_id, tenant_id), Eq(EmployeeAdvanceRecord.advance_id, advance_id))
    if adv is None:
        raise AppError(code="NOT_FOUND", message="Advance not found", status_code=404)
    actual = round_money(actual_amount)
    used = min(adv.amount, actual)
    refund = round_money(max(0, adv.amount - actual))
    additional = round_money(max(0, actual - adv.amount))
    settlement_id = f"stl_{uuid.uuid4().hex[:10]}"
    await EmployeeAdvanceSettlement(
        tenant_id=tenant_id,
        settlement_id=settlement_id,
        advance_id=advance_id,
        claim_id=claim_id,
        advance_used=used,
        refund_due=refund,
        additional_payable=additional,
    ).insert()
    adv.status = "settled"
    await adv.save()
    return {"settlement_id": settlement_id, "refund_due": refund, "additional_payable": additional}


async def expense_reports(scope: AccessScope) -> dict:
    authorize_finance_expense_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    claims = await EmployeeExpenseClaim.find(Eq(EmployeeExpenseClaim.tenant_id, tenant_id)).to_list()
    return {
        "pending": sum(1 for c in claims if c.status == ExpenseClaimStatus.SUBMITTED),
        "awaiting_payment": sum(1 for c in claims if c.status == ExpenseClaimStatus.AWAITING_PAYMENT),
        "paid_total": round_money(sum(c.amount for c in claims if c.status == ExpenseClaimStatus.PAID)),
        "by_category": {},
    }