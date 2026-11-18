"""Department Admin dashboard and profile routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.department_admin.dashboard_service import (
    get_academic_dashboard_summary,
    get_attendance_dashboard_summary,
    get_department_activities,
    get_department_alerts,
    get_department_dashboard_bundle,
    get_department_overview,
    get_examination_dashboard_summary,
    get_faculty_dashboard_stats,
    get_student_dashboard_stats,
    get_timetable_dashboard_summary,
)
from app.modules.department_admin.deps import department_admin_user, profile_update_rate_limit
from app.modules.department_admin.profile_service import (
    create_profile_change_request,
    get_academic_config_visibility,
    get_department_profile,
    get_department_setting,
    get_profile_change_request,
    list_department_settings,
    list_profile_change_requests,
    update_department_profile,
    upsert_department_setting,
)
from app.modules.department_admin.phase2_router import phase2_router
from app.modules.department_admin.phase3_router import phase3_router
from app.modules.department_admin.phase4_router import phase4_router
from app.modules.department_admin.phase5_router import phase5_router
from app.modules.department_admin.phase6_router import phase6_router
from app.modules.department_admin.phase7_router import phase7_router
from app.modules.department_admin.phase8_router import phase8_router
from app.modules.department_admin.phase9_router import phase9_router
from app.modules.department_admin.phase10_router import phase10_router
from app.modules.department_admin.schemas import (
    DepartmentAcademicConfigVisibilityRead,
    DepartmentAcademicSummaryRead,
    DepartmentActivityRead,
    DepartmentAlertRead,
    DepartmentAttendanceOverviewRead,
    DepartmentDashboardBundleRead,
    DepartmentDashboardFilters,
    DepartmentExaminationOverviewRead,
    DepartmentFacultyStatsRead,
    DepartmentOverviewRead,
    DepartmentProfileChangeRequestCreate,
    DepartmentProfileChangeRequestRead,
    DepartmentProfileDetailsRead,
    DepartmentProfileDetailsUpdate,
    DepartmentSettingRead,
    DepartmentSettingUpdate,
    DepartmentStudentStatsRead,
    DepartmentTimetableOverviewRead,
)

router = APIRouter()
router.include_router(phase2_router)
router.include_router(phase3_router)
router.include_router(phase4_router)
router.include_router(phase5_router)
router.include_router(phase6_router)
router.include_router(phase7_router)
router.include_router(phase8_router)
router.include_router(phase9_router)
router.include_router(phase10_router)


def _filters_query(
    anchor_date: date | None = Query(default=None),
    date_range: DashboardDateRange = Query(default=DashboardDateRange.WEEK, alias="range"),
    academic_year_label: str | None = Query(default=None),
    semester_label: str | None = Query(default=None),
    programme_code: str | None = Query(default=None),
    batch_label: str | None = Query(default=None),
    section_code: str | None = Query(default=None),
) -> DepartmentDashboardFilters:
    return DepartmentDashboardFilters(
        anchor_date=anchor_date,
        date_range=date_range,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        programme_code=programme_code,
        batch_label=batch_label,
        section_code=section_code,
    )


@router.get("/dashboard", response_model=ApiResponse[DepartmentDashboardBundleRead])
async def department_dashboard_bundle_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[DepartmentDashboardFilters, Depends(_filters_query)],
) -> ApiResponse[DepartmentDashboardBundleRead]:
    data = await get_department_dashboard_bundle(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/overview", response_model=ApiResponse[DepartmentOverviewRead])
async def department_dashboard_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[DepartmentDashboardFilters, Depends(_filters_query)],
) -> ApiResponse[DepartmentOverviewRead]:
    data = await get_department_overview(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/students", response_model=ApiResponse[DepartmentStudentStatsRead])
async def department_dashboard_students_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[DepartmentDashboardFilters, Depends(_filters_query)],
) -> ApiResponse[DepartmentStudentStatsRead]:
    data = await get_student_dashboard_stats(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/faculty", response_model=ApiResponse[DepartmentFacultyStatsRead])
async def department_dashboard_faculty_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DepartmentFacultyStatsRead]:
    data = await get_faculty_dashboard_stats(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/academics", response_model=ApiResponse[DepartmentAcademicSummaryRead])
async def department_dashboard_academics_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[DepartmentDashboardFilters, Depends(_filters_query)],
) -> ApiResponse[DepartmentAcademicSummaryRead]:
    data = await get_academic_dashboard_summary(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/attendance", response_model=ApiResponse[DepartmentAttendanceOverviewRead])
async def department_dashboard_attendance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DepartmentAttendanceOverviewRead]:
    data = await get_attendance_dashboard_summary(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/timetable", response_model=ApiResponse[DepartmentTimetableOverviewRead])
async def department_dashboard_timetable_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    anchor_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[DepartmentTimetableOverviewRead]:
    data = await get_timetable_dashboard_summary(scope, user, anchor_date=anchor_date)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/examinations", response_model=ApiResponse[DepartmentExaminationOverviewRead])
async def department_dashboard_examinations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[DepartmentDashboardFilters, Depends(_filters_query)],
) -> ApiResponse[DepartmentExaminationOverviewRead]:
    data = await get_examination_dashboard_summary(scope, user, filters=filters)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/alerts", response_model=ApiResponse[Page[DepartmentAlertRead]])
async def department_dashboard_alerts_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[DepartmentAlertRead]]:
    data = await get_department_alerts(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/activities", response_model=ApiResponse[Page[DepartmentActivityRead]])
async def department_dashboard_activities_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[DepartmentActivityRead]]:
    data = await get_department_activities(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/profile", response_model=ApiResponse[DepartmentProfileDetailsRead])
async def department_profile_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DepartmentProfileDetailsRead]:
    data = await get_department_profile(scope, user)
    return success_response(data, request_id=get_request_id())


@router.patch("/profile", response_model=ApiResponse[DepartmentProfileDetailsRead])
async def department_profile_update_route(
    payload: DepartmentProfileDetailsUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    _: Annotated[None, Depends(profile_update_rate_limit)],
) -> ApiResponse[DepartmentProfileDetailsRead]:
    data = await update_department_profile(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/settings", response_model=ApiResponse[list[DepartmentSettingRead]])
async def department_settings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[DepartmentSettingRead]]:
    data = await list_department_settings(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/settings/{setting_key}", response_model=ApiResponse[DepartmentSettingRead])
async def department_setting_get_route(
    setting_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DepartmentSettingRead]:
    data = await get_department_setting(scope, user, setting_key)
    return success_response(data, request_id=get_request_id())


@router.patch("/settings/{setting_key}", response_model=ApiResponse[DepartmentSettingRead])
async def department_setting_update_route(
    setting_key: str,
    payload: DepartmentSettingUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DepartmentSettingRead]:
    data = await upsert_department_setting(scope, user, setting_key, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/profile/change-requests", response_model=ApiResponse[Page[DepartmentProfileChangeRequestRead]])
async def department_change_requests_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[DepartmentProfileChangeRequestRead]]:
    data = await list_profile_change_requests(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@router.post("/profile/change-requests", response_model=ApiResponse[DepartmentProfileChangeRequestRead])
async def department_change_request_create_route(
    payload: DepartmentProfileChangeRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DepartmentProfileChangeRequestRead]:
    data = await create_profile_change_request(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/profile/change-requests/{request_id}", response_model=ApiResponse[DepartmentProfileChangeRequestRead])
async def department_change_request_get_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DepartmentProfileChangeRequestRead]:
    data = await get_profile_change_request(scope, user, request_id)
    return success_response(data, request_id=get_request_id())


@router.get("/academic-config/visibility", response_model=ApiResponse[DepartmentAcademicConfigVisibilityRead])
async def department_academic_config_visibility_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DepartmentAcademicConfigVisibilityRead]:
    data = await get_academic_config_visibility(scope, user)
    return success_response(data, request_id=get_request_id())