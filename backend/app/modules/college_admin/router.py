"""College Admin dashboard and institution routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.dashboard_service import (
    get_dashboard_overview,
    get_institutional_statistics,
    get_operational_summaries,
    get_pending_approvals,
    get_recent_activities,
)
from app.modules.college_admin.deps import college_admin_user, institution_settings_rate_limit
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.institution_overview_service import get_institutional_overview
from app.modules.college_admin.institution_information_page_service import (
    get_institution_information_page,
    publish_institution_information,
    save_institution_profile_draft,
)
from app.modules.college_admin.institution_branding_page_service import (
    get_institution_branding_page,
    publish_institution_branding,
    save_institution_branding_draft,
    upload_branding_asset,
)
from app.modules.college_admin.institution_academic_year_page_service import (
    copy_academic_year_from_previous,
    create_blank_academic_year,
    get_academic_year_configuration_page,
    save_academic_year_configuration,
)
from app.modules.college_admin.institution_policies_page_service import get_institution_policies_page
from app.modules.college_admin.institution_calendar_page_service import (
    get_institution_calendar_settings_page,
    import_institution_holidays_from_previous,
    save_institution_calendar_settings_page,
)
from app.modules.college_admin.institution_configuration_history_page_service import (
    get_institution_configuration_history_page,
)
from app.modules.college_admin.institution_academic_settings_page_service import (
    get_academic_institution_settings_page,
    reset_academic_institution_settings_page,
    save_academic_institution_settings_page,
)
from app.modules.college_admin.campus_contact_page_service import get_campus_contact_page, save_campus_contact_page
from app.modules.college_admin.campus_detail_page_service import get_campus_detail_page
from app.modules.college_admin.campus_management_dashboard_service import get_campus_management_dashboard
from app.modules.college_admin.institution_profile_page_service import get_institution_profile_page
from app.modules.college_admin.academic_performance_overview_service import get_academic_performance_overview
from app.modules.college_admin.attendance_overview_service import get_attendance_overview
from app.modules.college_admin.examination_overview_service import get_examination_overview
from app.modules.college_admin.finance_overview_service import get_finance_overview
from app.modules.college_admin.pending_approvals_overview_service import get_pending_approvals_overview
from app.modules.college_admin.recent_activities_overview_service import get_recent_activities_overview
from app.modules.college_admin.alerts_overview_service import get_alerts_overview, mark_dashboard_alerts_read
from app.modules.college_admin.all_departments_list_page_service import get_all_departments_list_page
from app.modules.college_admin.create_edit_department_page_service import (
    get_create_edit_department_page_by_id,
    save_create_edit_department,
)
from app.modules.college_admin.department_details_page_service import get_department_details_page_by_id
from app.modules.college_admin.department_head_assignment_page_service import (
    get_department_head_assignment_page,
    save_department_head_assignment,
)
from app.modules.college_admin.organizational_hierarchy_page_service import get_organizational_hierarchy_page
from app.modules.college_admin.programme_course_mapping_page_service import get_programme_course_mapping_page
from app.modules.college_admin.department_faculty_allocation_page_service import (
    get_department_faculty_allocation_page,
    save_department_faculty_allocation,
)
from app.modules.college_admin.department_status_history_page_service import get_department_status_history_page
from app.modules.college_admin.department_resource_management_page_service import (
    get_department_resource_management_page,
)
from app.modules.college_admin.department_management_dashboard_page_service import (
    get_department_management_dashboard_page,
)
from app.modules.college_admin.department_performance_overview_service import get_department_performance_overview
from app.modules.college_admin.faculty_statistics_overview_service import get_faculty_statistics_overview
from app.modules.college_admin.student_statistics_overview_service import get_student_statistics_overview
from app.modules.college_admin.institution_service import (
    create_campus,
    get_campus,
    get_configuration_history,
    get_institution_profile,
    get_institution_settings,
    list_campuses,
    update_campus,
    update_institution_profile,
    update_institution_settings,
)
from app.modules.college_admin.schemas import (
    ActivitySummary,
    CampusContactPageRead,
    CampusContactPageSave,
    CampusCreate,
    CampusDetailPageRead,
    CampusManagementDashboardRead,
    CampusRead,
    CampusUpdate,
    CollegeDashboardOverview,
    CollegeDashboardStatsRead,
    InstitutionConfigurationHistoryItem,
    InstitutionPoliciesPageRead,
    InstitutionalOverviewRead,
    AcademicInstitutionSettingsPageRead,
    AcademicInstitutionSettingsSave,
    AcademicYearConfigurationPageRead,
    AcademicYearConfigurationSave,
    InstitutionCalendarSettingsPageRead,
    InstitutionCalendarSettingsSave,
    ConfigurationHistoryPageRead,
    UserDashboardPageRead,
    UserAllUsersListPageRead,
    UserDetailsPageRead,
    CreateNewUserPageRead,
    CreateNewUserDraftUpdate,
    CreateNewUserValidatePayload,
    CreateNewUserValidateResponse,
    CreateNewUserSubmitPayload,
    CreateNewUserSubmitResponse,
    EditUserInformationPageRead,
    EditUserInformationSavePayload,
    BulkUserInvitationPageRead,
    BulkUserInvitationUploadPayload,
    BulkUserInvitationStepPayload,
    BulkUserInvitationSendResponse,
    RoleManagementDashboardPageRead,
    CreateEditRolePageRead,
    CreateEditRoleSavePayload,
    PermissionManagementPageRead,
    PermissionManagementSavePayload,
    RoleAssignmentPageRead,
    RoleAssignmentSubmitPayload,
    RoleAssignmentSubmitResponse,
    AccountStatusPageRead,
    AccountStatusSuspendPayload,
    AccountStatusSuspendResponse,
    LoginAccountActivityPageRead,
    AcademicPerformanceOverviewRead,
    AttendanceOverviewRead,
    ExaminationOverviewRead,
    FinanceOverviewRead,
    PendingApprovalOverviewRead,
    RecentActivitiesOverviewRead,
    AlertsOverviewRead,
    AllDepartmentsListPageRead,
    CreateEditDepartmentPageRead,
    CreateEditDepartmentSavePayload,
    DepartmentDetailsPageRead,
    DepartmentHeadAssignmentPageRead,
    DepartmentHeadAssignmentSavePayload,
    DepartmentHeadAssignmentSaveResult,
    OrganizationalHierarchyPageRead,
    ProgrammeCourseMappingPageRead,
    DepartmentFacultyAllocationPageRead,
    DepartmentFacultyAllocationSavePayload,
    DepartmentFacultyAllocationSaveResult,
    DepartmentStatusHistoryPageRead,
    DepartmentResourceManagementPageRead,
    DepartmentManagementDashboardPageRead,
    DepartmentPerformanceOverviewRead,
    FacultyStatisticsOverviewRead,
    StudentStatisticsOverviewRead,
    InstitutionProfileRead,
    InstitutionBrandingAssetRead,
    InstitutionBrandingDraftUpdate,
    InstitutionBrandingPageRead,
    InstitutionInformationPageRead,
    InstitutionProfileDraftUpdate,
    InstitutionProfilePageRead,
    InstitutionProfileUpdate,
    InstitutionSettingsRead,
    OperationalSummariesRead,
    PendingApprovalItem,
    FacultyEmployeeDashboardPageRead,
)
from app.modules.college_admin.settings_registry import InstitutionBrandingUpdate, InstitutionSettingsUpdate
from app.modules.college_admin.academic_routes import router as academic_config_router
from app.modules.college_admin.student_admin_routes import router as student_admin_router
from app.modules.parents.college_admin_routes import router as parent_admin_router
from app.modules.college_admin.faculty_admin_routes import router as faculty_admin_router
from app.modules.college_admin.faculty_employee_dashboard_page_service import (
    get_faculty_employee_dashboard_page,
)
from app.modules.college_admin.attendance_admin_routes import router as attendance_admin_router
from app.modules.college_admin.examination_admin_routes import router as examination_admin_router
from app.modules.college_admin.finance_admin_routes import router as finance_admin_router
from app.modules.college_admin.hr_admin_routes import router as hr_admin_router
from app.modules.college_admin.library_admin_routes import router as library_admin_router
from app.modules.college_admin.hostel_admin_routes import router as hostel_admin_router
from app.modules.college_admin.communication_admin_routes import router as communication_admin_router
from app.modules.college_admin.lms_admin_routes import router as lms_admin_router
from app.modules.college_admin.reports_admin_routes import router as reports_admin_router
from app.modules.college_admin.workflow_admin_routes import router as workflow_admin_router
from app.modules.college_admin.security_admin_routes import router as security_admin_router
from app.modules.college_admin.import_admin_routes import router as import_admin_router
from app.modules.college_admin.integration_admin_routes import router as integration_admin_router
from app.modules.college_admin.helpdesk_admin_routes import router as helpdesk_admin_router
from app.modules.college_admin.finance_ext_routes import router as finance_ext_router
from app.modules.college_admin.operations_ext_routes import router as operations_ext_router

router = APIRouter()

router.include_router(academic_config_router, prefix="/academic-config", tags=["college-admin-academic-config"])
router.include_router(student_admin_router, prefix="/student-administration", tags=["college-admin-student-admin"])
router.include_router(parent_admin_router, prefix="/parent-administration", tags=["college-admin-parent-admin"])
router.include_router(faculty_admin_router, prefix="/faculty-administration", tags=["college-admin-faculty-admin"])


@router.get(
    "/faculty-administration/dashboard/page",
    response_model=ApiResponse[FacultyEmployeeDashboardPageRead],
    tags=["college-admin-faculty-admin"],
)
async def faculty_employee_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_code: str | None = None,
    department_id: str | None = None,
    page: int = 1,
    page_size: int = 6,
) -> ApiResponse[FacultyEmployeeDashboardPageRead]:
    return success_response(
        await get_faculty_employee_dashboard_page(
            scope,
            academic_year_code=academic_year_code,
            department_id=department_id or None,
            page=page,
            page_size=page_size,
        ),
        request_id=get_request_id(),
    )


router.include_router(attendance_admin_router, prefix="/attendance-administration", tags=["college-admin-attendance-admin"])
router.include_router(examination_admin_router, prefix="/examination-administration", tags=["college-admin-examination-admin"])
router.include_router(finance_admin_router, prefix="/finance-administration", tags=["college-admin-finance-admin"])
router.include_router(hr_admin_router, prefix="/hr-administration", tags=["college-admin-hr-admin"])
router.include_router(library_admin_router, prefix="/library-administration", tags=["college-admin-library-admin"])
router.include_router(hostel_admin_router, prefix="/hostel-administration", tags=["college-admin-hostel-admin"])
router.include_router(communication_admin_router, prefix="/communication-administration", tags=["college-admin-communication-admin"])
router.include_router(lms_admin_router, prefix="/lms-administration", tags=["college-admin-lms-admin"])
router.include_router(reports_admin_router, prefix="/reports-analytics", tags=["college-admin-reports-analytics"])
router.include_router(workflow_admin_router, prefix="/workflow-administration", tags=["college-admin-workflow-admin"])
router.include_router(security_admin_router, prefix="/security-administration", tags=["college-admin-security-admin"])
router.include_router(import_admin_router, prefix="/data-import", tags=["college-admin-data-import"])
router.include_router(integration_admin_router, prefix="/integration-administration", tags=["college-admin-integration-admin"])
router.include_router(helpdesk_admin_router, prefix="/helpdesk", tags=["college-admin-helpdesk"])
router.include_router(finance_ext_router, prefix="/finance-extensions", tags=["college-admin-finance-extensions"])
router.include_router(operations_ext_router, prefix="/operations-extensions", tags=["college-admin-operations-extensions"])


@router.get("/dashboard", response_model=ApiResponse[CollegeDashboardOverview])
async def dashboard_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    anchor_date: Annotated[date | None, Query(description="Dashboard anchor date (UTC calendar day)")] = None,
    date_range: Annotated[DashboardDateRange, Query(alias="range")] = DashboardDateRange.WEEK,
    department_id: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[CollegeDashboardOverview]:
    data = await get_dashboard_overview(
        scope,
        user,
        anchor_date=anchor_date,
        date_range=date_range,
        department_id=department_id,
        campus_id=campus_id,
        academic_year_label=academic_year_label,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/statistics", response_model=ApiResponse[CollegeDashboardStatsRead])
async def dashboard_statistics_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    department_id: Annotated[str | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[CollegeDashboardStatsRead]:
    data = await get_institutional_statistics(
        scope,
        department_id=department_id,
        academic_year_label=academic_year_label,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/operations", response_model=ApiResponse[OperationalSummariesRead])
async def dashboard_operations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[OperationalSummariesRead]:
    data = await get_operational_summaries(scope, academic_year_label=academic_year_label)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/pending-approvals", response_model=ApiResponse[Page[PendingApprovalItem]])
async def dashboard_pending_approvals_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    department_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[PendingApprovalItem]]:
    data = await get_pending_approvals(scope, department_id=department_id, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/activities", response_model=ApiResponse[Page[ActivitySummary]])
async def dashboard_activities_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[DashboardDateRange, Query(alias="range")] = DashboardDateRange.WEEK,
) -> ApiResponse[Page[ActivitySummary]]:
    data = await get_recent_activities(
        scope,
        anchor_date=anchor_date,
        date_range=date_range,
        pagination=pagination,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/institution/overview", response_model=ApiResponse[InstitutionalOverviewRead])
async def institution_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionalOverviewRead]:
    data = await get_institutional_overview(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/academic-performance", response_model=ApiResponse[AcademicPerformanceOverviewRead])
async def academic_performance_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    study_year: Annotated[int | None, Query(ge=1, le=6)] = None,
) -> ApiResponse[AcademicPerformanceOverviewRead]:
    data = await get_academic_performance_overview(
        scope,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        programme_code=programme_code,
        study_year=study_year,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/attendance-overview", response_model=ApiResponse[AttendanceOverviewRead])
async def attendance_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[DashboardDateRange, Query(alias="range")] = DashboardDateRange.MONTH,
    department_id: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[AttendanceOverviewRead]:
    data = await get_attendance_overview(
        scope,
        anchor_date=anchor_date,
        date_range=date_range,
        department_id=department_id,
        programme_code=programme_code,
        campus_id=campus_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/examination-overview", response_model=ApiResponse[ExaminationOverviewRead])
async def examination_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    exam_session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[ExaminationOverviewRead]:
    data = await get_examination_overview(
        scope,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        exam_session_id=exam_session_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/alerts-overview", response_model=ApiResponse[AlertsOverviewRead])
async def alerts_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AlertsOverviewRead]:
    data = await get_alerts_overview(scope, user)
    return success_response(data, request_id=get_request_id())


@router.post("/dashboard/alerts-overview/mark-read", response_model=ApiResponse[dict])
async def alerts_mark_read_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    data = await mark_dashboard_alerts_read(scope, user)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/recent-activities-overview", response_model=ApiResponse[RecentActivitiesOverviewRead])
async def recent_activities_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[DashboardDateRange | None, Query(alias="range")] = DashboardDateRange.TODAY,
    module_key: Annotated[str | None, Query()] = None,
    user_id: Annotated[str | None, Query()] = None,
    feed_offset: Annotated[int, Query(ge=0)] = 0,
    feed_limit: Annotated[int, Query(ge=1, le=50)] = 9,
) -> ApiResponse[RecentActivitiesOverviewRead]:
    data = await get_recent_activities_overview(
        scope,
        anchor_date=anchor_date,
        date_range=date_range,
        module_key=module_key,
        user_id=user_id,
        feed_offset=feed_offset,
        feed_limit=feed_limit,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/pending-approvals-overview", response_model=ApiResponse[PendingApprovalOverviewRead])
async def pending_approvals_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    date_range: Annotated[DashboardDateRange | None, Query(alias="range")] = None,
    module_key: Annotated[str | None, Query()] = None,
    requester_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[PendingApprovalOverviewRead]:
    data = await get_pending_approvals_overview(
        scope,
        date_range=date_range,
        module_key=module_key,
        requester_id=requester_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/finance-summary", response_model=ApiResponse[FinanceOverviewRead])
async def finance_summary_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    fee_head: Annotated[str | None, Query()] = None,
) -> ApiResponse[FinanceOverviewRead]:
    data = await get_finance_overview(
        scope,
        academic_year_label=academic_year_label,
        programme_code=programme_code,
        fee_head=fee_head,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/department-performance", response_model=ApiResponse[DepartmentPerformanceOverviewRead])
async def department_performance_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    programme_level: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[DepartmentPerformanceOverviewRead]:
    data = await get_department_performance_overview(
        scope,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        programme_code=programme_code,
        programme_level=programme_level,
        campus_id=campus_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/student-statistics", response_model=ApiResponse[StudentStatisticsOverviewRead])
async def student_statistics_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    study_year: Annotated[int | None, Query(ge=1, le=6)] = None,
    department_id: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[StudentStatisticsOverviewRead]:
    data = await get_student_statistics_overview(
        scope,
        academic_year_label=academic_year_label,
        programme_code=programme_code,
        study_year=study_year,
        department_id=department_id,
        campus_id=campus_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/faculty-statistics", response_model=ApiResponse[FacultyStatisticsOverviewRead])
async def faculty_statistics_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[DashboardDateRange, Query(alias="range")] = DashboardDateRange.TODAY,
    department_id: Annotated[str | None, Query()] = None,
    designation: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[FacultyStatisticsOverviewRead]:
    data = await get_faculty_statistics_overview(
        scope,
        anchor_date=anchor_date,
        date_range=date_range,
        department_id=department_id,
        designation=designation,
        campus_id=campus_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/institution/profile", response_model=ApiResponse[InstitutionProfileRead])
async def institution_profile_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionProfileRead]:
    data = await get_institution_profile(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/institution/profile/page", response_model=ApiResponse[InstitutionProfilePageRead])
async def institution_profile_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionProfilePageRead]:
    data = await get_institution_profile_page(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/institution/information/page", response_model=ApiResponse[InstitutionInformationPageRead])
async def institution_information_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionInformationPageRead]:
    data = await get_institution_information_page(scope)
    return success_response(data, request_id=get_request_id())


@router.put("/institution/information/draft", response_model=ApiResponse[InstitutionInformationPageRead])
async def institution_information_draft_route(
    payload: InstitutionProfileDraftUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[InstitutionInformationPageRead]:
    data = await save_institution_profile_draft(scope, payload.values)
    return success_response(data, request_id=get_request_id())


@router.post("/institution/information/save", response_model=ApiResponse[InstitutionInformationPageRead])
async def institution_information_save_route(
    payload: InstitutionProfileDraftUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[InstitutionInformationPageRead]:
    data = await publish_institution_information(scope, payload.values)
    return success_response(data, request_id=get_request_id())


@router.get("/institution/branding/page", response_model=ApiResponse[InstitutionBrandingPageRead])
async def institution_branding_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionBrandingPageRead]:
    data = await get_institution_branding_page(scope)
    return success_response(data, request_id=get_request_id())


@router.put("/institution/branding/draft", response_model=ApiResponse[InstitutionBrandingPageRead])
async def institution_branding_draft_route(
    payload: InstitutionBrandingDraftUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[InstitutionBrandingPageRead]:
    data = await save_institution_branding_draft(scope, payload.values)
    return success_response(data, request_id=get_request_id())


@router.post("/institution/branding/publish", response_model=ApiResponse[InstitutionBrandingPageRead])
async def institution_branding_publish_route(
    payload: InstitutionBrandingDraftUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[InstitutionBrandingPageRead]:
    data = await publish_institution_branding(scope, payload.values)
    return success_response(data, request_id=get_request_id())


@router.post(
    "/institution/branding/assets/{asset_key}",
    response_model=ApiResponse[InstitutionBrandingAssetRead],
)
async def institution_branding_asset_upload_route(
    asset_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
    file: Annotated[UploadFile, File()],
) -> ApiResponse[InstitutionBrandingAssetRead]:
    data = await upload_branding_asset(scope, asset_key, file)
    return success_response(data, request_id=get_request_id())


@router.patch("/institution/profile", response_model=ApiResponse[InstitutionProfileRead])
async def institution_profile_update_route(
    payload: InstitutionProfileUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[InstitutionProfileRead]:
    data = await update_institution_profile(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/institution/campuses/dashboard",
    response_model=ApiResponse[CampusManagementDashboardRead],
)
async def institution_campuses_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CampusManagementDashboardRead]:
    data = await get_campus_management_dashboard(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/institution/campuses", response_model=ApiResponse[list[CampusRead]])
async def institution_campuses_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    active_only: Annotated[bool, Query()] = False,
) -> ApiResponse[list[CampusRead]]:
    data = await list_campuses(scope, active_only=active_only)
    return success_response(data, request_id=get_request_id())


@router.post("/institution/campuses", response_model=ApiResponse[CampusRead], status_code=status.HTTP_201_CREATED)
async def institution_campus_create_route(
    payload: CampusCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CampusRead]:
    data = await create_campus(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/institution/campuses/{campus_id}/page",
    response_model=ApiResponse[CampusDetailPageRead],
)
async def institution_campus_detail_page_route(
    campus_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CampusDetailPageRead]:
    data = await get_campus_detail_page(scope, to_object_id(campus_id, "campus id"))
    return success_response(data, request_id=get_request_id())


@router.get(
    "/institution/campuses/{campus_id}/contact/page",
    response_model=ApiResponse[CampusContactPageRead],
)
async def institution_campus_contact_page_route(
    campus_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CampusContactPageRead]:
    data = await get_campus_contact_page(scope, to_object_id(campus_id, "campus id"))
    return success_response(data, request_id=get_request_id())


@router.put(
    "/institution/campuses/{campus_id}/contact/page",
    response_model=ApiResponse[CampusContactPageRead],
)
async def institution_campus_contact_save_route(
    campus_id: str,
    payload: CampusContactPageSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[CampusContactPageRead]:
    data = await save_campus_contact_page(scope, to_object_id(campus_id, "campus id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/institution/campuses/{campus_id}", response_model=ApiResponse[CampusRead])
async def institution_campus_detail_route(
    campus_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CampusRead]:
    data = await get_campus(scope, to_object_id(campus_id, "campus id"))
    return success_response(data, request_id=get_request_id())


@router.patch("/institution/campuses/{campus_id}", response_model=ApiResponse[CampusRead])
async def institution_campus_update_route(
    campus_id: str,
    payload: CampusUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CampusRead]:
    data = await update_campus(scope, to_object_id(campus_id, "campus id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/institution/academic-year/page",
    response_model=ApiResponse[AcademicYearConfigurationPageRead],
)
async def institution_academic_year_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    selected_year_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[AcademicYearConfigurationPageRead]:
    data = await get_academic_year_configuration_page(scope, selected_year_id=selected_year_id)
    return success_response(data, request_id=get_request_id())


@router.put(
    "/institution/academic-year/{year_id}/configuration",
    response_model=ApiResponse[AcademicYearConfigurationPageRead],
)
async def institution_academic_year_save_route(
    year_id: str,
    payload: AcademicYearConfigurationSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[AcademicYearConfigurationPageRead]:
    data = await save_academic_year_configuration(
        scope,
        to_object_id(year_id, "year_id"),
        payload,
    )
    return success_response(data, request_id=get_request_id())


@router.post(
    "/institution/academic-year/copy-previous",
    response_model=ApiResponse[AcademicYearConfigurationPageRead],
)
async def institution_academic_year_copy_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[AcademicYearConfigurationPageRead]:
    data = await copy_academic_year_from_previous(scope)
    return success_response(data, request_id=get_request_id())


@router.post(
    "/institution/academic-year/new",
    response_model=ApiResponse[AcademicYearConfigurationPageRead],
)
async def institution_academic_year_new_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[AcademicYearConfigurationPageRead]:
    data = await create_blank_academic_year(scope)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/institution/calendar/page",
    response_model=ApiResponse[InstitutionCalendarSettingsPageRead],
)
async def institution_calendar_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    academic_year_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[InstitutionCalendarSettingsPageRead]:
    data = await get_institution_calendar_settings_page(
        scope,
        page=page,
        academic_year_id=academic_year_id,
    )
    return success_response(data, request_id=get_request_id())


@router.put(
    "/institution/calendar/page",
    response_model=ApiResponse[InstitutionCalendarSettingsPageRead],
)
async def institution_calendar_save_route(
    payload: InstitutionCalendarSettingsSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[InstitutionCalendarSettingsPageRead]:
    data = await save_institution_calendar_settings_page(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post(
    "/institution/calendar/import-holidays",
    response_model=ApiResponse[InstitutionCalendarSettingsPageRead],
)
async def institution_calendar_import_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[InstitutionCalendarSettingsPageRead]:
    data = await import_institution_holidays_from_previous(scope)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/institution/policies/page",
    response_model=ApiResponse[InstitutionPoliciesPageRead],
)
async def institution_policies_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    search: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    audience: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 6,
    selected_policy_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[InstitutionPoliciesPageRead]:
    data = await get_institution_policies_page(
        scope,
        search=search,
        category=category or None,
        audience=audience or None,
        status=status or None,
        page=page,
        page_size=page_size,
        selected_policy_id=selected_policy_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get(
    "/institution/academic-settings/page",
    response_model=ApiResponse[AcademicInstitutionSettingsPageRead],
)
async def institution_academic_settings_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AcademicInstitutionSettingsPageRead]:
    data = await get_academic_institution_settings_page(scope)
    return success_response(data, request_id=get_request_id())


@router.put(
    "/institution/academic-settings/page",
    response_model=ApiResponse[AcademicInstitutionSettingsPageRead],
)
async def institution_academic_settings_save_route(
    payload: AcademicInstitutionSettingsSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[AcademicInstitutionSettingsPageRead]:
    data = await save_academic_institution_settings_page(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post(
    "/institution/academic-settings/reset",
    response_model=ApiResponse[AcademicInstitutionSettingsPageRead],
)
async def institution_academic_settings_reset_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[AcademicInstitutionSettingsPageRead]:
    data = await reset_academic_institution_settings_page(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/institution/settings", response_model=ApiResponse[InstitutionSettingsRead])
async def institution_settings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionSettingsRead]:
    data = await get_institution_settings(scope)
    return success_response(data, request_id=get_request_id())


class InstitutionSettingsPatchBody(InstitutionSettingsUpdate):
    branding: InstitutionBrandingUpdate | None = None


@router.patch("/institution/settings", response_model=ApiResponse[InstitutionSettingsRead])
async def institution_settings_update_route(
    payload: InstitutionSettingsPatchBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[InstitutionSettingsRead]:
    branding = payload.branding
    settings_payload = InstitutionSettingsUpdate(**payload.model_dump(exclude={"branding"}, exclude_none=True))
    data = await update_institution_settings(scope, settings_payload, branding=branding)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/institution/configuration-history/page",
    response_model=ApiResponse[ConfigurationHistoryPageRead],
)
async def institution_configuration_history_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    date_range: Annotated[str, Query()] = "last_90_days",
    setting_area: Annotated[str | None, Query()] = None,
    actor_id: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
    selected_change_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[ConfigurationHistoryPageRead]:
    data = await get_institution_configuration_history_page(
        scope,
        page=page,
        date_range=date_range,
        setting_area=setting_area,
        actor_id=actor_id,
        search=search,
        selected_change_id=selected_change_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/institution/configuration-history", response_model=ApiResponse[list[InstitutionConfigurationHistoryItem]])
async def institution_configuration_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[InstitutionConfigurationHistoryItem]]:
    data = await get_configuration_history(scope)
    return success_response(data, request_id=get_request_id())


from app.modules.college_admin.identity_schemas import (
    AccessHistoryRead,
    AccountStatusChange,
    BulkUserCreate,
    DepartmentHeadAssign,
    DepartmentHistoryRead,
    DepartmentTransfer,
    InstitutionDepartmentCreate,
    InstitutionDepartmentRead,
    InstitutionDepartmentUpdate,
    InstitutionRoleCreate,
    InstitutionRoleRead,
    InstitutionRoleUpdate,
    InstitutionUserCreate,
    InstitutionUserInvite,
    InstitutionUserRead,
    InstitutionUserUpdate,
    InvitationAccept,
    InvitationCreateResponse,
    OrganizationUnitCreate,
    OrganizationUnitRead,
    PermissionRead,
    UserRoleAssign,
    UserRoleRevoke,
)
from app.modules.college_admin.organization_service import (
    assign_department_head,
    associate_department_staff,
    create_institution_department,
    create_organization_unit,
    get_department_history,
    get_institution_department,
    list_institution_departments,
    list_organization_units,
    transfer_department,
    update_institution_department,
)
from app.modules.college_admin.role_management_service import (
    create_institution_role,
    list_institution_roles,
    list_permissions,
    update_institution_role,
)
from app.modules.college_admin.user_management_dashboard_page_service import (
    get_user_management_dashboard_page,
)
from app.modules.college_admin.user_all_users_list_page_service import get_all_users_list_page
from app.modules.college_admin.user_details_page_service import get_user_details_page_by_id
from app.modules.college_admin.edit_user_information_page_service import (
    get_edit_user_information_page_by_id,
    save_edit_user_information,
)
from app.modules.college_admin.role_management_dashboard_page_service import get_role_management_dashboard_page
from app.modules.college_admin.create_edit_role_page_service import (
    get_create_edit_role_page_by_id,
    save_create_edit_role,
)
from app.modules.college_admin.permission_management_page_service import (
    get_permission_management_page,
    get_permission_management_page_export,
    save_permission_management_matrix,
)
from app.modules.college_admin.role_assignment_page_service import (
    get_role_assignment_page,
    submit_role_assignment,
)
from app.modules.college_admin.account_status_page_service import (
    export_account_status_csv,
    get_account_status_page,
    submit_account_suspension,
)
from app.modules.college_admin.login_account_activity_page_service import (
    export_login_account_activity_csv,
    get_login_account_activity_page,
)
from app.modules.college_admin.bulk_user_invitation_page_service import (
    bulk_invitation_template_csv,
    get_bulk_user_invitation_page,
    send_bulk_user_invitations,
    update_bulk_user_invitation_settings,
    upload_bulk_user_invitation,
)
from app.modules.college_admin.create_new_user_page_service import (
    get_create_new_user_page,
    save_create_new_user_draft,
    submit_create_new_user,
    validate_create_new_user,
)
from app.modules.college_admin.user_management_service import (
    accept_institution_invitation,
    accept_password_reset,
    activate_user,
    assign_user_roles,
    bulk_create_users,
    create_institution_user,
    deactivate_user,
    get_institution_user,
    get_user_access_history,
    invite_institution_user,
    list_institution_users,
    reset_user_access,
    revoke_user_role,
    revoke_user_sessions,
    suspend_user,
    update_institution_user,
)


@router.post("/users", response_model=ApiResponse[InstitutionUserRead], status_code=status.HTTP_201_CREATED)
async def create_user_route(
    payload: InstitutionUserCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await create_institution_user(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/invite", response_model=ApiResponse[InvitationCreateResponse], status_code=status.HTTP_201_CREATED)
async def invite_user_route(
    payload: InstitutionUserInvite,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InvitationCreateResponse]:
    data = await invite_institution_user(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/invitations/accept", response_model=ApiResponse[InstitutionUserRead])
async def accept_invitation_route(payload: InvitationAccept) -> ApiResponse[InstitutionUserRead]:
    data = await accept_institution_invitation(payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/password-reset/accept", response_model=ApiResponse[dict])
async def accept_password_reset_route(payload: InvitationAccept) -> ApiResponse[dict]:
    data = await accept_password_reset(payload)
    return success_response(data, request_id=get_request_id())


@router.get("/users/all-users-list/page", response_model=ApiResponse[UserAllUsersListPageRead])
async def all_users_list_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    search: Annotated[str | None, Query()] = None,
    role_filter: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query()] = None,
) -> ApiResponse[UserAllUsersListPageRead]:
    data = await get_all_users_list_page(
        scope,
        page=page,
        search=search,
        role_filter=role_filter or None,
        department_id=department_id,
        status_filter=status_filter or None,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/users/management-dashboard/page", response_model=ApiResponse[UserDashboardPageRead])
async def user_management_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    date_range: Annotated[str, Query()] = "last_30_days",
    role_filter: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[UserDashboardPageRead]:
    data = await get_user_management_dashboard_page(
        scope,
        date_range=date_range,
        role_filter=role_filter or None,
        department_id=department_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/users/bulk-user-invitation/template")
async def bulk_user_invitation_template_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    from fastapi.responses import PlainTextResponse

    _ = scope
    return PlainTextResponse(
        bulk_invitation_template_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="bulk_invite_template.csv"'},
    )


@router.get("/users/login-account-activity/page", response_model=ApiResponse[LoginAccountActivityPageRead])
async def login_account_activity_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    date_range: Annotated[str, Query()] = "last_7_days",
    role_filter: Annotated[str, Query()] = "",
    location_filter: Annotated[str, Query()] = "",
) -> ApiResponse[LoginAccountActivityPageRead]:
    data = await get_login_account_activity_page(
        scope,
        date_range=date_range,
        role_filter=role_filter,
        location_filter=location_filter,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/users/login-account-activity/export")
async def login_account_activity_export_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    date_range: Annotated[str, Query()] = "last_7_days",
    role_filter: Annotated[str, Query()] = "",
    location_filter: Annotated[str, Query()] = "",
):
    from fastapi.responses import PlainTextResponse

    csv_text = await export_login_account_activity_csv(
        scope,
        date_range=date_range,
        role_filter=role_filter,
        location_filter=location_filter,
    )
    return PlainTextResponse(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="login_account_activity.csv"'},
    )


@router.get("/users/account-status/page", response_model=ApiResponse[AccountStatusPageRead])
async def account_status_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    tab: Annotated[str, Query()] = "suspended",
    page: Annotated[int, Query(ge=1)] = 1,
    user_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[AccountStatusPageRead]:
    data = await get_account_status_page(scope, tab=tab, page=page, user_id_raw=user_id)
    return success_response(data, request_id=get_request_id())


@router.post("/users/account-status/suspend", response_model=ApiResponse[AccountStatusSuspendResponse])
async def account_status_suspend_route(
    payload: AccountStatusSuspendPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AccountStatusSuspendResponse]:
    data = await submit_account_suspension(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/users/account-status/export")
async def account_status_export_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    tab: Annotated[str, Query()] = "suspended",
):
    from fastapi.responses import PlainTextResponse

    csv_text = await export_account_status_csv(scope, tab=tab)
    return PlainTextResponse(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="account_status_{tab}.csv"'},
    )


@router.get("/users/role-assignment/page", response_model=ApiResponse[RoleAssignmentPageRead])
async def role_assignment_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    user_id: Annotated[str | None, Query()] = None,
    role_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[RoleAssignmentPageRead]:
    data = await get_role_assignment_page(scope, user_id_raw=user_id, role_id_raw=role_id)
    return success_response(data, request_id=get_request_id())


@router.post("/users/role-assignment/submit", response_model=ApiResponse[RoleAssignmentSubmitResponse])
async def role_assignment_submit_route(
    payload: RoleAssignmentSubmitPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[RoleAssignmentSubmitResponse]:
    data = await submit_role_assignment(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/users/bulk-user-invitation/page", response_model=ApiResponse[BulkUserInvitationPageRead])
async def bulk_user_invitation_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[BulkUserInvitationPageRead]:
    data = await get_bulk_user_invitation_page(scope, page=page)
    return success_response(data, request_id=get_request_id())


@router.post("/users/bulk-user-invitation/upload", response_model=ApiResponse[BulkUserInvitationPageRead])
async def bulk_user_invitation_upload_route(
    payload: BulkUserInvitationUploadPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[BulkUserInvitationPageRead]:
    data = await upload_bulk_user_invitation(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.put("/users/bulk-user-invitation/settings", response_model=ApiResponse[BulkUserInvitationPageRead])
async def bulk_user_invitation_settings_route(
    payload: BulkUserInvitationStepPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[BulkUserInvitationPageRead]:
    data = await update_bulk_user_invitation_settings(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/bulk-user-invitation/send", response_model=ApiResponse[BulkUserInvitationSendResponse])
async def bulk_user_invitation_send_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[BulkUserInvitationSendResponse]:
    data = await send_bulk_user_invitations(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/users/create-new-user/page", response_model=ApiResponse[CreateNewUserPageRead])
async def create_new_user_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CreateNewUserPageRead]:
    data = await get_create_new_user_page(scope)
    return success_response(data, request_id=get_request_id())


@router.put("/users/create-new-user/draft", response_model=ApiResponse[CreateNewUserPageRead])
async def create_new_user_draft_route(
    payload: CreateNewUserDraftUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CreateNewUserPageRead]:
    data = await save_create_new_user_draft(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/create-new-user/validate", response_model=ApiResponse[CreateNewUserValidateResponse])
async def create_new_user_validate_route(
    payload: CreateNewUserValidatePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CreateNewUserValidateResponse]:
    data = await validate_create_new_user(scope, payload.values)
    return success_response(data, request_id=get_request_id())


@router.post("/users/create-new-user/submit", response_model=ApiResponse[CreateNewUserSubmitResponse])
async def create_new_user_submit_route(
    payload: CreateNewUserSubmitPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CreateNewUserSubmitResponse]:
    data = await submit_create_new_user(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/users/edit-user-information/page", response_model=ApiResponse[EditUserInformationPageRead])
async def edit_user_information_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    user_id: Annotated[str, Query(description="Institution user id")],
) -> ApiResponse[EditUserInformationPageRead]:
    data = await get_edit_user_information_page_by_id(scope, user_id)
    return success_response(data, request_id=get_request_id())


@router.put("/users/edit-user-information/save", response_model=ApiResponse[EditUserInformationPageRead])
async def edit_user_information_save_route(
    payload: EditUserInformationSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[EditUserInformationPageRead]:
    data = await save_edit_user_information(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/users/user-details/page", response_model=ApiResponse[UserDetailsPageRead])
async def user_details_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    user_id: Annotated[str, Query(description="Institution user id")],
) -> ApiResponse[UserDetailsPageRead]:
    data = await get_user_details_page_by_id(scope, user_id)
    return success_response(data, request_id=get_request_id())


@router.get("/users", response_model=ApiResponse[Page[InstitutionUserRead]])
async def list_users_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[InstitutionUserRead]]:
    data = await list_institution_users(scope, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/users/{user_id}", response_model=ApiResponse[InstitutionUserRead])
async def get_user_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await get_institution_user(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.patch("/users/{user_id}", response_model=ApiResponse[InstitutionUserRead])
async def update_user_route(
    user_id: str,
    payload: InstitutionUserUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await update_institution_user(scope, to_object_id(user_id, "user id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/activate", response_model=ApiResponse[InstitutionUserRead])
async def activate_user_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await activate_user(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/suspend", response_model=ApiResponse[InstitutionUserRead])
async def suspend_user_route(
    user_id: str,
    payload: AccountStatusChange,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await suspend_user(scope, to_object_id(user_id, "user id"), reason=payload.reason)
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/deactivate", response_model=ApiResponse[InstitutionUserRead])
async def deactivate_user_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await deactivate_user(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/roles", response_model=ApiResponse[InstitutionUserRead])
async def assign_roles_route(
    user_id: str,
    payload: UserRoleAssign,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await assign_user_roles(scope, to_object_id(user_id, "user id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/roles/revoke", response_model=ApiResponse[InstitutionUserRead])
async def revoke_role_route(
    user_id: str,
    payload: UserRoleRevoke,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await revoke_user_role(scope, to_object_id(user_id, "user id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/sessions/revoke", response_model=ApiResponse[dict])
async def revoke_sessions_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    data = await revoke_user_sessions(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/reset-access", response_model=ApiResponse[dict])
async def reset_access_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    data = await reset_user_access(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.post("/users/bulk", response_model=ApiResponse[list[InstitutionUserRead]])
async def bulk_users_route(
    payload: BulkUserCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[InstitutionUserRead]]:
    data = await bulk_create_users(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/users/{user_id}/access-history", response_model=ApiResponse[list[AccessHistoryRead]])
async def user_access_history_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[AccessHistoryRead]]:
    data = await get_user_access_history(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.get("/roles/management-dashboard/page", response_model=ApiResponse[RoleManagementDashboardPageRead])
async def role_management_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[RoleManagementDashboardPageRead]:
    data = await get_role_management_dashboard_page(scope, page=page)
    return success_response(data, request_id=get_request_id())


@router.get("/roles/create-edit/page", response_model=ApiResponse[CreateEditRolePageRead])
async def create_edit_role_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    role_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[CreateEditRolePageRead]:
    data = await get_create_edit_role_page_by_id(scope, role_id)
    return success_response(data, request_id=get_request_id())


@router.post("/roles/create-edit/save", response_model=ApiResponse[CreateEditRolePageRead])
async def create_edit_role_save_route(
    payload: CreateEditRoleSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CreateEditRolePageRead]:
    data = await save_create_edit_role(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/permissions/management-matrix/page", response_model=ApiResponse[PermissionManagementPageRead])
async def permission_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[PermissionManagementPageRead]:
    data = await get_permission_management_page(scope)
    return success_response(data, request_id=get_request_id())


@router.post(
    "/permissions/management-matrix/save",
    response_model=ApiResponse[PermissionManagementPageRead],
)
async def permission_management_save_route(
    payload: PermissionManagementSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[PermissionManagementPageRead]:
    data = await save_permission_management_matrix(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/permissions/management-matrix/export")
async def permission_management_export_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    from fastapi.responses import PlainTextResponse

    csv_text = await get_permission_management_page_export(scope)
    return PlainTextResponse(
        csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="permission_matrix.csv"'},
    )


@router.get("/roles", response_model=ApiResponse[list[InstitutionRoleRead]])
async def list_roles_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[InstitutionRoleRead]]:
    data = await list_institution_roles(scope)
    return success_response(data, request_id=get_request_id())


@router.post("/roles", response_model=ApiResponse[InstitutionRoleRead], status_code=status.HTTP_201_CREATED)
async def create_role_route(
    payload: InstitutionRoleCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionRoleRead]:
    data = await create_institution_role(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.patch("/roles/{role_id}", response_model=ApiResponse[InstitutionRoleRead])
async def update_role_route(
    role_id: str,
    payload: InstitutionRoleUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionRoleRead]:
    data = await update_institution_role(scope, to_object_id(role_id, "role id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/permissions", response_model=ApiResponse[list[PermissionRead]])
async def list_permissions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[PermissionRead]]:
    data = await list_permissions(scope)
    return success_response(data, request_id=get_request_id())


@router.post("/organization/units", response_model=ApiResponse[OrganizationUnitRead], status_code=status.HTTP_201_CREATED)
async def create_org_unit_route(
    payload: OrganizationUnitCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[OrganizationUnitRead]:
    data = await create_organization_unit(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/organization/units", response_model=ApiResponse[list[OrganizationUnitRead]])
async def list_org_units_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[OrganizationUnitRead]]:
    data = await list_organization_units(scope)
    return success_response(data, request_id=get_request_id())


@router.post("/departments", response_model=ApiResponse[InstitutionDepartmentRead], status_code=status.HTTP_201_CREATED)
async def create_department_route(
    payload: InstitutionDepartmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionDepartmentRead]:
    data = await create_institution_department(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/departments", response_model=ApiResponse[Page[InstitutionDepartmentRead]])
async def list_departments_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[InstitutionDepartmentRead]]:
    data = await list_institution_departments(scope, pagination)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/departments/details/page",
    response_model=ApiResponse[DepartmentDetailsPageRead],
)
async def department_details_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    department_id: Annotated[str, Query()],
) -> ApiResponse[DepartmentDetailsPageRead]:
    data = await get_department_details_page_by_id(scope, department_id)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/departments/create-edit/page",
    response_model=ApiResponse[CreateEditDepartmentPageRead],
)
async def create_edit_department_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    department_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[CreateEditDepartmentPageRead]:
    data = await get_create_edit_department_page_by_id(scope, department_id)
    return success_response(data, request_id=get_request_id())


@router.post(
    "/departments/create-edit/save",
    response_model=ApiResponse[CreateEditDepartmentPageRead],
)
async def create_edit_department_save_route(
    payload: CreateEditDepartmentSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CreateEditDepartmentPageRead]:
    data = await save_create_edit_department(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/departments/all-departments/page",
    response_model=ApiResponse[AllDepartmentsListPageRead],
)
async def all_departments_list_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    search: Annotated[str | None, Query()] = None,
    school_id: Annotated[str | None, Query()] = None,
    type_filter: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query()] = None,
) -> ApiResponse[AllDepartmentsListPageRead]:
    data = await get_all_departments_list_page(
        scope,
        page=page,
        search=search,
        school_id=school_id,
        type_filter=type_filter,
        status_filter=status_filter,
    )
    return success_response(data, request_id=get_request_id())


@router.get(
    "/departments/faculty-allocation/page",
    response_model=ApiResponse[DepartmentFacultyAllocationPageRead],
)
async def department_faculty_allocation_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    semester_label: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
    designation_filter: Annotated[str | None, Query()] = None,
) -> ApiResponse[DepartmentFacultyAllocationPageRead]:
    data = await get_department_faculty_allocation_page(
        scope,
        page=page,
        semester_label=semester_label,
        department_id=department_id,
        designation_filter=designation_filter,
    )
    return success_response(data, request_id=get_request_id())


@router.post(
    "/departments/faculty-allocation/save",
    response_model=ApiResponse[DepartmentFacultyAllocationSaveResult],
)
async def department_faculty_allocation_save_route(
    payload: DepartmentFacultyAllocationSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[DepartmentFacultyAllocationSaveResult]:
    data = await save_department_faculty_allocation(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/departments/resource-management/page",
    response_model=ApiResponse[DepartmentResourceManagementPageRead],
)
async def department_resource_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    department_id: Annotated[str | None, Query()] = None,
    view: Annotated[str | None, Query()] = None,
) -> ApiResponse[DepartmentResourceManagementPageRead]:
    data = await get_department_resource_management_page(scope, department_id=department_id, view=view)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/departments/status-history/page",
    response_model=ApiResponse[DepartmentStatusHistoryPageRead],
)
async def department_status_history_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    since_year: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
    change_type_filter: Annotated[str | None, Query()] = None,
    selected_department_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[DepartmentStatusHistoryPageRead]:
    data = await get_department_status_history_page(
        scope,
        page=page,
        since_year=since_year,
        department_id=department_id,
        change_type_filter=change_type_filter,
        selected_department_id=selected_department_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get(
    "/departments/programme-course-mapping/page",
    response_model=ApiResponse[ProgrammeCourseMappingPageRead],
)
async def programme_course_mapping_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    department_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[ProgrammeCourseMappingPageRead]:
    data = await get_programme_course_mapping_page(scope, department_id=department_id)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/organization/hierarchy/page",
    response_model=ApiResponse[OrganizationalHierarchyPageRead],
)
async def organizational_hierarchy_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    selected_node_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[OrganizationalHierarchyPageRead]:
    data = await get_organizational_hierarchy_page(scope, selected_node_id=selected_node_id)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/departments/head-assignment/page",
    response_model=ApiResponse[DepartmentHeadAssignmentPageRead],
)
async def department_head_assignment_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    selected_department_id: Annotated[str | None, Query()] = None,
    faculty_user_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[DepartmentHeadAssignmentPageRead]:
    data = await get_department_head_assignment_page(
        scope,
        page=page,
        selected_department_id=selected_department_id,
        faculty_user_id=faculty_user_id,
    )
    return success_response(data, request_id=get_request_id())


@router.post(
    "/departments/head-assignment/submit",
    response_model=ApiResponse[DepartmentHeadAssignmentSaveResult],
)
async def department_head_assignment_submit_route(
    payload: DepartmentHeadAssignmentSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[DepartmentHeadAssignmentSaveResult]:
    data = await save_department_head_assignment(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get(
    "/departments/management-dashboard/page",
    response_model=ApiResponse[DepartmentManagementDashboardPageRead],
)
async def department_management_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
    school_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[DepartmentManagementDashboardPageRead]:
    data = await get_department_management_dashboard_page(
        scope,
        academic_year_label=academic_year_label,
        campus_id=campus_id,
        school_id=school_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/departments/{department_id}", response_model=ApiResponse[InstitutionDepartmentRead])
async def get_department_route(
    department_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionDepartmentRead]:
    data = await get_institution_department(scope, to_object_id(department_id, "department id"))
    return success_response(data, request_id=get_request_id())


@router.patch("/departments/{department_id}", response_model=ApiResponse[InstitutionDepartmentRead])
async def update_department_route(
    department_id: str,
    payload: InstitutionDepartmentUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionDepartmentRead]:
    data = await update_institution_department(scope, to_object_id(department_id, "department id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/departments/{department_id}/head", response_model=ApiResponse[InstitutionDepartmentRead])
async def assign_head_route(
    department_id: str,
    payload: DepartmentHeadAssign,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionDepartmentRead]:
    data = await assign_department_head(scope, to_object_id(department_id, "department id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/departments/{department_id}/transfer", response_model=ApiResponse[InstitutionDepartmentRead])
async def transfer_department_route(
    department_id: str,
    payload: DepartmentTransfer,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionDepartmentRead]:
    data = await transfer_department(scope, to_object_id(department_id, "department id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/departments/{department_id}/history", response_model=ApiResponse[list[DepartmentHistoryRead]])
async def department_history_route(
    department_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[DepartmentHistoryRead]]:
    data = await get_department_history(scope, to_object_id(department_id, "department id"))
    return success_response(data, request_id=get_request_id())


@router.post("/departments/{department_id}/staff/{staff_user_id}", response_model=ApiResponse[dict])
async def associate_staff_route(
    department_id: str,
    staff_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    data = await associate_department_staff(
        scope,
        to_object_id(department_id, "department id"),
        to_object_id(staff_user_id, "user id"),
    )
    return success_response(data, request_id=get_request_id())
