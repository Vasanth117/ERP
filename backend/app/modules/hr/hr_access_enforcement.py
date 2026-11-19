"""Enforce HR access-scope assignments (department / employee-set overlays)."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.enums import HrAccessScopeKind
from app.modules.hr.hr_audit_models import HrAccessScopeAssignment


async def assert_hr_employee_in_scope(scope: AccessScope, tenant_id: PydanticObjectId, employee_user_id: PydanticObjectId) -> None:
    """When an assignment exists for the HR user, restrict visibility to configured scope."""
    if Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    assignment = await HrAccessScopeAssignment.find_one(
        Eq(HrAccessScopeAssignment.tenant_id, tenant_id),
        Eq(HrAccessScopeAssignment.user_id, scope.user_id),
    )
    if assignment is None:
        return
    if assignment.scope_kind == HrAccessScopeKind.INSTITUTION:
        return
    if assignment.scope_kind == HrAccessScopeKind.EMPLOYEE_SET:
        if employee_user_id not in set(assignment.employee_user_ids):
            raise AppError(code="FORBIDDEN", message="Employee outside assigned HR scope", status_code=403)
        return
    emp = await EmployeeRecord.find_one(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.user_id, employee_user_id),
    )
    if emp is None:
        raise AppError(code="NOT_FOUND", message="Employee not found", status_code=404)
    if assignment.scope_kind == HrAccessScopeKind.DEPARTMENT:
        if assignment.department_id and emp.department_id != assignment.department_id:
            raise AppError(code="FORBIDDEN", message="Employee outside assigned department scope", status_code=403)
    if assignment.scope_kind == HrAccessScopeKind.CAMPUS:
        if assignment.campus_id and emp.campus_id != assignment.campus_id:
            raise AppError(code="FORBIDDEN", message="Employee outside assigned campus scope", status_code=403)