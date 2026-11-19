"""Synchronize HR current assignment from employee records."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.structure_models import HrDesignation, HrEmployeeCurrentAssignment


async def institution_dept_for_central(tenant_id: PydanticObjectId, central_department_id: PydanticObjectId | None) -> InstitutionDepartment | None:
    if central_department_id is None:
        return None
    return await InstitutionDepartment.find_one(
        Eq(InstitutionDepartment.tenant_id, tenant_id),
        Eq(InstitutionDepartment.central_department_id, central_department_id),
    )


async def designation_for_code(tenant_id: PydanticObjectId, code: str | None) -> HrDesignation | None:
    if not code:
        return None
    return await HrDesignation.find_one(Eq(HrDesignation.tenant_id, tenant_id), Eq(HrDesignation.designation_code, code))


async def ensure_current_assignment(
    tenant_id: PydanticObjectId,
    employee: EmployeeRecord,
    profile: HrEmployeeProfile | None,
    *,
    actor_id: PydanticObjectId | None = None,
) -> HrEmployeeCurrentAssignment:
    inst_dept = await institution_dept_for_central(tenant_id, employee.department_id)
    designation = None
    if employee.designation:
        designation = await designation_for_code(tenant_id, employee.designation)
    row = await HrEmployeeCurrentAssignment.find_one(
        Eq(HrEmployeeCurrentAssignment.tenant_id, tenant_id),
        Eq(HrEmployeeCurrentAssignment.employee_user_id, employee.user_id),
    )
    if row is None:
        row = HrEmployeeCurrentAssignment(
            tenant_id=tenant_id,
            employee_user_id=employee.user_id,
            employee_record_id=employee.id,
            effective_from=employee.joining_date or date.today(),
        )
    row.central_department_id = employee.department_id
    row.institution_department_id = inst_dept.id if inst_dept else None
    row.designation_id = designation.id if designation else None
    row.designation_code = employee.designation
    row.employment_type_code = employee.employment_type
    row.employment_category_code = profile.employee_category if profile else None
    row.campus_id = employee.campus_id
    row.organization_unit_id = inst_dept.organization_unit_id if inst_dept else None
    if profile and profile.reporting_manager_user_id:
        row.reporting_manager_user_id = profile.reporting_manager_user_id
    row.updated_by = actor_id
    row.updated_at = utcnow()
    if row.id is None:
        await row.insert()
    else:
        await row.save()
    return row