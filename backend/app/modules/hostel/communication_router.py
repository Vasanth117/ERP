"""Hostel communication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.communication_schemas import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementTransition,
    AudiencePreview,
    AudiencePreviewRequest,
    NotificationDashboard,
    NotificationTemplateRead,
    NotificationTemplateUpsert,
)
from app.modules.hostel.communication_service import (
    create_announcement,
    list_templates,
    notification_dashboard,
    preview_audience,
    run_reminder_scan,
    transition_announcement,
    upsert_template,
)
from app.modules.hostel.deps import hostel_admin_user

router = APIRouter(prefix="/me", tags=["hostel-communication"])


@router.get("/notifications/dashboard", response_model=ApiResponse[NotificationDashboard])
async def notify_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await notification_dashboard(scope), request_id=get_request_id())


@router.post("/notifications/audience/preview", response_model=ApiResponse[AudiencePreview])
async def audience_preview_route(
    payload: AudiencePreviewRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await preview_audience(scope, payload.audience), request_id=get_request_id())


@router.put("/notifications/templates", response_model=ApiResponse[NotificationTemplateRead])
async def template_upsert_route(
    payload: NotificationTemplateUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_template(scope, payload), request_id=get_request_id())


@router.get("/notifications/templates", response_model=ApiResponse[list[NotificationTemplateRead]])
async def template_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await list_templates(scope), request_id=get_request_id())


@router.post("/announcements", response_model=ApiResponse[AnnouncementRead])
async def announcement_create_route(
    payload: AnnouncementCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await create_announcement(scope, payload), request_id=get_request_id())


@router.post("/announcements/{announcement_code}/transition", response_model=ApiResponse[AnnouncementRead])
async def announcement_transition_route(
    announcement_code: str,
    payload: AnnouncementTransition,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await transition_announcement(scope, announcement_code, payload), request_id=get_request_id())


@router.post("/notifications/reminders/scan", response_model=ApiResponse[dict])
async def reminder_scan_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await run_reminder_scan(scope), request_id=get_request_id())