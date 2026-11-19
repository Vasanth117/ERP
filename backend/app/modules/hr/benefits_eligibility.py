"""Benefit program eligibility evaluation."""

from datetime import date

from beanie import PydanticObjectId

from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.hr.benefits_models import HrBenefitProgram, EmployeeBenefitEnrollment
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.enums import HrBenefitEnrollmentStatus, HrBenefitProgramStatus


_ELIGIBLE_STATUSES = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.NOTICE_PERIOD,
    }
)


async def evaluate_benefit_eligibility(
    *,
    program: HrBenefitProgram,
    employee: EmployeeRecord,
    profile: HrEmployeeProfile | None,
    as_of: date | None = None,
) -> tuple[bool, str | None]:
    today = as_of or date.today()
    if program.status != HrBenefitProgramStatus.ACTIVE:
        return False, "Benefit program is not active"
    if employee.employment_status not in _ELIGIBLE_STATUSES:
        return False, f"Employment status {employee.employment_status.value} is not eligible"
    category = profile.employee_category if profile else None
    if program.applicable_categories and category and category not in program.applicable_categories:
        return False, "Employee category not covered"
    if program.applicable_departments and employee.department_id:
        if str(employee.department_id) not in program.applicable_departments:
            return False, "Department not covered"
    join_raw = (employee.confidential_hr or {}).get("joining_date")
    if program.min_service_days > 0:
        if not join_raw:
            return False, "Joining date required for service-duration rule"
        join_date = date.fromisoformat(join_raw)
        service_days = (today - join_date).days
        if service_days < program.min_service_days:
            return False, f"Minimum service {program.min_service_days} days not met"
    if program.valid_from and today < program.valid_from:
        return False, "Benefit not yet valid"
    if program.valid_to and today > program.valid_to:
        return False, "Benefit validity expired"
    employment_type = (program.eligibility_rules or {}).get("employment_types")
    if employment_type:
        et = (employee.confidential_hr or {}).get("employment_type") or employee.employment_type
        if isinstance(employment_type, list) and et and et not in employment_type:
            return False, "Employment type not eligible"
    return True, None


async def has_active_enrollment(tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId, program_id: PydanticObjectId) -> bool:
    from beanie.odm.operators.find.comparison import Eq

    row = await EmployeeBenefitEnrollment.find_one(
        Eq(EmployeeBenefitEnrollment.tenant_id, tenant_id),
        Eq(EmployeeBenefitEnrollment.employee_user_id, employee_user_id),
        Eq(EmployeeBenefitEnrollment.benefit_program_id, program_id),
        Eq(EmployeeBenefitEnrollment.status, HrBenefitEnrollmentStatus.ACTIVE),
    )
    return row is not None