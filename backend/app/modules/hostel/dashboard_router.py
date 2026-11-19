"""Hostel Admin dashboard routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.dashboard_schemas import HostelDashboardOverview, HostelDrillDownRecord
from app.modules.hostel.dashboard_service import get_dashboard_drill_down, get_hostel_dashboard_overview
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.hostel_portal_enums import HostelDashboardDateRange, HostelDashboardDrillMetric

router = APIRouter(prefix="/me", tags=["hostel-dashboard"])


@router.get("/dashboard", response_model=ApiResponse[HostelDashboardOverview])
async def hostel_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(hostel_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    hostel_code: Annotated[str | None, Query()] = None,
    building_code: Annotated[str | None, Query()] = None,
    block_code: Annotated[str | None, Query()] = None,
    floor_id: Annotated[str | None, Query()] = None,
    room_type: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
    resident_status: Annotated[str | None, Query()] = None,
    allocation_status: Annotated[str | None, Query()] = None,
    mess_status: Annotated[str | None, Query()] = None,
    maintenance_status: Annotated[str | None, Query()] = None,
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[HostelDashboardDateRange, Query(alias="range")] = HostelDashboardDateRange.WEEK,
):
    data = await get_hostel_dashboard_overview(
        scope,
        user,
        academic_year_label=academic_year_label,
        hostel_code=hostel_code,
        building_code=building_code,
        block_code=block_code,
        floor_id=floor_id,
        room_type=room_type,
        department_id=department_id,
        resident_status=resident_status,
        allocation_status=allocation_status,
        mess_status=mess_status,
        maintenance_status=maintenance_status,
        anchor_date=anchor_date,
        date_range=date_range,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/drill-down/{metric}", response_model=ApiResponse[Page[HostelDrillDownRecord]])
async def hostel_dashboard_drill_down_route(
    metric: HostelDashboardDrillMetric,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    academic_year_label: Annotated[str | None, Query()] = None,
    hostel_code: Annotated[str | None, Query()] = None,
    building_code: Annotated[str | None, Query()] = None,
    block_code: Annotated[str | None, Query()] = None,
    floor_id: Annotated[str | None, Query()] = None,
    room_type: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[HostelDashboardDateRange, Query(alias="range")] = HostelDashboardDateRange.WEEK,
):
    data = await get_dashboard_drill_down(
        scope,
        metric,
        pagination,
        academic_year_label=academic_year_label,
        hostel_code=hostel_code,
        building_code=building_code,
        block_code=block_code,
        floor_id=floor_id,
        room_type=room_type,
        department_id=department_id,
        anchor_date=anchor_date,
        date_range=date_range,
    )
    return success_response(data, request_id=get_request_id())