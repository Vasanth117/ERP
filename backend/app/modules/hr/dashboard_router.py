"""HR dashboard routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hr.dashboard_schemas import DashboardEmployeeListItem, HrActivityItem, HrDashboardOverview
from app.modules.hr.dashboard_service import get_hr_dashboard_overview, get_recent_hr_activities, list_dashboard_employees, review_leave_request
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.enums import HrDashboardDateRange, LeaveRequestStatus

router = APIRouter(prefix="/dashboard", tags=["hr-dashboard"])


@router.get("", response_model=ApiResponse[HrDashboardOverview])
async def hr_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(hr_staff_user)],
    department_id: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[HrDashboardDateRange, Query()] = HrDashboardDateRange.WEEK,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
):
    return success_response(
        await get_hr_dashboard_overview(
            scope,
            user,
            department_id=department_id,
            campus_id=campus_id,
            anchor_date=anchor_date,
            date_range=date_range,
            date_from=date_from,
            date_to=date_to,
        ),
        request_id=get_request_id(),
    )


@router.get("/activities", response_model=ApiResponse[list[HrActivityItem]])
async def hr_activities_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    department_id: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[HrDashboardDateRange, Query()] = HrDashboardDateRange.WEEK,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    return success_response(
        await get_recent_hr_activities(
            scope,
            department_id=department_id,
            campus_id=campus_id,
            anchor_date=anchor_date,
            date_range=date_range,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        ),
        request_id=get_request_id(),
    )


@router.get("/employees", response_model=ApiResponse[Page[DashboardEmployeeListItem]])
async def dashboard_employees_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    metric: Annotated[str, Query(description="Employee or attendance metric key")],
    department_id: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
    anchor_date: Annotated[date | None, Query()] = None,
):
    return success_response(
        await list_dashboard_employees(
            scope,
            metric,
            pagination,
            department_id=department_id,
            campus_id=campus_id,
            anchor_date=anchor_date,
        ),
        request_id=get_request_id(),
    )


@router.post("/leave-requests/{leave_request_id}/review", response_model=ApiResponse[dict])
async def dashboard_leave_review_route(
    leave_request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    decision: Annotated[LeaveRequestStatus, Query()],
    note: Annotated[str | None, Query()] = None,
):
    if decision not in {LeaveRequestStatus.APPROVED, LeaveRequestStatus.REJECTED}:
        from app.core.exceptions import AppError

        raise AppError(code="VALIDATION_ERROR", message="Only approve or reject decisions are allowed", status_code=422)
    return success_response(
        await review_leave_request(scope, leave_request_id, decision, note),
        request_id=get_request_id(),
    )