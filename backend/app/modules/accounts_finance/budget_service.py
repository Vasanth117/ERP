"""Finance Staff budget planning, approval, allocation, and utilization."""

import uuid
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase9_enums import FinanceBudgetStatus
from app.modules.accounts_finance.phase9_models import (
    FinanceBudget,
    FinanceBudgetAllocation,
    FinanceBudgetApprovalHistory,
    FinanceBudgetCommitment,
    FinanceBudgetLine,
    FinanceBudgetRevision,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_budget_approve,
    authorize_finance_budget_manage,
    authorize_finance_budget_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit


async def _budget_history(tenant_id, budget_id: str, from_status: str | None, to_status: str, actor_id) -> None:
    await FinanceBudgetApprovalHistory(
        tenant_id=tenant_id,
        history_id=f"fbh_{uuid.uuid4().hex[:12]}",
        budget_id=budget_id,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor_id,
    ).insert()


async def create_budget(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_budget_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    budget_id = f"bgt_{uuid.uuid4().hex[:10]}"
    dept = to_object_id(payload["department_id"], "department_id") if payload.get("department_id") else None
    campus = to_object_id(payload["campus_id"], "campus_id") if payload.get("campus_id") else None
    doc = FinanceBudget(
        tenant_id=tenant_id,
        budget_id=budget_id,
        budget_code=payload["budget_code"],
        budget_name=payload["budget_name"],
        financial_year_id=payload["financial_year_id"],
        budget_category=payload.get("budget_category") or "operational",
        department_id=dept,
        campus_id=campus,
        cost_centre_code=payload.get("cost_centre_code"),
        total_amount=round_money(payload["total_amount"]),
        owner_id=to_object_id(payload["owner_id"], "owner_id") if payload.get("owner_id") else None,
        justification=payload.get("justification"),
        document_refs=payload.get("document_refs") or [],
        created_by=scope.user_id,
    )
    await doc.insert()
    await _budget_history(tenant_id, budget_id, None, FinanceBudgetStatus.DRAFT.value, scope.user_id)
    return {"budget_id": budget_id, "status": doc.status.value}


async def add_budget_line(scope: AccessScope, budget_id: str, payload: dict[str, Any]) -> dict:
    authorize_finance_budget_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    budget = await FinanceBudget.find_one(Eq(FinanceBudget.tenant_id, tenant_id), Eq(FinanceBudget.budget_id, budget_id))
    if budget is None or budget.status not in (FinanceBudgetStatus.DRAFT, FinanceBudgetStatus.UNDER_REVIEW):
        raise AppError(code="CONFLICT", message="Budget not editable", status_code=409)
    line_id = f"bgl_{uuid.uuid4().hex[:10]}"
    await FinanceBudgetLine(
        tenant_id=tenant_id,
        line_id=line_id,
        budget_id=budget_id,
        category=payload["category"],
        period_code=payload.get("period_code"),
        amount=round_money(payload["amount"]),
        note=payload.get("note"),
    ).insert()
    return {"line_id": line_id}


async def submit_budget(scope: AccessScope, budget_id: str) -> dict:
    authorize_finance_budget_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    budget = await FinanceBudget.find_one(Eq(FinanceBudget.tenant_id, tenant_id), Eq(FinanceBudget.budget_id, budget_id))
    if budget is None:
        raise AppError(code="NOT_FOUND", message="Budget not found", status_code=404)
    prev = budget.status.value
    budget.status = FinanceBudgetStatus.SUBMITTED
    budget.updated_at = utcnow()
    await budget.save()
    await _budget_history(tenant_id, budget_id, prev, budget.status.value, scope.user_id)
    return {"budget_id": budget_id, "status": budget.status.value}


async def approve_budget(scope: AccessScope, budget_id: str) -> dict:
    authorize_finance_budget_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    budget = await FinanceBudget.find_one(Eq(FinanceBudget.tenant_id, tenant_id), Eq(FinanceBudget.budget_id, budget_id))
    if budget is None:
        raise AppError(code="NOT_FOUND", message="Budget not found", status_code=404)
    if budget.status != FinanceBudgetStatus.SUBMITTED:
        raise AppError(code="CONFLICT", message="Budget not submitted", status_code=409)
    prev = budget.status.value
    budget.status = FinanceBudgetStatus.ACTIVE
    budget.approved_by = scope.user_id
    budget.updated_at = utcnow()
    await budget.save()
    await _budget_history(tenant_id, budget_id, prev, budget.status.value, scope.user_id)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.budget.approve",
        module="accounts_finance",
        resource_type="finance_budget",
        resource_id=budget_id,
    )
    return {"budget_id": budget_id, "status": budget.status.value}


async def allocate_budget(scope: AccessScope, budget_id: str, payload: dict[str, Any]) -> dict:
    authorize_finance_budget_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    budget = await FinanceBudget.find_one(Eq(FinanceBudget.tenant_id, tenant_id), Eq(FinanceBudget.budget_id, budget_id))
    if budget is None or budget.status != FinanceBudgetStatus.ACTIVE:
        raise AppError(code="CONFLICT", message="Budget must be active", status_code=409)
    amount = round_money(payload["allocated_amount"])
    existing = await FinanceBudgetAllocation.find(Eq(FinanceBudgetAllocation.tenant_id, tenant_id), Eq(FinanceBudgetAllocation.budget_id, budget_id)).to_list()
    if round_money(sum(a.allocated_amount for a in existing) + amount) > budget.total_amount:
        raise AppError(code="BUDGET_LIMIT", message="Allocation exceeds approved budget", status_code=409)
    allocation_id = f"ball_{uuid.uuid4().hex[:10]}"
    await FinanceBudgetAllocation(
        tenant_id=tenant_id,
        allocation_id=allocation_id,
        budget_id=budget_id,
        department_id=to_object_id(payload["department_id"], "department_id") if payload.get("department_id") else None,
        cost_centre_code=payload.get("cost_centre_code"),
        project_code=payload.get("project_code"),
        allocated_amount=amount,
        period_code=payload.get("period_code"),
    ).insert()
    return {"allocation_id": allocation_id}


async def record_commitment(scope: AccessScope, budget_id: str, payload: dict[str, Any]) -> dict:
    authorize_finance_budget_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    amount = round_money(payload["amount"])
    ref_type = payload["reference_type"]
    ref_id = payload["reference_id"]
    dup = await FinanceBudgetCommitment.find_one(
        Eq(FinanceBudgetCommitment.tenant_id, tenant_id),
        Eq(FinanceBudgetCommitment.reference_type, ref_type),
        Eq(FinanceBudgetCommitment.reference_id, ref_id),
    )
    if dup:
        return {"commitment_id": dup.commitment_id, "idempotent": True}
    util = await budget_utilization(scope, budget_id)
    if util["available"] < amount:
        raise AppError(code="BUDGET_LIMIT", message="Insufficient available budget", status_code=409)
    commitment_id = f"bcm_{uuid.uuid4().hex[:10]}"
    await FinanceBudgetCommitment(
        tenant_id=tenant_id,
        commitment_id=commitment_id,
        budget_id=budget_id,
        allocation_id=payload.get("allocation_id"),
        reference_type=ref_type,
        reference_id=ref_id,
        amount=amount,
        note=payload.get("note"),
    ).insert()
    return {"commitment_id": commitment_id}


async def budget_utilization(scope: AccessScope, budget_id: str) -> dict:
    authorize_finance_budget_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    budget = await FinanceBudget.find_one(Eq(FinanceBudget.tenant_id, tenant_id), Eq(FinanceBudget.budget_id, budget_id))
    if budget is None:
        raise AppError(code="NOT_FOUND", message="Budget not found", status_code=404)
    allocations = await FinanceBudgetAllocation.find(Eq(FinanceBudgetAllocation.tenant_id, tenant_id), Eq(FinanceBudgetAllocation.budget_id, budget_id)).to_list()
    commitments = await FinanceBudgetCommitment.find(
        Eq(FinanceBudgetCommitment.tenant_id, tenant_id),
        Eq(FinanceBudgetCommitment.budget_id, budget_id),
        Eq(FinanceBudgetCommitment.status, "open"),
    ).to_list()
    allocated = round_money(sum(a.allocated_amount for a in allocations))
    committed = round_money(sum(c.amount for c in commitments))
    available = round_money(budget.total_amount - committed)
    utilization_pct = round_money((committed / budget.total_amount * 100) if budget.total_amount else 0)
    return {
        "budget_id": budget_id,
        "approved": budget.total_amount,
        "allocated": allocated,
        "committed": committed,
        "available": available,
        "utilization_percentage": utilization_pct,
        "overspent": committed > budget.total_amount,
    }


async def budget_overview(scope: AccessScope) -> dict:
    authorize_finance_budget_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    budgets = await FinanceBudget.find(Eq(FinanceBudget.tenant_id, tenant_id)).to_list()
    total_annual = round_money(sum(b.total_amount for b in budgets if b.status == FinanceBudgetStatus.ACTIVE))
    pending = sum(1 for b in budgets if b.status == FinanceBudgetStatus.SUBMITTED)
    overspent = 0
    for b in budgets:
        if b.status != FinanceBudgetStatus.ACTIVE:
            continue
        util = await budget_utilization(scope, b.budget_id)
        if util["overspent"]:
            overspent += 1
    return {
        "total_annual_budget": total_annual,
        "pending_approvals": pending,
        "active_budgets": sum(1 for b in budgets if b.status == FinanceBudgetStatus.ACTIVE),
        "overspent_budgets": overspent,
    }


async def request_budget_revision(scope: AccessScope, budget_id: str, revised_amount: float, reason: str) -> dict:
    authorize_finance_budget_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    budget = await FinanceBudget.find_one(Eq(FinanceBudget.tenant_id, tenant_id), Eq(FinanceBudget.budget_id, budget_id))
    if budget is None:
        raise AppError(code="NOT_FOUND", message="Budget not found", status_code=404)
    revision_id = f"brev_{uuid.uuid4().hex[:10]}"
    await FinanceBudgetRevision(
        tenant_id=tenant_id,
        revision_id=revision_id,
        budget_id=budget_id,
        previous_amount=budget.total_amount,
        revised_amount=round_money(revised_amount),
        reason=reason,
        requested_by=scope.user_id,
    ).insert()
    return {"revision_id": revision_id, "status": "submitted"}


async def approve_budget_revision(scope: AccessScope, revision_id: str) -> dict:
    authorize_finance_budget_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rev = await FinanceBudgetRevision.find_one(Eq(FinanceBudgetRevision.tenant_id, tenant_id), Eq(FinanceBudgetRevision.revision_id, revision_id))
    if rev is None or rev.status != "submitted":
        raise AppError(code="CONFLICT", message="Revision not pending", status_code=409)
    budget = await FinanceBudget.find_one(Eq(FinanceBudget.tenant_id, tenant_id), Eq(FinanceBudget.budget_id, rev.budget_id))
    if budget is None:
        raise AppError(code="NOT_FOUND", message="Budget not found", status_code=404)
    budget.total_amount = rev.revised_amount
    budget.updated_at = utcnow()
    await budget.save()
    rev.status = "approved"
    rev.approved_by = scope.user_id
    await rev.save()
    return {"budget_id": budget.budget_id, "total_amount": budget.total_amount}