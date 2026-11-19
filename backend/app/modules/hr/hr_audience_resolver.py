"""Resolve HR notification / announcement audiences."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.hr.employee_profile_models import HrEmployeeProfile


_ACTIVE = frozenset(
    {
        FacultyEmploymentStatus.ACTIVE,
        FacultyEmploymentStatus.CONFIRMED,
        FacultyEmploymentStatus.PROBATION,
        FacultyEmploymentStatus.NOTICE_PERIOD,
    }
)


async def resolve_hr_audience(tenant_id: PydanticObjectId, audience: dict) -> list[PydanticObjectId]:
    """Audience spec keys: all_employees, department_ids, campus_ids, designations, categories, employee_user_ids."""
    if audience.get("all_employees"):
        rows = await EmployeeRecord.find(
            Eq(EmployeeRecord.tenant_id, tenant_id),
            In(EmployeeRecord.employment_status, list(_ACTIVE)),
        ).to_list()
        return [r.user_id for r in rows]

    user_ids: set[PydanticObjectId] = set()
    for raw in audience.get("employee_user_ids", []):
        user_ids.add(PydanticObjectId(str(raw)))

    employees = await EmployeeRecord.find(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        In(EmployeeRecord.employment_status, list(_ACTIVE)),
    ).to_list()
    dept_ids = {str(x) for x in audience.get("department_ids", [])}
    campus_ids = {str(x) for x in audience.get("campus_ids", [])}
    designations = set(audience.get("designations", []))
    categories = set(audience.get("employee_categories", []))

    profile_cache: dict[str, HrEmployeeProfile | None] = {}

    for emp in employees:
        if dept_ids and emp.department_id and str(emp.department_id) not in dept_ids:
            continue
        if campus_ids and emp.campus_id and str(emp.campus_id) not in campus_ids:
            continue
        if designations and emp.designation not in designations:
            continue
        if categories:
            key = str(emp.user_id)
            if key not in profile_cache:
                profile_cache[key] = await HrEmployeeProfile.find_one(
                    Eq(HrEmployeeProfile.tenant_id, tenant_id),
                    Eq(HrEmployeeProfile.user_id, emp.user_id),
                )
            profile = profile_cache[key]
            if profile is None or profile.employee_category not in categories:
                continue
        user_ids.add(emp.user_id)
    return list(user_ids)