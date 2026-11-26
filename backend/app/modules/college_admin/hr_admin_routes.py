"""College admin HR administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.hr_admin_schemas import (
    HrPolicyRead,
    HrPolicyUpsert,
    LeaveDecision,
    LeavePolicyUpsert,
    OffboardingCreate,
    OnboardingCreate,
    PayrollConfigRead,
    PayrollConfigUpsert,
    RecruitmentCreate,
)
from app.modules.college_admin.hr_dashboard_page_service import get_hr_dashboard_page
from app.modules.college_admin.hr_employee_management_page_service import get_hr_employee_management_page
from app.modules.college_admin.hr_employee_onboarding_page_service import get_hr_employee_onboarding_page
from app.modules.college_admin.hr_employee_attendance_page_service import get_hr_employee_attendance_page
from app.modules.college_admin.hr_leave_approval_page_service import get_hr_leave_approval_page
from app.modules.college_admin.hr_leave_management_page_service import get_hr_leave_management_page
from app.modules.college_admin.hr_benefits_performance_actions_service import college_admin_open_performance_cycle
from app.modules.college_admin.hr_employee_benefits_claims_page_service import get_hr_employee_benefits_claims_page
from app.modules.college_admin.hr_performance_management_page_service import get_hr_performance_management_page
from app.modules.college_admin.hr_reports_page_service import create_hr_report_schedule, get_hr_reports_page
from app.modules.college_admin.hr_settings_policies_page_service import (
    get_hr_settings_policies_page,
    save_hr_settings_policies_page,
)
from app.modules.college_admin.hr_payroll_college_actions_service import (
    college_admin_generate_salary_slips,
    college_admin_process_payroll,
    college_admin_publish_salary_slips,
    college_admin_validate_payroll,
)
from app.modules.college_admin.hr_payroll_processing_page_service import get_hr_payroll_processing_page
from app.modules.college_admin.hr_recruitment_management_page_service import get_hr_recruitment_management_page
from app.modules.college_admin.hr_salary_slip_management_page_service import get_hr_salary_slip_management_page
from app.modules.college_admin.hr_salary_structure_management_page_service import get_hr_salary_structure_management_page
from app.modules.college_admin.hr_admin_service import (
    complete_onboarding,
    create_recruitment,
    decide_leave,
    hr_report,
    list_pending_leave,
    payroll_status,
    publish_hr_policy,
    record_offboarding,
    start_onboarding,
    upsert_hr_policy,
    upsert_leave_policy,
    upsert_payroll_config,
    workforce_statistics,
)
from app.modules.college_admin.schemas import (
    EmployeeDirectoryPageRead,
    HrDashboardPageRead,
    HrEmployeeAttendancePageRead,
    HrEmployeeBenefitsClaimsPageRead,
    HrEmployeeOnboardingPageRead,
    HrPerformanceManagementPageRead,
    HrReportsPageRead,
    HrReportScheduleCreate,
    HrSettingsPoliciesPageRead,
    HrSettingsPoliciesSave,
    HrLeaveApprovalPageRead,
    HrLeaveManagementPageRead,
    HrPayrollProcessingPageRead,
    HrRecruitmentManagementPageRead,
    HrSalarySlipManagementPageRead,
    HrSalaryStructureManagementPageRead,
)

router = APIRouter()


@router.get("/dashboard/page", response_model=ApiResponse[HrDashboardPageRead])
async def hr_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
) -> ApiResponse[HrDashboardPageRead]:
    return success_response(
        await get_hr_dashboard_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/recruitment/management/page", response_model=ApiResponse[HrRecruitmentManagementPageRead])
async def hr_recruitment_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
) -> ApiResponse[HrRecruitmentManagementPageRead]:
    return success_response(
        await get_hr_recruitment_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/onboarding/management/page", response_model=ApiResponse[HrEmployeeOnboardingPageRead])
async def hr_employee_onboarding_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
) -> ApiResponse[HrEmployeeOnboardingPageRead]:
    return success_response(
        await get_hr_employee_onboarding_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/attendance/page", response_model=ApiResponse[HrEmployeeAttendancePageRead])
async def hr_employee_attendance_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
    department_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[HrEmployeeAttendancePageRead]:
    return success_response(
        await get_hr_employee_attendance_page(scope, page=page, page_size=page_size, department_id=department_id),
        request_id=get_request_id(),
    )


@router.get("/leave/management/page", response_model=ApiResponse[HrLeaveManagementPageRead])
async def hr_leave_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
) -> ApiResponse[HrLeaveManagementPageRead]:
    return success_response(
        await get_hr_leave_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/leave/approval/page", response_model=ApiResponse[HrLeaveApprovalPageRead])
async def hr_leave_approval_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    leave_request_id: Annotated[str | None, Query(alias="id")] = None,
) -> ApiResponse[HrLeaveApprovalPageRead]:
    return success_response(
        await get_hr_leave_approval_page(scope, leave_request_id=leave_request_id),
        request_id=get_request_id(),
    )


@router.get("/payroll/salary-structure/page", response_model=ApiResponse[HrSalaryStructureManagementPageRead])
async def hr_salary_structure_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
) -> ApiResponse[HrSalaryStructureManagementPageRead]:
    return success_response(
        await get_hr_salary_structure_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/payroll/processing/page", response_model=ApiResponse[HrPayrollProcessingPageRead])
async def hr_payroll_processing_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 5,
) -> ApiResponse[HrPayrollProcessingPageRead]:
    return success_response(
        await get_hr_payroll_processing_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.post("/payroll/processing/validate", response_model=ApiResponse[dict])
async def hr_payroll_validate_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    payroll_run_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(
        await college_admin_validate_payroll(scope, payroll_run_id=payroll_run_id),
        request_id=get_request_id(),
    )


@router.post("/payroll/processing/process", response_model=ApiResponse[dict])
async def hr_payroll_process_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    payroll_run_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(
        await college_admin_process_payroll(scope, payroll_run_id=payroll_run_id),
        request_id=get_request_id(),
    )


@router.get("/payroll/slips/page", response_model=ApiResponse[HrSalarySlipManagementPageRead])
async def hr_salary_slip_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[HrSalarySlipManagementPageRead]:
    return success_response(
        await get_hr_salary_slip_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.post("/payroll/slips/generate", response_model=ApiResponse[dict])
async def hr_salary_slips_generate_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    payroll_run_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(
        await college_admin_generate_salary_slips(scope, payroll_run_id=payroll_run_id),
        request_id=get_request_id(),
    )


@router.post("/payroll/slips/publish", response_model=ApiResponse[dict])
async def hr_salary_slips_publish_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    payroll_run_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(
        await college_admin_publish_salary_slips(scope, payroll_run_id=payroll_run_id),
        request_id=get_request_id(),
    )


@router.get("/benefits/claims/page", response_model=ApiResponse[HrEmployeeBenefitsClaimsPageRead])
async def hr_employee_benefits_claims_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
) -> ApiResponse[HrEmployeeBenefitsClaimsPageRead]:
    return success_response(
        await get_hr_employee_benefits_claims_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/performance/management/page", response_model=ApiResponse[HrPerformanceManagementPageRead])
async def hr_performance_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HrPerformanceManagementPageRead]:
    return success_response(
        await get_hr_performance_management_page(scope),
        request_id=get_request_id(),
    )


@router.get("/reports/page", response_model=ApiResponse[HrReportsPageRead])
async def hr_reports_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
) -> ApiResponse[HrReportsPageRead]:
    return success_response(
        await get_hr_reports_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.post("/reports/schedules", response_model=ApiResponse[HrReportsPageRead], status_code=status.HTTP_201_CREATED)
async def hr_create_report_schedule_route(
    payload: HrReportScheduleCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HrReportsPageRead]:
    return success_response(
        await create_hr_report_schedule(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/settings/policies/page", response_model=ApiResponse[HrSettingsPoliciesPageRead])
async def hr_settings_policies_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HrSettingsPoliciesPageRead]:
    return success_response(await get_hr_settings_policies_page(scope), request_id=get_request_id())


@router.put("/settings/policies/page", response_model=ApiResponse[HrSettingsPoliciesPageRead])
async def hr_settings_policies_save_route(
    payload: HrSettingsPoliciesSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HrSettingsPoliciesPageRead]:
    return success_response(await save_hr_settings_policies_page(scope, payload), request_id=get_request_id())


@router.post("/performance/cycles/open", response_model=ApiResponse[dict])
async def hr_open_performance_cycle_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    cycle_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(
        await college_admin_open_performance_cycle(scope, cycle_id=cycle_id),
        request_id=get_request_id(),
    )


@router.get("/employees/management/page", response_model=ApiResponse[EmployeeDirectoryPageRead])
async def hr_employee_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    search: Annotated[str | None, Query(max_length=200)] = None,
    department_id: Annotated[str | None, Query()] = None,
    type_filter: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query()] = None,
) -> ApiResponse[EmployeeDirectoryPageRead]:
    return success_response(
        await get_hr_employee_management_page(
            scope,
            page=page,
            search=search,
            department_id=department_id,
            type_filter=type_filter,
            status_filter=status_filter,
        ),
        request_id=get_request_id(),
    )


@router.put("/policies", response_model=ApiResponse[HrPolicyRead])
async def hr_policy_route(
    payload: HrPolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HrPolicyRead]:
    return success_response(await upsert_hr_policy(scope, payload), request_id=get_request_id())


@router.post("/policies/{policy_code}/publish", response_model=ApiResponse[HrPolicyRead])
async def publish_policy_route(
    policy_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HrPolicyRead]:
    return success_response(await publish_hr_policy(scope, policy_code), request_id=get_request_id())


@router.post("/recruitment", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def recruitment_route(
    payload: RecruitmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_recruitment(scope, payload), request_id=get_request_id())


@router.post("/onboarding", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def onboarding_route(
    payload: OnboardingCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await start_onboarding(scope, payload), request_id=get_request_id())


@router.post("/onboarding/{user_id}/complete", response_model=ApiResponse[dict])
async def complete_onboarding_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await complete_onboarding(scope, user_id), request_id=get_request_id())


@router.post("/offboarding", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def offboarding_route(
    payload: OffboardingCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await record_offboarding(scope, payload), request_id=get_request_id())


@router.put("/leave-policies", response_model=ApiResponse[dict])
async def leave_policy_route(
    payload: LeavePolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_leave_policy(scope, payload), request_id=get_request_id())


@router.get("/leave/pending", response_model=ApiResponse[Page[dict]])
async def pending_leave_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await list_pending_leave(scope, pagination), request_id=get_request_id())


@router.post("/leave/decide", response_model=ApiResponse[dict])
async def leave_decide_route(
    payload: LeaveDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await decide_leave(scope, payload), request_id=get_request_id())


@router.put("/payroll/configuration", response_model=ApiResponse[PayrollConfigRead])
async def payroll_config_route(
    payload: PayrollConfigUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[PayrollConfigRead]:
    return success_response(await upsert_payroll_config(scope, payload), request_id=get_request_id())


@router.get("/payroll/status", response_model=ApiResponse[dict])
async def payroll_status_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await payroll_status(scope), request_id=get_request_id())


@router.get("/statistics", response_model=ApiResponse[dict])
async def workforce_stats_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await workforce_statistics(scope), request_id=get_request_id())


@router.get("/reports/summary", response_model=ApiResponse[dict])
async def hr_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await hr_report(scope), request_id=get_request_id())
