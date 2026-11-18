"""Library notification routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.deps import librarian_user
from app.modules.library.notification_schemas import (
    LibraryAnnouncementCreate,
    LibraryAnnouncementRead,
    LibraryNotificationPreferenceRead,
    LibraryNotificationPreferenceUpdate,
    LibraryNotificationRead,
    ManualNotificationRequest,
    NotificationDeliveryRead,
)
from app.modules.library.notification_service import (
    create_library_announcement,
    get_preferences,
    notification_deliveries,
    publish_library_announcement,
    retry_notification_delivery,
    run_notification_batch,
    search_notifications,
    send_manual_notification,
    update_preferences,
)

router = APIRouter(prefix="/notifications", tags=["library-notifications"])


@router.get("", response_model=ApiResponse[Page[LibraryNotificationRead]])
async def search_notifications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    recipient_user_id: Annotated[str | None, Query()] = None,
    branch_code: Annotated[str | None, Query()] = None,
    event_type: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[LibraryNotificationRead]]:
    return success_response(
        await search_notifications(scope, pagination, recipient_user_id=recipient_user_id, branch_code=branch_code, event_type=event_type),
        request_id=get_request_id(),
    )


@router.get("/preferences/{user_id}", response_model=ApiResponse[LibraryNotificationPreferenceRead])
async def get_prefs_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryNotificationPreferenceRead]:
    return success_response(await get_preferences(scope, user_id), request_id=get_request_id())


@router.patch("/preferences/{user_id}", response_model=ApiResponse[LibraryNotificationPreferenceRead])
async def update_prefs_route(
    user_id: str,
    payload: LibraryNotificationPreferenceUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryNotificationPreferenceRead]:
    return success_response(await update_preferences(scope, user_id, payload), request_id=get_request_id())


@router.post("/send", response_model=ApiResponse[LibraryNotificationRead], status_code=status.HTTP_201_CREATED)
async def manual_send_route(
    payload: ManualNotificationRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryNotificationRead]:
    return success_response(await send_manual_notification(scope, payload), request_id=get_request_id())


@router.post("/announcements", response_model=ApiResponse[LibraryAnnouncementRead], status_code=status.HTTP_201_CREATED)
async def announcement_create_route(
    payload: LibraryAnnouncementCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryAnnouncementRead]:
    return success_response(await create_library_announcement(scope, payload), request_id=get_request_id())


@router.post("/announcements/{announcement_id}/publish", response_model=ApiResponse[dict])
async def announcement_publish_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[dict]:
    return success_response(await publish_library_announcement(scope, announcement_id), request_id=get_request_id())


@router.post("/batch/run", response_model=ApiResponse[dict])
async def batch_run_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await run_notification_batch(scope, branch_code=branch_code), request_id=get_request_id())


@router.get("/{notification_id}/deliveries", response_model=ApiResponse[list[NotificationDeliveryRead]])
async def deliveries_route(
    notification_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[list[NotificationDeliveryRead]]:
    return success_response(await notification_deliveries(scope, notification_id), request_id=get_request_id())


@router.post("/deliveries/{delivery_id}/retry", response_model=ApiResponse[NotificationDeliveryRead])
async def retry_delivery_route(
    delivery_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[NotificationDeliveryRead]:
    return success_response(await retry_notification_delivery(scope, delivery_id), request_id=get_request_id())