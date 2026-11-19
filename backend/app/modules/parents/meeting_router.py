"""Parent meeting routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.parents.deps import parent_enquiry_rate_limit, parent_user
from app.modules.parents.meeting_portal_service import (
    cancel_meeting_request,
    create_meeting_request,
    get_meeting_availability,
    get_meeting_dashboard,
    get_meeting_outcome,
    list_appointments,
    list_meeting_categories,
    list_meeting_requests,
    list_representatives,
    request_reschedule,
)
from app.modules.parents.phase5_schemas import (
    ParentMeetingAppointmentRead,
    ParentMeetingCancelCreate,
    ParentMeetingCategoryRead,
    ParentMeetingDashboardRead,
    ParentMeetingOutcomeRead,
    ParentMeetingRepresentativeRead,
    ParentMeetingRequestCreate,
    ParentMeetingRequestRead,
    ParentMeetingRescheduleCreate,
    ParentMeetingSlotRead,
)

router = APIRouter()


@router.get("/categories", response_model=ApiResponse[list[ParentMeetingCategoryRead]])
async def parent_meeting_categories_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentMeetingCategoryRead]]:
    return success_response(await list_meeting_categories(scope, user), request_id=get_request_id())


@router.get("/representatives", response_model=ApiResponse[list[ParentMeetingRepresentativeRead]])
async def parent_meeting_representatives_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    department_id: str | None = None,
) -> ApiResponse[list[ParentMeetingRepresentativeRead]]:
    return success_response(
        await list_representatives(scope, user, department_id=department_id),
        request_id=get_request_id(),
    )


@router.get("/availability", response_model=ApiResponse[list[ParentMeetingSlotRead]])
async def parent_meeting_availability_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    on_date: date,
    staff_user_id: str | None = None,
) -> ApiResponse[list[ParentMeetingSlotRead]]:
    return success_response(
        await get_meeting_availability(scope, user, on_date=on_date, staff_user_id=staff_user_id),
        request_id=get_request_id(),
    )


@router.get("/dashboard", response_model=ApiResponse[ParentMeetingDashboardRead])
async def parent_meeting_dashboard_global_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    student_user_id: str | None = None,
) -> ApiResponse[ParentMeetingDashboardRead]:
    return success_response(
        await get_meeting_dashboard(scope, user, student_user_id=student_user_id),
        request_id=get_request_id(),
    )