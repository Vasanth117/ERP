"""Department Admin phase 6 — calendar and announcements."""

from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.department_admin.announcement_service import (
    announcement_delivery_status,
    approve_announcement,
    cancel_announcement,
    create_announcement,
    get_announcement,
    list_announcement_acknowledgements,
    list_announcements,
    publish_announcement,
    reject_announcement,
    schedule_announcement,
    submit_announcement,
    update_announcement,
)
from app.modules.department_admin.calendar_service import (
    calendar_conflicts,
    calendar_overview,
    cancel_calendar_event,
    create_calendar_event,
    get_calendar_event,
    list_calendar_events,
    upcoming_calendar_events,
    update_calendar_event,
)
from app.modules.department_admin.deps import department_admin_user
from app.modules.department_admin.models import DepartmentAnnouncementStatus, DepartmentEventStatus
from app.modules.department_admin.phase6_schemas import (
    AnnouncementCreate,
    AnnouncementDecisionBody,
    AnnouncementDeliveryStatusRead,
    AnnouncementRead,
    AnnouncementScheduleBody,
    AnnouncementUpdate,
    AnnouncementAcknowledgementRead,
    CalendarCancelBody,
    CalendarConflictRead,
    CalendarEventCreate,
    CalendarEventRead,
    CalendarEventUpdate,
    CalendarFilters,
    CalendarOverviewRead,
)

phase6_router = APIRouter()


def _calendar_filters(
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    batch_label: Annotated[str | None, Query()] = None,
    section_code: Annotated[str | None, Query()] = None,
    audience_scope: Annotated[str | None, Query()] = None,
    date_from: Annotated[datetime | None, Query()] = None,
    date_to: Annotated[datetime | None, Query()] = None,
    status: Annotated[DepartmentEventStatus | None, Query()] = None,
) -> CalendarFilters:
    return CalendarFilters(
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        category=category,
        programme_code=programme_code,
        batch_label=batch_label,
        section_code=section_code,
        audience_scope=audience_scope,
        date_from=date_from,
        date_to=date_to,
        status=status,
    )


