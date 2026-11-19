"""Built-in HR role profile catalog (maps to platform permissions; not a second RBAC engine)."""

from app.authorization.permissions import Permission
from app.modules.hr.hr_audit_schemas import RoleProfileRead

_BUILTIN: list[RoleProfileRead] = [
    RoleProfileRead(
        role_profile_code="hr_administrator",
        title="HR Administrator",
        permission_codes=[
            Permission.HR_ADMIN_MANAGE.value,
            Permission.HR_SETTINGS_MANAGE.value,
            Permission.HR_ACCESS_MANAGE.value,
        ],
        platform_note="Uses institution Role.HR_STAFF plus overlays",
    ),
    RoleProfileRead(
        role_profile_code="hr_manager",
        title="HR Manager",
        permission_codes=[Permission.HR_ADMIN_READ.value, Permission.HR_EMPLOYEE_MANAGE.value, Permission.HR_SETTINGS_READ.value],
    ),
    RoleProfileRead(
        role_profile_code="hr_executive",
        title="HR Executive",
        permission_codes=[Permission.HR_EMPLOYEE_READ.value, Permission.HR_EMPLOYEE_MANAGE.value],
    ),
    RoleProfileRead(
        role_profile_code="recruitment_officer",
        title="Recruitment Officer",
        permission_codes=[Permission.HR_RECRUITMENT_READ.value, Permission.HR_RECRUITMENT_MANAGE.value],
    ),
    RoleProfileRead(
        role_profile_code="payroll_officer",
        title="Payroll Officer",
        permission_codes=[Permission.HR_PAYROLL_READ.value, Permission.HR_PAYROLL_PREPARE.value],
    ),
    RoleProfileRead(
        role_profile_code="leave_administrator",
        title="Leave Administrator",
        permission_codes=[Permission.HR_LEAVE_READ.value, Permission.HR_LEAVE_MANAGE.value],
    ),
    RoleProfileRead(
        role_profile_code="attendance_administrator",
        title="Attendance Administrator",
        permission_codes=[Permission.HR_ATTENDANCE_READ.value, Permission.HR_ATTENDANCE_MANAGE.value],
    ),
    RoleProfileRead(
        role_profile_code="hr_document_verifier",
        title="HR Document Verifier",
        permission_codes=[Permission.HR_DOCUMENT_VERIFY.value],
    ),
    RoleProfileRead(
        role_profile_code="training_coordinator",
        title="Training Coordinator",
        permission_codes=[Permission.HR_TRAINING_READ.value, Permission.HR_TRAINING_MANAGE.value],
    ),
    RoleProfileRead(
        role_profile_code="benefits_administrator",
        title="Benefits Administrator",
        permission_codes=[Permission.HR_BENEFITS_READ.value, Permission.HR_BENEFITS_MANAGE.value],
    ),
    RoleProfileRead(
        role_profile_code="hr_auditor",
        title="HR Auditor",
        permission_codes=[Permission.HR_AUDIT_READ.value, Permission.HR_AUDIT_EXPORT.value],
    ),
    RoleProfileRead(
        role_profile_code="hr_viewer",
        title="Read-Only HR Viewer",
        permission_codes=[Permission.HR_DASHBOARD_READ.value, Permission.HR_EMPLOYEE_READ.value, Permission.HR_AUDIT_READ.value],
    ),
]


def builtin_role_profiles() -> list[RoleProfileRead]:
    return list(_BUILTIN)