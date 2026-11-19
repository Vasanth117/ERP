"""Parent communication center routes (not student-scoped)."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.parents.communication_portal_service import (
    acknowledge_notification,
    get_communication_dashboard,
    get_notification_detail,
    get_notification_preferences,
    list_notifications,
    mark_notification_read,
    update_notification_preferences,
)
from app.modules.parents.deps import parent_user
from app.modules.parents.enums import ParentCommunicationInboxCategory, ParentNotificationPriority
from app.modules.parents.phase4_schemas import (
    ParentCommunicationDashboardRead,
    ParentNotificationDetailRead,
    ParentNotificationPreferencesRead,
    ParentNotificationPreferencesUpdate,
    ParentNotificationRead,
)
from app.modules.parents.support_portal_service import list_support_enquiries, submit_support_enquiry
from app.modules.parents.phase4_schemas import ParentSupportEnquiryCreate, ParentSupportEnquiryRead

router = APIRouter()


@router.get("/dashboard", response_model=ApiResponse[ParentCommunicationDashboardRead])
async def parent_communication_dashboard_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentCommunicationDashboardRead]:
    return success_response(await get_communication_dashboard(scope, user), request_id=get_request_id())


@router.get("/notifications", response_model=ApiResponse[Page[ParentNotificationRead]])
async def parent_notifications_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    student_user_id: str | None = None,
    category: ParentCommunicationInboxCategory | None = None,
    unread_only: bool = False,
    priority: ParentNotificationPriority | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
) -> ApiResponse[Page[ParentNotificationRead]]:
    return success_response(
        await list_notifications(
            scope,
            user,
            pagination,
            student_user_id=student_user_id,
            category=category,
            unread_only=unread_only,
            priority=priority,
            from_date=from_date,
            to_date=to_date,
        ),
        request_id=get_request_id(),
    )


@router.get("/notifications/{notification_key:path}", response_model=ApiResponse[ParentNotificationDetailRead])
async def parent_notification_detail_route(
    notification_key: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentNotificationDetailRead]:
    return success_response(await get_notification_detail(scope, user, notification_key), request_id=get_request_id())


@router.post("/notifications/{notification_key:path}/read", response_model=ApiResponse[dict])
async def parent_notification_read_route(
    notification_key: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    return success_response(await mark_notification_read(scope, user, notification_key), request_id=get_request_id())


@router.post("/notifications/{notification_key:path}/acknowledge", response_model=ApiResponse[dict])
async def parent_notification_ack_route(
    notification_key: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    return success_response(await acknowledge_notification(scope, user, notification_key), request_id=get_request_id())


@router.get("/preferences", response_model=ApiResponse[ParentNotificationPreferencesRead])
async def parent_notification_preferences_get_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentNotificationPreferencesRead]:
    return success_response(await get_notification_preferences(scope, user), request_id=get_request_id())


@router.put("/preferences", response_model=ApiResponse[ParentNotificationPreferencesRead])
async def parent_notification_preferences_put_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentNotificationPreferencesUpdate,
) -> ApiResponse[ParentNotificationPreferencesRead]:
    return success_response(await update_notification_preferences(scope, user, payload), request_id=get_request_id())


@router.post("/support/enquiries", response_model=ApiResponse[ParentSupportEnquiryRead])
async def parent_support_enquiry_post_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentSupportEnquiryCreate,
) -> ApiResponse[ParentSupportEnquiryRead]:
    return success_response(await submit_support_enquiry(scope, user, payload), request_id=get_request_id())


@router.get("/support/enquiries", response_model=ApiResponse[list[ParentSupportEnquiryRead]])
async def parent_support_enquiries_list_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentSupportEnquiryRead]]:
    return success_response(await list_support_enquiries(scope, user), request_id=get_request_id())