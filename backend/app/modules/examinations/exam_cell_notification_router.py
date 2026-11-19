"""Examination notification routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, get_current_user, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_notification_schemas import (
    ExamAnnouncementCreate,
    ExamAnnouncementRead,
    ExamManualNotificationRequest,
    ExamNotificationDeliveryRead,
    ExamNotificationEventRead,
    ExamNotificationPreferenceRead,
    ExamNotificationPreferenceUpdate,
    ExamNotificationTemplateRead,
    ExamNotificationTemplateUpsert,
)
from app.modules.examinations.exam_cell_notification_service import (
    create_announcement,
    get_preferences,
    list_deliveries_for_event,
    list_notification_history,
    publish_announcement,
    run_notification_batch,
    send_manual_notification,
    update_preferences,
    upsert_template,
)

router = APIRouter(tags=["examination-cell-notifications"])


@router.put("/notifications/templates", response_model=ApiResponse[ExamNotificationTemplateRead])
async def upsert_template_route(
    payload: ExamNotificationTemplateUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamNotificationTemplateRead]:
    return success_response(await upsert_template(scope, user, payload), request_id=get_request_id())


@router.post("/notifications/send", response_model=ApiResponse[ExamNotificationEventRead])
async def send_notification_route(
    payload: ExamManualNotificationRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamNotificationEventRead]:
    return success_response(await send_manual_notification(scope, user, payload), request_id=get_request_id())


@router.get("/notifications/history", response_model=ApiResponse[Page[ExamNotificationEventRead]])
async def notification_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(get_current_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    recipient_user_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[ExamNotificationEventRead]]:
    _ = user
    return success_response(
        await list_notification_history(scope, pagination, recipient_user_id=recipient_user_id),
        request_id=get_request_id(),
    )


@router.get("/notifications/events/{event_record_id}/deliveries", response_model=ApiResponse[list[ExamNotificationDeliveryRead]])
async def notification_deliveries_route(
    event_record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamNotificationDeliveryRead]]:
    _ = user
    return success_response(await list_deliveries_for_event(scope, event_record_id), request_id=get_request_id())


@router.get("/notifications/preferences/me", response_model=ApiResponse[ExamNotificationPreferenceRead])
async def get_preferences_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ExamNotificationPreferenceRead]:
    return success_response(await get_preferences(scope, user), request_id=get_request_id())


@router.patch("/notifications/preferences/me", response_model=ApiResponse[ExamNotificationPreferenceRead])
async def update_preferences_route(
    payload: ExamNotificationPreferenceUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(get_current_user)],
) -> ApiResponse[ExamNotificationPreferenceRead]:
    return success_response(await update_preferences(scope, user, payload), request_id=get_request_id())


@router.post("/notifications/announcements", response_model=ApiResponse[ExamAnnouncementRead])
async def create_announcement_route(
    payload: ExamAnnouncementCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamAnnouncementRead]:
    return success_response(await create_announcement(scope, user, payload), request_id=get_request_id())


@router.post("/notifications/announcements/{announcement_id}/publish", response_model=ApiResponse[ExamAnnouncementRead])
async def publish_announcement_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamAnnouncementRead]:
    return success_response(await publish_announcement(scope, user, announcement_id), request_id=get_request_id())


@router.post("/notifications/deliveries/process", response_model=ApiResponse[dict[str, int]])
async def process_deliveries_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[dict[str, int]]:
    _ = user
    return success_response(await run_notification_batch(scope), request_id=get_request_id())