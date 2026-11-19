"""Employment change, probation, and contract routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.employment_change_schemas import (
    ContractRecordRead,
    ContractUpsert,
    EmploymentChangeCreate,
    EmploymentChangeDetailRead,
    EmploymentChangeOverview,
    EmploymentChangeRead,
    EmploymentChangeReview,
    ProbationApproachingItem,
    ProbationReviewRead,
    ProbationReviewUpsert,
)
from app.modules.hr.employment_change_service import (
    approve_probation_review,
    create_employment_change,
    dispatch_contract_expiry_reminders,
    employment_change_overview,
    get_employment_change,
    list_contracts,
    list_employment_changes,
    list_probation_approaching,
    process_due_employment_changes,
    review_employment_change,
    upsert_contract,
    upsert_probation_review,
)

router = APIRouter(prefix="/employment-changes", tags=["hr-employment"])


@router.get("/overview", response_model=ApiResponse[EmploymentChangeOverview])
async def overview_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await employment_change_overview(scope), request_id=get_request_id())


@router.get("/probation/approaching", response_model=ApiResponse[list[ProbationApproachingItem]])
async def probation_approaching_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    within_days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    return success_response(await list_probation_approaching(scope, within_days), request_id=get_request_id())


@router.get("/contracts", response_model=ApiResponse[Page[ContractRecordRead]])
async def list_contracts_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    employee_user_id: Annotated[str | None, Query()] = None,
):
    return success_response(await list_contracts(scope, pagination, employee_user_id), request_id=get_request_id())


@router.post("/contracts/reminders", response_model=ApiResponse[dict])
async def contract_reminders_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    within_days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    return success_response(await dispatch_contract_expiry_reminders(scope, within_days), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[EmploymentChangeRead]])
async def list_changes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    employee_user_id: Annotated[str | None, Query()] = None,
):
    return success_response(await list_employment_changes(scope, pagination, employee_user_id), request_id=get_request_id())


@router.post("", response_model=ApiResponse[EmploymentChangeRead])
async def create_change_route(
    payload: EmploymentChangeCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await create_employment_change(scope, payload), request_id=get_request_id())


@router.post("/{change_id}/review", response_model=ApiResponse[EmploymentChangeRead])
async def review_change_route(
    change_id: str,
    payload: EmploymentChangeReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await review_employment_change(scope, change_id, payload), request_id=get_request_id())


@router.post("/process-due", response_model=ApiResponse[dict])
async def process_due_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await process_due_employment_changes(scope), request_id=get_request_id())


@router.post("/probation-reviews", response_model=ApiResponse[ProbationReviewRead])
async def probation_review_route(
    payload: ProbationReviewUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await upsert_probation_review(scope, payload), request_id=get_request_id())


@router.post("/probation-reviews/{review_id}/decide", response_model=ApiResponse[ProbationReviewRead])
async def probation_decide_route(
    review_id: str,
    decision: Annotated[str, Query(pattern="^(confirm|extend|reject)$")],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await approve_probation_review(scope, review_id, decision), request_id=get_request_id())


@router.put("/contracts", response_model=ApiResponse[dict])
async def contract_upsert_route(
    payload: ContractUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await upsert_contract(scope, payload), request_id=get_request_id())


@router.get("/{change_id}", response_model=ApiResponse[EmploymentChangeDetailRead])
async def get_change_route(change_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await get_employment_change(scope, change_id), request_id=get_request_id())