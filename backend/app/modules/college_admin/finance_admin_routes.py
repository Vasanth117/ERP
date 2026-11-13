"""College admin finance administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.finance_admin_schemas import (
    ConcessionCreate,
    FeeAssessmentCreate,
    FeeStructureRead,
    FeeStructureUpsert,
    FinancialPeriodUpsert,
    OfflineCollectionCreate,
    ReconciliationConfirm,
    RefundDecision,
)
from app.modules.college_admin.finance_admin_service import (
    approve_concession,
    create_concession,
    create_fee_assessment,
    decide_refund,
    finance_report,
    list_transactions,
    publish_fee_structure,
    reconcile_payment,
    record_offline_collection,
    request_refund,
    student_ledger,
    upsert_fee_structure,
    upsert_financial_period,
)

router = APIRouter()


@router.put("/fee-structures", response_model=ApiResponse[FeeStructureRead])
async def fee_structure_route(
    payload: FeeStructureUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FeeStructureRead]:
    return success_response(await upsert_fee_structure(scope, payload), request_id=get_request_id())


@router.post("/fee-structures/{structure_id}/publish", response_model=ApiResponse[FeeStructureRead])
async def publish_structure_route(
    structure_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FeeStructureRead]:
    return success_response(await publish_fee_structure(scope, structure_id), request_id=get_request_id())


@router.post("/assessments", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def assessment_route(
    payload: FeeAssessmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_fee_assessment(scope, payload), request_id=get_request_id())


@router.post("/collections/offline", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def offline_collection_route(
    payload: OfflineCollectionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await record_offline_collection(scope, payload), request_id=get_request_id())


@router.get("/transactions", response_model=ApiResponse[Page[dict]])
async def transactions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await list_transactions(scope, pagination), request_id=get_request_id())


@router.post("/reconciliation", response_model=ApiResponse[dict])
async def reconciliation_route(
    payload: ReconciliationConfirm,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await reconcile_payment(scope, payload), request_id=get_request_id())


@router.get("/ledger/{student_user_id}", response_model=ApiResponse[Page[dict]])
async def ledger_route(
    student_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await student_ledger(scope, student_user_id, pagination), request_id=get_request_id())


@router.post("/concessions", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def concession_route(
    payload: ConcessionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_concession(scope, payload), request_id=get_request_id())


@router.post("/concessions/{concession_id}/approve", response_model=ApiResponse[dict])
async def approve_concession_route(
    concession_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await approve_concession(scope, concession_id), request_id=get_request_id())


@router.post("/refunds", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def refund_request_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    student_user_id: Annotated[str, Query()],
    transaction_id: Annotated[str, Query()],
    amount: Annotated[float, Query(ge=0)],
) -> ApiResponse[dict]:
    return success_response(await request_refund(scope, student_user_id, transaction_id, amount), request_id=get_request_id())


@router.post("/refunds/decide", response_model=ApiResponse[dict])
async def refund_decide_route(
    payload: RefundDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await decide_refund(scope, payload), request_id=get_request_id())


@router.put("/periods", response_model=ApiResponse[dict])
async def financial_period_route(
    payload: FinancialPeriodUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_financial_period(scope, payload), request_id=get_request_id())


@router.get("/reports/summary", response_model=ApiResponse[dict])
async def finance_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await finance_report(scope), request_id=get_request_id())
