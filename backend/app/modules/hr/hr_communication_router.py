"""HR notifications and communication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.deps import employee_self_user, hr_staff_user
from app.modules.hr.hr_communication_schemas import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementTransition,
    AudiencePreview,
    HrBroadcastCreate,
    InboxItemRead,
    NotificationDashboard,
    NotificationPreferenceUpsert,
    NotificationTemplateRead,
    NotificationTemplateUpsert,
)
from app.modules.hr.hr_communication_service import (
    acknowledge_notification,
    communication_history,
    create_announcement,
    list_templates,
    mark_notification_read,
    my_inbox,
    notification_dashboard,
    preview_audience,
    send_broadcast,
    transition_announcement,
    upsert_preferences,
    upsert_template,
)

router = APIRouter(prefix="/communications", tags=["hr-communications"])


@router.get("/dashboard", response_model=ApiResponse[NotificationDashboard])
async def notify_dashboard_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await notification_dashboard(scope), request_id=get_request_id())


@router.post("/audience/preview", response_model=ApiResponse[AudiencePreview])
async def audience_preview_route(audience: dict, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await preview_audience(scope, audience), request_id=get_request_id())


@router.post("/templates", response_model=ApiResponse[NotificationTemplateRead])
async def template_upsert_route(payload: NotificationTemplateUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_template(scope, payload), request_id=get_request_id())


@router.get("/templates", response_model=ApiResponse[list[NotificationTemplateRead]])
async def template_list_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_templates(scope), request_id=get_request_id())


@router.post("/announcements", response_model=ApiResponse[AnnouncementRead])
async def announcement_create_route(payload: AnnouncementCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_announcement(scope, payload), request_id=get_request_id())


@router.post("/announcements/{announcement_id}/transition", response_model=ApiResponse[AnnouncementRead])
async def announcement_transition_route(announcement_id: str, payload: AnnouncementTransition, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await transition_announcement(scope, announcement_id, payload), request_id=get_request_id())


@router.post("/broadcast", response_model=ApiResponse)
async def broadcast_route(payload: HrBroadcastCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await send_broadcast(scope, payload), request_id=get_request_id())


@router.get("/history", response_model=ApiResponse)
async def history_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)], limit: int = 100):
    return success_response(await communication_history(scope, limit), request_id=get_request_id())


@router.put("/preferences", response_model=ApiResponse)
async def preferences_route(payload: NotificationPreferenceUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(employee_self_user)]):
    return success_response(await upsert_preferences(scope, payload), request_id=get_request_id())


@router.get("/inbox", response_model=ApiResponse[list[InboxItemRead]])
async def inbox_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(employee_self_user)], unread_only: bool = False):
    return success_response(await my_inbox(scope, unread_only), request_id=get_request_id())


@router.post("/inbox/{notification_id}/read", response_model=ApiResponse)
async def read_route(notification_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(employee_self_user)]):
    return success_response(await mark_notification_read(scope, notification_id), request_id=get_request_id())


@router.post("/inbox/{notification_id}/acknowledge", response_model=ApiResponse)
async def ack_route(notification_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(employee_self_user)]):
    return success_response(await acknowledge_notification(scope, notification_id), request_id=get_request_id())