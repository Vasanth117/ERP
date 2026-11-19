"""College admin communication administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.communication_admin_schemas import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementSchedule,
    AudienceGroupUpsert,
    ProviderSettingsUpsert,
    RetryDelivery,
    TemplateUpsert,
)
from app.modules.college_admin.communication_admin_service import (
    communication_report,
    create_announcement,
    list_failed_deliveries,
    publish_announcement,
    retry_delivery,
    schedule_announcement,
    upsert_audience_group,
    upsert_provider_settings,
    upsert_template,
)
from app.modules.college_admin.deps import college_admin_user

router = APIRouter()


@router.post("/announcements", response_model=ApiResponse[AnnouncementRead], status_code=status.HTTP_201_CREATED)
async def announcement_create_route(payload: AnnouncementCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_announcement(scope, payload), request_id=get_request_id())


@router.post("/announcements/{announcement_id}/publish", response_model=ApiResponse[AnnouncementRead])
async def announcement_publish_route(announcement_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await publish_announcement(scope, announcement_id), request_id=get_request_id())


@router.post("/announcements/schedule", response_model=ApiResponse[dict])
async def schedule_route(payload: AnnouncementSchedule, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await schedule_announcement(scope, payload), request_id=get_request_id())


@router.put("/templates", response_model=ApiResponse[dict])
async def template_route(payload: TemplateUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await upsert_template(scope, payload), request_id=get_request_id())


@router.put("/audience-groups", response_model=ApiResponse[dict])
async def audience_route(payload: AudienceGroupUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await upsert_audience_group(scope, payload), request_id=get_request_id())


@router.put("/providers", response_model=ApiResponse[dict])
async def provider_route(payload: ProviderSettingsUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await upsert_provider_settings(scope, payload), request_id=get_request_id())


@router.get("/deliveries/failed", response_model=ApiResponse[Page[dict]])
async def failed_deliveries_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)], pagination: Annotated[Pagination, Depends(pagination_params)]):
    return success_response(await list_failed_deliveries(scope, pagination), request_id=get_request_id())


@router.post("/deliveries/retry", response_model=ApiResponse[dict])
async def retry_route(payload: RetryDelivery, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await retry_delivery(scope, payload), request_id=get_request_id())


@router.get("/reports/summary", response_model=ApiResponse[dict])
async def comm_report_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await communication_report(scope), request_id=get_request_id())