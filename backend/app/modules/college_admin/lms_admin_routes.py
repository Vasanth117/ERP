"""LMS administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.lms_admin_schemas import (
    LmsConfigurationHistoryItem,
    LmsContentCategoryRead,
    LmsContentCategoryUpsert,
    LmsCourseMappingRead,
    LmsCourseMappingUpsert,
    LmsMonitorSummary,
    LmsOperationalStats,
    LmsPublishingPolicyRead,
    LmsPublishingPolicyUpsert,
    LmsSettingsRead,
    LmsSettingsUpdate,
)
from app.modules.college_admin.lms_admin_service import (
    get_lms_integration_status,
    get_lms_monitor_summary,
    get_lms_operational_stats,
    get_lms_settings,
    list_content_categories,
    list_course_mappings,
    list_lms_configuration_history,
    update_lms_settings,
    upsert_content_category,
    upsert_course_mapping,
    upsert_publishing_policy,
)

router = APIRouter()


@router.get("/settings", response_model=ApiResponse[LmsSettingsRead])
async def lms_settings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsSettingsRead]:
    return success_response(await get_lms_settings(scope), request_id=get_request_id())


@router.patch("/settings", response_model=ApiResponse[LmsSettingsRead])
async def lms_settings_update_route(
    payload: LmsSettingsUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsSettingsRead]:
    return success_response(await update_lms_settings(scope, user, payload), request_id=get_request_id())


@router.get("/course-mappings", response_model=ApiResponse[list[LmsCourseMappingRead]])
async def lms_course_mappings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[LmsCourseMappingRead]]:
    return success_response(await list_course_mappings(scope), request_id=get_request_id())


@router.put("/course-mappings", response_model=ApiResponse[LmsCourseMappingRead])
async def lms_course_mapping_upsert_route(
    payload: LmsCourseMappingUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsCourseMappingRead]:
    return success_response(await upsert_course_mapping(scope, user, payload), request_id=get_request_id())


@router.get("/content-categories", response_model=ApiResponse[list[LmsContentCategoryRead]])
async def lms_categories_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[LmsContentCategoryRead]]:
    return success_response(await list_content_categories(scope), request_id=get_request_id())


@router.put("/content-categories", response_model=ApiResponse[LmsContentCategoryRead])
async def lms_category_upsert_route(
    payload: LmsContentCategoryUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsContentCategoryRead]:
    return success_response(await upsert_content_category(scope, payload), request_id=get_request_id())


@router.put("/publishing-policies", response_model=ApiResponse[LmsPublishingPolicyRead])
async def lms_publishing_policy_route(
    payload: LmsPublishingPolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsPublishingPolicyRead]:
    return success_response(await upsert_publishing_policy(scope, user, payload), request_id=get_request_id())


@router.get("/statistics", response_model=ApiResponse[LmsOperationalStats])
async def lms_statistics_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsOperationalStats]:
    return success_response(await get_lms_operational_stats(scope), request_id=get_request_id())


@router.get("/monitoring", response_model=ApiResponse[LmsMonitorSummary])
async def lms_monitor_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LmsMonitorSummary]:
    return success_response(await get_lms_monitor_summary(scope), request_id=get_request_id())


@router.get("/configuration-history", response_model=ApiResponse[list[LmsConfigurationHistoryItem]])
async def lms_config_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[LmsConfigurationHistoryItem]]:
    return success_response(await list_lms_configuration_history(scope), request_id=get_request_id())


@router.get("/integrations", response_model=ApiResponse[dict])
async def lms_integrations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await get_lms_integration_status(scope), request_id=get_request_id())