@phase6_router.get("/calendar", response_model=ApiResponse[CalendarOverviewRead])
async def department_calendar_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[CalendarFilters, Depends(_calendar_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[CalendarOverviewRead]:
    data = await calendar_overview(scope, user, filters=filters, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase6_router.get("/calendar/events", response_model=ApiResponse[Page[CalendarEventRead]])
async def department_calendar_events_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[CalendarFilters, Depends(_calendar_filters)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[CalendarEventRead]]:
    data = await list_calendar_events(scope, user, filters=filters, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase6_router.post("/calendar/events", response_model=ApiResponse[CalendarEventRead])
async def department_calendar_event_create_route(
    payload: CalendarEventCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[CalendarEventRead]:
    data = await create_calendar_event(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase6_router.get("/calendar/events/{event_id}", response_model=ApiResponse[CalendarEventRead])
async def department_calendar_event_get_route(
    event_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[CalendarEventRead]:
    data = await get_calendar_event(scope, user, event_id)
    return success_response(data, request_id=get_request_id())


@phase6_router.patch("/calendar/events/{event_id}", response_model=ApiResponse[CalendarEventRead])
async def department_calendar_event_update_route(
    event_id: str,
    payload: CalendarEventUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[CalendarEventRead]:
    data = await update_calendar_event(scope, user, event_id, payload)
    return success_response(data, request_id=get_request_id())


@phase6_router.post("/calendar/events/{event_id}/cancel", response_model=ApiResponse[CalendarEventRead])
async def department_calendar_event_cancel_route(
    event_id: str,
    payload: CalendarCancelBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[CalendarEventRead]:
    data = await cancel_calendar_event(scope, user, event_id, payload)
    return success_response(data, request_id=get_request_id())


@phase6_router.get("/calendar/upcoming", response_model=ApiResponse[Page[CalendarEventRead]])
async def department_calendar_upcoming_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    days: Annotated[int, Query(ge=1, le=90)] = 14,
) -> ApiResponse[Page[CalendarEventRead]]:
    data = await upcoming_calendar_events(scope, user, days=days, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase6_router.get("/calendar/conflicts", response_model=ApiResponse[CalendarConflictRead])
async def department_calendar_conflicts_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    event_id: Annotated[str | None, Query()] = None,
    starts_at: Annotated[datetime | None, Query()] = None,
    ends_at: Annotated[datetime | None, Query()] = None,
    room: Annotated[str | None, Query()] = None,
    laboratory: Annotated[str | None, Query()] = None,
    organizer_user_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[CalendarConflictRead]:
    data = await calendar_conflicts(
        scope,
        user,
        event_id=event_id,
        starts_at=starts_at,
        ends_at=ends_at,
        room=room,
        laboratory=laboratory,
        organizer_user_id=organizer_user_id,
    )
    return success_response(data, request_id=get_request_id())


@phase6_router.get("/announcements", response_model=ApiResponse[Page[AnnouncementRead]])
async def department_announcements_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[DepartmentAnnouncementStatus | None, Query()] = None,
) -> ApiResponse[Page[AnnouncementRead]]:
    data = await list_announcements(scope, user, status=status, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase6_router.post("/announcements", response_model=ApiResponse[AnnouncementRead])
async def department_announcement_create_route(
    payload: AnnouncementCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AnnouncementRead]:
    data = await create_announcement(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase6_router.get("/announcements/{announcement_id}", response_model=ApiResponse[AnnouncementRead])
async def department_announcement_get_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AnnouncementRead]:
    data = await get_announcement(scope, user, announcement_id)
    return success_response(data, request_id=get_request_id())


@phase6_router.patch("/announcements/{announcement_id}", response_model=ApiResponse[AnnouncementRead])
async def department_announcement_update_route(
    announcement_id: str,
    payload: AnnouncementUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AnnouncementRead]:
    data = await update_announcement(scope, user, announcement_id, payload)
    return success_response(data, request_id=get_request_id())


@phase6_router.post("/announcements/{announcement_id}/submit", response_model=ApiResponse[AnnouncementRead])
async def department_announcement_submit_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AnnouncementRead]:
    data = await submit_announcement(scope, user, announcement_id)
    return success_response(data, request_id=get_request_id())


@phase6_router.post("/announcements/{announcement_id}/approve", response_model=ApiResponse[AnnouncementRead])
async def department_announcement_approve_route(
    announcement_id: str,
    payload: AnnouncementDecisionBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AnnouncementRead]:
    data = await approve_announcement(scope, user, announcement_id, payload)
    return success_response(data, request_id=get_request_id())


@phase6_router.post("/announcements/{announcement_id}/reject", response_model=ApiResponse[AnnouncementRead])
async def department_announcement_reject_route(
    announcement_id: str,
    payload: AnnouncementDecisionBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AnnouncementRead]:
    data = await reject_announcement(scope, user, announcement_id, payload)
    return success_response(data, request_id=get_request_id())


@phase6_router.post("/announcements/{announcement_id}/publish", response_model=ApiResponse[AnnouncementRead])
async def department_announcement_publish_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AnnouncementRead]:
    data = await publish_announcement(scope, user, announcement_id)
    return success_response(data, request_id=get_request_id())


@phase6_router.post("/announcements/{announcement_id}/schedule", response_model=ApiResponse[AnnouncementRead])
async def department_announcement_schedule_route(
    announcement_id: str,
    payload: AnnouncementScheduleBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AnnouncementRead]:
    data = await schedule_announcement(scope, user, announcement_id, payload)
    return success_response(data, request_id=get_request_id())


@phase6_router.post("/announcements/{announcement_id}/cancel", response_model=ApiResponse[AnnouncementRead])
async def department_announcement_cancel_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AnnouncementRead]:
    data = await cancel_announcement(scope, user, announcement_id)
    return success_response(data, request_id=get_request_id())


@phase6_router.get(
    "/announcements/{announcement_id}/delivery-status",
    response_model=ApiResponse[AnnouncementDeliveryStatusRead],
)
async def department_announcement_delivery_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AnnouncementDeliveryStatusRead]:
    data = await announcement_delivery_status(scope, user, announcement_id)
    return success_response(data, request_id=get_request_id())


@phase6_router.get(
    "/announcements/{announcement_id}/acknowledgements",
    response_model=ApiResponse[Page[AnnouncementAcknowledgementRead]],
)
async def department_announcement_acks_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AnnouncementAcknowledgementRead]]:
    data = await list_announcement_acknowledgements(scope, user, announcement_id, pagination=pagination)
    return success_response(data, request_id=get_request_id())