"""College admin attendance administration routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.schemas import (
    AttendanceApprovalPageRead,
    AttendanceConfigurationPageRead,
    AttendanceConfigurationSave,
    AttendanceInstitutionalPolicySave,
    AttendanceCorrectionRequestsPageRead,
    AttendanceDashboardPageRead,
    AttendanceReportCreate,
    AttendanceReportsPageRead,
    AttendanceRulesPoliciesPageRead,
    AttendanceMonitoringPageRead,
    DepartmentWiseAttendancePageRead,
    FacultyAttendanceOverviewPageRead,
    StudentAttendanceOverviewPageRead,
    SubjectWiseAttendancePageRead,
    AttendanceSectionSubNavRead,
)
from app.modules.college_admin.attendance_configuration_page_service import (
    get_attendance_configuration_page,
    get_attendance_rules_policies_page,
    save_attendance_configuration,
    save_institutional_policy_row,
)
from app.modules.college_admin.attendance_reports_page_service import (
    create_attendance_report,
    get_attendance_reports_page,
)
from app.modules.college_admin.attendance_corrections_page_service import (
    get_attendance_approval_page,
    get_attendance_correction_requests_page,
)
from app.modules.college_admin.attendance_admin_schemas import (
    AttendancePolicyRead,
    AttendancePolicyUpsert,
    AttendanceReportGenerate,
    ComplianceSnapshotRead,
    CorrectionDecision,
    CorrectionRequestRead,
    DepartmentAttendanceSummary,
)
from app.modules.college_admin.attendance_dashboard_page_service import get_attendance_dashboard_page
from app.modules.college_admin.department_wise_attendance_page_service import (
    get_department_wise_attendance_page,
)
from app.modules.college_admin.attendance_monitoring_page_service import (
    get_attendance_monitoring_page,
    notify_faculty_for_missing_attendance,
)
from app.modules.college_admin.faculty_attendance_overview_page_service import (
    get_faculty_attendance_overview_page,
)
from app.modules.college_admin.student_attendance_overview_page_service import (
    get_student_attendance_overview_page,
)
from app.modules.college_admin.subject_wise_attendance_page_service import (
    get_subject_wise_attendance_page,
)
from app.modules.college_admin.attendance_admin_service import (
    attendance_history,
    attendance_shortages,
    decide_correction,
    department_summaries,
    generate_compliance_snapshot,
    list_attendance_policies,
    list_correction_requests,
    missing_submissions,
    refresh_submission_monitoring,
    upsert_attendance_policy,
)
from app.modules.college_admin.attendance_section_sub_nav_service import get_attendance_section_sub_nav
from app.modules.college_admin.deps import college_admin_user

router = APIRouter()


@router.get("/navigation/section-sub-nav", response_model=ApiResponse[AttendanceSectionSubNavRead])
async def attendance_section_sub_nav_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    path: str = "",
) -> ApiResponse[AttendanceSectionSubNavRead]:
    return success_response(await get_attendance_section_sub_nav(scope, path=path), request_id=get_request_id())


@router.get("/configuration/page", response_model=ApiResponse[AttendanceConfigurationPageRead])
async def attendance_configuration_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AttendanceConfigurationPageRead]:
    return success_response(await get_attendance_configuration_page(scope), request_id=get_request_id())


@router.post("/configuration/save", response_model=ApiResponse[AttendanceConfigurationPageRead])
async def attendance_configuration_save_route(
    payload: AttendanceConfigurationSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AttendanceConfigurationPageRead]:
    return success_response(await save_attendance_configuration(scope, payload), request_id=get_request_id())


@router.get("/rules-policies/page", response_model=ApiResponse[AttendanceRulesPoliciesPageRead])
async def attendance_rules_policies_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    page_size: int = 4,
) -> ApiResponse[AttendanceRulesPoliciesPageRead]:
    return success_response(
        await get_attendance_rules_policies_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.post("/rules-policies/save", response_model=ApiResponse[AttendanceRulesPoliciesPageRead])
async def attendance_rules_policies_save_route(
    payload: AttendanceInstitutionalPolicySave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    page_size: int = 4,
) -> ApiResponse[AttendanceRulesPoliciesPageRead]:
    return success_response(
        await save_institutional_policy_row(scope, payload, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/monitoring/page", response_model=ApiResponse[AttendanceMonitoringPageRead])
async def attendance_monitoring_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    page_size: int = 10,
) -> ApiResponse[AttendanceMonitoringPageRead]:
    return success_response(
        await get_attendance_monitoring_page(scope, page_num=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.post("/monitoring/notify-faculty", response_model=ApiResponse[dict])
async def attendance_monitoring_notify_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await notify_faculty_for_missing_attendance(scope), request_id=get_request_id())


@router.get(
    "/faculty-attendance/page",
    response_model=ApiResponse[FacultyAttendanceOverviewPageRead],
)
async def faculty_attendance_overview_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    department_id: str | None = None,
    page: int = 1,
    page_size: int = 4,
) -> ApiResponse[FacultyAttendanceOverviewPageRead]:
    return success_response(
        await get_faculty_attendance_overview_page(
            scope,
            department_id=department_id or None,
            page=page,
            page_size=page_size,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/department-wise/page",
    response_model=ApiResponse[DepartmentWiseAttendancePageRead],
)
async def department_wise_attendance_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    term_key: str | None = None,
) -> ApiResponse[DepartmentWiseAttendancePageRead]:
    return success_response(
        await get_department_wise_attendance_page(scope, term_key=term_key),
        request_id=get_request_id(),
    )


@router.get(
    "/subject-wise/page",
    response_model=ApiResponse[SubjectWiseAttendancePageRead],
)
async def subject_wise_attendance_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    term_key: str | None = None,
    scope_key: str | None = None,
) -> ApiResponse[SubjectWiseAttendancePageRead]:
    return success_response(
        await get_subject_wise_attendance_page(
            scope,
            term_key=term_key,
            scope_key=scope_key or None,
        ),
        request_id=get_request_id(),
    )


@router.get(
    "/student-attendance/page",
    response_model=ApiResponse[StudentAttendanceOverviewPageRead],
)
async def student_attendance_overview_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    term_key: str | None = None,
    programme_code: str | None = None,
) -> ApiResponse[StudentAttendanceOverviewPageRead]:
    return success_response(
        await get_student_attendance_overview_page(
            scope,
            term_key=term_key,
            programme_code=programme_code or None,
        ),
        request_id=get_request_id(),
    )


@router.get("/dashboard/page", response_model=ApiResponse[AttendanceDashboardPageRead])
async def attendance_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    term_key: str | None = None,
    department_id: str | None = None,
) -> ApiResponse[AttendanceDashboardPageRead]:
    return success_response(
        await get_attendance_dashboard_page(scope, term_key=term_key, department_id=department_id or None),
        request_id=get_request_id(),
    )


@router.put("/policies", response_model=ApiResponse[AttendancePolicyRead])
async def upsert_policy_route(
    payload: AttendancePolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AttendancePolicyRead]:
    return success_response(await upsert_attendance_policy(scope, payload), request_id=get_request_id())


@router.get("/policies", response_model=ApiResponse[list[AttendancePolicyRead]])
async def list_policies_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[AttendancePolicyRead]]:
    return success_response(await list_attendance_policies(scope), request_id=get_request_id())


@router.get("/summaries/departments", response_model=ApiResponse[list[DepartmentAttendanceSummary]])
async def department_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[DepartmentAttendanceSummary]]:
    return success_response(await department_summaries(scope), request_id=get_request_id())


@router.post("/monitoring/refresh", response_model=ApiResponse[dict])
async def refresh_monitoring_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await refresh_submission_monitoring(scope), request_id=get_request_id())


@router.get("/submissions/missing", response_model=ApiResponse[Page[dict]])
async def missing_submissions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await missing_submissions(scope, pagination), request_id=get_request_id())


@router.get("/corrections/requests/page", response_model=ApiResponse[AttendanceCorrectionRequestsPageRead])
async def attendance_correction_requests_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    page_size: int = 10,
) -> ApiResponse[AttendanceCorrectionRequestsPageRead]:
    return success_response(
        await get_attendance_correction_requests_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/corrections/approval/page", response_model=ApiResponse[AttendanceApprovalPageRead])
async def attendance_approval_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    request_id: str | None = None,
) -> ApiResponse[AttendanceApprovalPageRead]:
    return success_response(
        await get_attendance_approval_page(scope, request_id=request_id or None),
        request_id=get_request_id(),
    )


@router.get("/corrections", response_model=ApiResponse[Page[CorrectionRequestRead]])
async def list_corrections_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[CorrectionRequestRead]]:
    return success_response(await list_correction_requests(scope, pagination), request_id=get_request_id())


@router.post("/corrections/decide", response_model=ApiResponse[dict])
async def decide_correction_route(
    payload: CorrectionDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await decide_correction(scope, payload), request_id=get_request_id())


@router.get("/shortages", response_model=ApiResponse[list[dict]])
async def shortages_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    course_code: Annotated[str | None, Query()] = None,
    section: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[dict]]:
    return success_response(await attendance_shortages(scope, course_code=course_code, section=section), request_id=get_request_id())


@router.get("/history", response_model=ApiResponse[Page[dict]])
async def attendance_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    faculty_user_id: Annotated[str | None, Query()] = None,
    session_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[Page[dict]]:
    return success_response(
        await attendance_history(scope, faculty_user_id=faculty_user_id, session_date=session_date, pagination=pagination),
        request_id=get_request_id(),
    )


@router.get("/reports/page", response_model=ApiResponse[AttendanceReportsPageRead])
async def attendance_reports_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    page_size: int = 4,
) -> ApiResponse[AttendanceReportsPageRead]:
    return success_response(
        await get_attendance_reports_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.post("/reports/create", response_model=ApiResponse[AttendanceReportsPageRead])
async def attendance_reports_create_route(
    payload: AttendanceReportCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AttendanceReportsPageRead]:
    return success_response(await create_attendance_report(scope, payload), request_id=get_request_id())


@router.post("/reports/compliance", response_model=ApiResponse[ComplianceSnapshotRead], status_code=status.HTTP_201_CREATED)
async def compliance_report_route(
    payload: AttendanceReportGenerate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ComplianceSnapshotRead]:
    return success_response(await generate_compliance_snapshot(scope, payload), request_id=get_request_id())
