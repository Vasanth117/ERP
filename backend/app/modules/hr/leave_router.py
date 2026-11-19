"""Leave management routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.leave_schemas import (
    LeaveAdjustmentCreate,
    LeaveApplicationCreate,
    LeaveApplicationReview,
    LeaveBalanceRead,
    LeaveOverviewStats,
    LeavePolicyUpsert,
    LeaveReports,
    LeaveRequestRead,
    LeaveTypeConfigRead,
    LeaveTypeConfigUpsert,
)
from app.modules.hr.leave_service import (
    apply_leave_adjustment,
    create_leave_application,
    get_employee_balances,
    leave_overview,
    leave_reports,
    list_leave_requests,
    list_leave_types,
    review_leave_application,
    upsert_leave_policy,
    upsert_leave_type,
)

router = APIRouter(prefix="/leave", tags=["hr-leave"])


@router.get("/overview", response_model=ApiResponse[LeaveOverviewStats])
async def leave_overview_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await leave_overview(scope), request_id=get_request_id())


@router.get("/types", response_model=ApiResponse[list[LeaveTypeConfigRead]])
async def list_types_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_leave_types(scope), request_id=get_request_id())


@router.put("/types", response_model=ApiResponse[LeaveTypeConfigRead])
async def upsert_type_route(
    payload: LeaveTypeConfigUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await upsert_leave_type(scope, payload), request_id=get_request_id())


@router.get("/requests", response_model=ApiResponse[Page[LeaveRequestRead]])
async def list_requests_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[LeaveRequestStatus | None, Query()] = None,
):
    return success_response(await list_leave_requests(scope, pagination, status), request_id=get_request_id())


@router.post("/requests", response_model=ApiResponse[LeaveRequestRead])
async def create_request_route(
    payload: LeaveApplicationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await create_leave_application(scope, payload), request_id=get_request_id())


@router.post("/requests/{leave_id}/review", response_model=ApiResponse[LeaveRequestRead])
async def review_request_route(
    leave_id: str,
    payload: LeaveApplicationReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await review_leave_application(scope, leave_id, payload), request_id=get_request_id())


@router.post("/adjustments", response_model=ApiResponse[LeaveBalanceRead])
async def adjustment_route(
    payload: LeaveAdjustmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await apply_leave_adjustment(scope, payload), request_id=get_request_id())


@router.put("/policies", response_model=ApiResponse[dict])
async def leave_policy_route(
    payload: LeavePolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await upsert_leave_policy(scope, payload), request_id=get_request_id())


@router.get("/reports", response_model=ApiResponse[LeaveReports])
async def leave_reports_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    period_year: Annotated[int | None, Query()] = None,
):
    return success_response(await leave_reports(scope, period_year), request_id=get_request_id())


@router.get("/balances/{employee_user_id}", response_model=ApiResponse[list[LeaveBalanceRead]])
async def balances_route(
    employee_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    period_year: Annotated[int | None, Query()] = None,
):
    year = period_year if period_year is not None else date.today().year
    return success_response(await get_employee_balances(scope, employee_user_id, year), request_id=get_request_id())