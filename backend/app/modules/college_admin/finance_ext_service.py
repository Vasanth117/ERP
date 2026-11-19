"""Institutional finance extensions service."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.finance_admin_models import FinancialApprovalRecord
from app.modules.college_admin.finance_ext_models import (
    BudgetStatus,
    DepartmentBudgetAllocation,
    ExpenseStatus,
    InstitutionBudget,
    InstitutionBudgetTransaction,
    InstitutionExpenseRecord,
    InstitutionPurchaseOrder,
    InstitutionPurchaseRequest,
    InstitutionVendorInvoice,
    InstitutionVendorRecord,
    InvoicePaymentStatus,
    PurchaseOrderStatus,
    PurchaseRequestStatus,
)
from app.modules.college_admin.finance_ext_schemas import (
    BudgetAllocationUpsert,
    BudgetRead,
    BudgetReportRead,
    BudgetUpsert,
    ExpenseApprove,
    ExpenseCreate,
    PurchaseOrderCreate,
    PurchaseRequestApprove,
    PurchaseRequestCreate,
    VendorInvoiceCreate,
    VendorUpsert,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.college_admin.workflow_admin_schemas import WorkflowInstanceStart
from app.modules.college_admin.workflow_admin_service import start_workflow_instance


async def _record_financial_approval(
    tenant_id: PydanticObjectId,
    actor_id: PydanticObjectId,
    *,
    scope_key: str,
    resource_type: str,
    resource_id: str,
    decision: str,
) -> None:
    await FinancialApprovalRecord(
        tenant_id=tenant_id,
        scope=scope_key,
        resource_type=resource_type,
        resource_id=resource_id,
        decision=decision,
        actor_id=actor_id,
    ).insert()


async def upsert_budget(scope: AccessScope, user: User, payload: BudgetUpsert) -> BudgetRead:
    authorize(scope, Permission.FINANCE_EXT_BUDGET)
    tenant_id = require_college_tenant_scope(scope)
    bid = payload.budget_id.strip()
    doc = await InstitutionBudget.find_one(Eq(InstitutionBudget.tenant_id, tenant_id), Eq(InstitutionBudget.budget_id, bid))
    if doc is None:
        doc = InstitutionBudget(
            tenant_id=tenant_id,
            budget_id=bid,
            label=payload.label,
            fiscal_year=payload.fiscal_year,
            period_start=payload.period_start,
            period_end=payload.period_end,
            total_amount=payload.total_amount,
            status=payload.status,
            updated_by=user.id,
        )
        await doc.insert()
    else:
        if doc.status == BudgetStatus.CLOSED:
            raise AppError(code="FORBIDDEN", message="Closed budget cannot change", status_code=403)
        doc.label = payload.label
        doc.fiscal_year = payload.fiscal_year
        doc.period_start = payload.period_start
        doc.period_end = payload.period_end
        doc.total_amount = payload.total_amount
        doc.status = payload.status
        doc.updated_by = user.id
        doc.updated_at = utcnow()
        await doc.save()
    await append_institution_audit(tenant_id, actor_id=user.id, action="finance_ext.budget.upsert", module="finance_ext", resource_type="budget", resource_id=bid)
    return await budget_utilization(scope, bid)


async def budget_utilization(scope: AccessScope, budget_id: str) -> BudgetRead:
    authorize(scope, Permission.FINANCE_EXT_READ)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionBudget.find_one(Eq(InstitutionBudget.tenant_id, tenant_id), Eq(InstitutionBudget.budget_id, budget_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Budget not found", status_code=404)
    allocs = await DepartmentBudgetAllocation.find(
        Eq(DepartmentBudgetAllocation.tenant_id, tenant_id),
        Eq(DepartmentBudgetAllocation.budget_id, budget_id),
    ).to_list()
    utilized = sum(a.utilized_amount for a in allocs)
    txs = await InstitutionBudgetTransaction.find(
        Eq(InstitutionBudgetTransaction.tenant_id, tenant_id),
        Eq(InstitutionBudgetTransaction.budget_id, budget_id),
    ).count()
    return BudgetRead(
        budget_id=doc.budget_id,
        label=doc.label,
        fiscal_year=doc.fiscal_year,
        total_amount=doc.total_amount,
        status=doc.status,
        utilized=utilized,
        variance=doc.total_amount - utilized,
    )


async def allocate_department_budget(scope: AccessScope, user: User, payload: BudgetAllocationUpsert) -> dict:
    authorize(scope, Permission.FINANCE_EXT_BUDGET)
    tenant_id = require_college_tenant_scope(scope)
    dept = to_object_id(payload.department_id, "department_id")
    await budget_utilization(scope, payload.budget_id)
    aid = payload.allocation_id.strip()
    total_alloc = await DepartmentBudgetAllocation.find(
        Eq(DepartmentBudgetAllocation.tenant_id, tenant_id),
        Eq(DepartmentBudgetAllocation.budget_id, payload.budget_id),
    ).to_list()
    new_total = sum(a.allocated_amount for a in total_alloc if a.allocation_id != aid) + payload.allocated_amount
    budget = await InstitutionBudget.find_one(Eq(InstitutionBudget.tenant_id, tenant_id), Eq(InstitutionBudget.budget_id, payload.budget_id))
    if budget and new_total > budget.total_amount:
        raise AppError(code="VALIDATION_ERROR", message="Allocation exceeds budget total", status_code=422)
    doc = await DepartmentBudgetAllocation.find_one(
        Eq(DepartmentBudgetAllocation.tenant_id, tenant_id),
        Eq(DepartmentBudgetAllocation.allocation_id, aid),
    )
    if doc is None:
        doc = DepartmentBudgetAllocation(
            tenant_id=tenant_id,
            allocation_id=aid,
            budget_id=payload.budget_id,
            department_id=dept,
            allocated_amount=payload.allocated_amount,
            actor_id=user.id,
        )
        await doc.insert()
    else:
        doc.allocated_amount = payload.allocated_amount
        doc.updated_at = utcnow()
        await doc.save()
    return {"allocation_id": aid, "allocated_amount": payload.allocated_amount}


async def create_expense(scope: AccessScope, user: User, payload: ExpenseCreate) -> dict:
    authorize(scope, Permission.FINANCE_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    eid = payload.expense_id.strip()
    if await InstitutionExpenseRecord.find_one(Eq(InstitutionExpenseRecord.tenant_id, tenant_id), Eq(InstitutionExpenseRecord.expense_id, eid)):
        raise AppError(code="CONFLICT", message="Expense id exists", status_code=409)
    dept = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    status = ExpenseStatus.PENDING_APPROVAL if payload.submit_for_approval else ExpenseStatus.DRAFT
    wf_id = None
    if payload.submit_for_approval:
        inst = await start_workflow_instance(
            scope,
            user,
            WorkflowInstanceStart(
                workflow_key="finance_approval",
                resource_type="institution_expense",
                resource_id=eid,
                context={"amount": payload.amount},
            ),
        )
        wf_id = inst.instance_id
    doc = InstitutionExpenseRecord(
        tenant_id=tenant_id,
        expense_id=eid,
        budget_id=payload.budget_id,
        department_id=dept,
        title=payload.title,
        amount=payload.amount,
        status=status,
        workflow_instance_id=wf_id,
        asset_id=payload.asset_id,
        actor_id=user.id,
    )
    await doc.insert()
    return {"expense_id": eid, "status": status.value, "workflow_instance_id": wf_id}


async def approve_expense(scope: AccessScope, user: User, expense_id: str, payload: ExpenseApprove) -> dict:
    authorize(scope, Permission.FINANCE_EXT_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionExpenseRecord.find_one(
        Eq(InstitutionExpenseRecord.tenant_id, tenant_id),
        Eq(InstitutionExpenseRecord.expense_id, expense_id),
    )
    if doc is None or doc.status != ExpenseStatus.PENDING_APPROVAL:
        raise AppError(code="VALIDATION_ERROR", message="Expense not pending approval", status_code=422)
    if not payload.approved:
        doc.status = ExpenseStatus.REJECTED
        await doc.save()
        await _record_financial_approval(tenant_id, user.id, scope_key="expense", resource_type="expense", resource_id=expense_id, decision="rejected")
        return {"expense_id": expense_id, "status": doc.status.value}
    doc.status = ExpenseStatus.APPROVED
    doc.approved_by = user.id
    doc.updated_at = utcnow()
    await doc.save()
    if doc.budget_id:
        tx_id = f"btx_{uuid4().hex[:10]}"
        await InstitutionBudgetTransaction(
            tenant_id=tenant_id,
            transaction_id=tx_id,
            budget_id=doc.budget_id,
            department_id=doc.department_id,
            amount=doc.amount,
            reference_type="expense",
            reference_id=expense_id,
        ).insert()
        if doc.department_id:
            alloc = await DepartmentBudgetAllocation.find_one(
                Eq(DepartmentBudgetAllocation.tenant_id, tenant_id),
                Eq(DepartmentBudgetAllocation.budget_id, doc.budget_id),
                Eq(DepartmentBudgetAllocation.department_id, doc.department_id),
            )
            if alloc:
                alloc.utilized_amount += doc.amount
                alloc.updated_at = utcnow()
                await alloc.save()
    await _record_financial_approval(tenant_id, user.id, scope_key="expense", resource_type="expense", resource_id=expense_id, decision="approved")
    await append_institution_audit(tenant_id, actor_id=user.id, action="finance_ext.expense.approve", module="finance_ext", resource_type="expense", resource_id=expense_id)
    return {"expense_id": expense_id, "status": doc.status.value}


async def upsert_vendor(scope: AccessScope, user: User, payload: VendorUpsert) -> dict:
    authorize(scope, Permission.FINANCE_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    vid = payload.vendor_id.strip()
    doc = await InstitutionVendorRecord.find_one(Eq(InstitutionVendorRecord.tenant_id, tenant_id), Eq(InstitutionVendorRecord.vendor_id, vid))
    if doc is None:
        doc = InstitutionVendorRecord(
            tenant_id=tenant_id,
            vendor_id=vid,
            name=payload.name,
            gstin=payload.gstin,
            contact_email=payload.contact_email,
        )
        await doc.insert()
    else:
        doc.name = payload.name
        doc.gstin = payload.gstin
        doc.contact_email = payload.contact_email
        doc.updated_at = utcnow()
        await doc.save()
    return {"vendor_id": vid, "name": doc.name}


async def create_purchase_request(scope: AccessScope, user: User, payload: PurchaseRequestCreate) -> dict:
    authorize(scope, Permission.FINANCE_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    rid = payload.request_id.strip()
    if await InstitutionPurchaseRequest.find_one(Eq(InstitutionPurchaseRequest.tenant_id, tenant_id), Eq(InstitutionPurchaseRequest.request_id, rid)):
        raise AppError(code="CONFLICT", message="Request exists", status_code=409)
    status = PurchaseRequestStatus.SUBMITTED if payload.submit else PurchaseRequestStatus.DRAFT
    wf_id = None
    if payload.submit:
        inst = await start_workflow_instance(
            scope,
            user,
            WorkflowInstanceStart(workflow_key="finance_approval", resource_type="purchase_request", resource_id=rid),
        )
        wf_id = inst.instance_id
    dept = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    await InstitutionPurchaseRequest(
        tenant_id=tenant_id,
        request_id=rid,
        vendor_id=payload.vendor_id,
        department_id=dept,
        budget_id=payload.budget_id,
        description=payload.description,
        estimated_amount=payload.estimated_amount,
        status=status,
        workflow_instance_id=wf_id,
        actor_id=user.id,
    ).insert()
    return {"request_id": rid, "status": status.value}


async def approve_purchase_request(scope: AccessScope, user: User, request_id: str, payload: PurchaseRequestApprove) -> dict:
    authorize(scope, Permission.FINANCE_EXT_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionPurchaseRequest.find_one(
        Eq(InstitutionPurchaseRequest.tenant_id, tenant_id),
        Eq(InstitutionPurchaseRequest.request_id, request_id),
    )
    if doc is None or doc.status != PurchaseRequestStatus.SUBMITTED:
        raise AppError(code="VALIDATION_ERROR", message="Request not submitted", status_code=422)
    doc.status = PurchaseRequestStatus.APPROVED if payload.approved else PurchaseRequestStatus.REJECTED
    doc.updated_at = utcnow()
    await doc.save()
    await _record_financial_approval(
        tenant_id,
        user.id,
        scope_key="procurement",
        resource_type="purchase_request",
        resource_id=request_id,
        decision="approved" if payload.approved else "rejected",
    )
    return {"request_id": request_id, "status": doc.status.value}


async def create_purchase_order(scope: AccessScope, user: User, payload: PurchaseOrderCreate) -> dict:
    authorize(scope, Permission.FINANCE_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    oid = payload.order_id.strip()
    if await InstitutionPurchaseOrder.find_one(Eq(InstitutionPurchaseOrder.tenant_id, tenant_id), Eq(InstitutionPurchaseOrder.order_id, oid)):
        raise AppError(code="CONFLICT", message="Order exists", status_code=409)
    vendor = await InstitutionVendorRecord.find_one(
        Eq(InstitutionVendorRecord.tenant_id, tenant_id),
        Eq(InstitutionVendorRecord.vendor_id, payload.vendor_id),
    )
    if vendor is None:
        raise AppError(code="NOT_FOUND", message="Vendor not found", status_code=404)
    if payload.request_id:
        pr = await InstitutionPurchaseRequest.find_one(
            Eq(InstitutionPurchaseRequest.tenant_id, tenant_id),
            Eq(InstitutionPurchaseRequest.request_id, payload.request_id),
        )
        if pr is None or pr.status != PurchaseRequestStatus.APPROVED:
            raise AppError(code="VALIDATION_ERROR", message="Approved purchase request required", status_code=422)
        pr.status = PurchaseRequestStatus.ORDERED
        await pr.save()
    await InstitutionPurchaseOrder(
        tenant_id=tenant_id,
        order_id=oid,
        request_id=payload.request_id,
        vendor_id=payload.vendor_id,
        total_amount=payload.total_amount,
        status=PurchaseOrderStatus.ISSUED,
        actor_id=user.id,
    ).insert()
    return {"order_id": oid, "status": PurchaseOrderStatus.ISSUED.value}


async def create_vendor_invoice(scope: AccessScope, user: User, payload: VendorInvoiceCreate) -> dict:
    authorize(scope, Permission.FINANCE_EXT_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    iid = payload.invoice_id.strip()
    await InstitutionVendorInvoice(
        tenant_id=tenant_id,
        invoice_id=iid,
        vendor_id=payload.vendor_id,
        order_id=payload.order_id,
        amount=payload.amount,
        due_date=payload.due_date,
        actor_id=user.id,
    ).insert()
    return {"invoice_id": iid, "payment_status": InvoicePaymentStatus.PENDING.value}


async def budget_report(scope: AccessScope, budget_id: str) -> BudgetReportRead:
    authorize(scope, Permission.FINANCE_EXT_READ)
    tenant_id = require_college_tenant_scope(scope)
    util = await budget_utilization(scope, budget_id)
    allocs = await DepartmentBudgetAllocation.find(
        Eq(DepartmentBudgetAllocation.tenant_id, tenant_id),
        Eq(DepartmentBudgetAllocation.budget_id, budget_id),
    ).to_list()
    expenses = await InstitutionExpenseRecord.find(
        Eq(InstitutionExpenseRecord.tenant_id, tenant_id),
        Eq(InstitutionExpenseRecord.budget_id, budget_id),
    ).count()
    return BudgetReportRead(
        budget_id=budget_id,
        total=util.total_amount,
        allocated=sum(a.allocated_amount for a in allocs),
        utilized=util.utilized,
        variance=util.variance,
        expense_count=expenses,
    )