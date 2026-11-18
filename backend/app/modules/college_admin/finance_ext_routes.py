"""Finance extensions routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
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
from app.modules.college_admin.finance_ext_service import (
    allocate_department_budget,
    approve_expense,
    approve_purchase_request,
    budget_report,
    budget_utilization,
    create_expense,
    create_purchase_order,
    create_purchase_request,
    create_vendor_invoice,
    upsert_budget,
    upsert_vendor,
)

router = APIRouter()


@router.put("/budgets", response_model=ApiResponse[BudgetRead])
async def budget_upsert_route(payload: BudgetUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[BudgetRead]:
    return success_response(await upsert_budget(scope, user, payload), request_id=get_request_id())


@router.get("/budgets/{budget_id}/utilization", response_model=ApiResponse[BudgetRead])
async def budget_util_route(budget_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[BudgetRead]:
    return success_response(await budget_utilization(scope, budget_id), request_id=get_request_id())


@router.put("/budgets/allocations", response_model=ApiResponse[dict])
async def budget_alloc_route(payload: BudgetAllocationUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await allocate_department_budget(scope, user, payload), request_id=get_request_id())


@router.post("/expenses", response_model=ApiResponse[dict])
async def expense_create_route(payload: ExpenseCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await create_expense(scope, user, payload), request_id=get_request_id())


@router.post("/expenses/{expense_id}/approve", response_model=ApiResponse[dict])
async def expense_approve_route(expense_id: str, payload: ExpenseApprove, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await approve_expense(scope, user, expense_id, payload), request_id=get_request_id())


@router.put("/vendors", response_model=ApiResponse[dict])
async def vendor_route(payload: VendorUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await upsert_vendor(scope, user, payload), request_id=get_request_id())


@router.post("/purchase-requests", response_model=ApiResponse[dict])
async def pr_create_route(payload: PurchaseRequestCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await create_purchase_request(scope, user, payload), request_id=get_request_id())


@router.post("/purchase-requests/{request_id}/approve", response_model=ApiResponse[dict])
async def pr_approve_route(request_id: str, payload: PurchaseRequestApprove, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await approve_purchase_request(scope, user, request_id, payload), request_id=get_request_id())


@router.post("/purchase-orders", response_model=ApiResponse[dict])
async def po_create_route(payload: PurchaseOrderCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await create_purchase_order(scope, user, payload), request_id=get_request_id())


@router.post("/vendor-invoices", response_model=ApiResponse[dict])
async def invoice_route(payload: VendorInvoiceCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[dict]:
    return success_response(await create_vendor_invoice(scope, user, payload), request_id=get_request_id())


@router.get("/budgets/{budget_id}/report", response_model=ApiResponse[BudgetReportRead])
async def budget_report_route(budget_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]) -> ApiResponse[BudgetReportRead]:
    return success_response(await budget_report(scope, budget_id), request_id=get_request_id())