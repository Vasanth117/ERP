"""Hostel maintenance and complaints routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.maintenance_models import HostelComplaintPriority, HostelComplaintStatus
from app.modules.hostel.maintenance_schemas import (
    ComplaintAssign,
    ComplaintFeedbackInput,
    ComplaintRead,
    ComplaintStatusUpdate,
    ComplaintSubmit,
    FacilityUnavailabilityInput,
    MaintenanceDashboard,
    MaintenanceScheduleUpsert,
)
from app.modules.hostel.maintenance_service import (
    assign_complaint,
    list_complaints,
    maintenance_dashboard,
    set_facility_unavailability,
    submit_complaint,
    update_complaint_status,
    upsert_maintenance_schedule,
)

router = APIRouter(prefix="/me", tags=["hostel-maintenance"])


@router.get("/maintenance/dashboard", response_model=ApiResponse[MaintenanceDashboard])
async def maintenance_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await maintenance_dashboard(scope), request_id=get_request_id())


@router.post("/complaints", response_model=ApiResponse[ComplaintRead], status_code=status.HTTP_201_CREATED)
async def complaint_submit_admin_route(
    payload: ComplaintSubmit,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await submit_complaint(scope, payload), request_id=get_request_id())


@router.get("/complaints", response_model=ApiResponse[Page[ComplaintRead]])
async def complaint_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[HostelComplaintStatus | None, Query()] = None,
    priority: Annotated[HostelComplaintPriority | None, Query()] = None,
    hostel_code: Annotated[str | None, Query()] = None,
):
    return success_response(
        await list_complaints(scope, pagination, status=status, priority=priority, hostel_code=hostel_code),
        request_id=get_request_id(),
    )


@router.post("/complaints/assign", response_model=ApiResponse[ComplaintRead])
async def complaint_assign_route(
    payload: ComplaintAssign,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await assign_complaint(scope, payload), request_id=get_request_id())


@router.post("/complaints/status", response_model=ApiResponse[ComplaintRead])
async def complaint_status_route(
    payload: ComplaintStatusUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await update_complaint_status(scope, payload), request_id=get_request_id())


@router.put("/maintenance/schedules", response_model=ApiResponse[dict])
async def maintenance_schedule_route(
    payload: MaintenanceScheduleUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_maintenance_schedule(scope, payload), request_id=get_request_id())


@router.post("/maintenance/facility-availability", response_model=ApiResponse[dict])
async def facility_unavailability_route(
    payload: FacilityUnavailabilityInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await set_facility_unavailability(scope, payload), request_id=get_request_id())