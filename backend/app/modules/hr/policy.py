"""HR staff portal authorization."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.core.exceptions import AppError


def _has_hr_dashboard_read(scope: AccessScope) -> bool:
    return (
        Permission.HR_DASHBOARD_READ in scope.effective_permissions
        or Permission.HR_ADMIN_READ in scope.effective_permissions
    )


def _has_hr_portal_access(scope: AccessScope) -> bool:
    return (
        _has_hr_dashboard_read(scope)
        or Permission.HR_EMPLOYEE_READ in scope.effective_permissions
        or Permission.HR_EMPLOYEE_MANAGE in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
        or Permission.HR_SELF_ACCESS in scope.effective_permissions
    )


def authorize_hr_dashboard(scope: AccessScope) -> None:
    if _has_hr_dashboard_read(scope):
        return
    authorize(scope, Permission.HR_DASHBOARD_READ)


def authorize_hr_employee_read(scope: AccessScope) -> None:
    if Permission.HR_EMPLOYEE_READ in scope.effective_permissions or Permission.HR_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_EMPLOYEE_READ)


def authorize_hr_employee_manage(scope: AccessScope) -> None:
    if Permission.HR_EMPLOYEE_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_EMPLOYEE_MANAGE)


def authorize_hr_portal(scope: AccessScope) -> None:
    if _has_hr_portal_access(scope):
        return
    authorize(scope, Permission.HR_SELF_ACCESS)


def require_hr_tenant_scope(scope: AccessScope) -> PydanticObjectId:
    authorize_hr_portal(scope)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context is required", status_code=403)
    return scope.tenant_id


def authorize_hr_org_read(scope: AccessScope) -> None:
    if Permission.HR_ORG_READ in scope.effective_permissions or Permission.INSTITUTION_ORG_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_ORG_READ)


def authorize_hr_org_manage(scope: AccessScope) -> None:
    if Permission.HR_ORG_MANAGE in scope.effective_permissions or Permission.INSTITUTION_ORG_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_ORG_MANAGE)


def authorize_hr_assignment_manage(scope: AccessScope) -> None:
    if Permission.HR_ASSIGNMENT_MANAGE in scope.effective_permissions or Permission.HR_EMPLOYEE_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_ASSIGNMENT_MANAGE)


def authorize_hr_transfer_manage(scope: AccessScope) -> None:
    if Permission.HR_TRANSFER_MANAGE in scope.effective_permissions or Permission.HR_ASSIGNMENT_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_TRANSFER_MANAGE)


def authorize_hr_document_read(scope: AccessScope) -> None:
    if Permission.HR_DOCUMENT_READ in scope.effective_permissions or Permission.HR_EMPLOYEE_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_DOCUMENT_READ)


def authorize_hr_document_manage(scope: AccessScope) -> None:
    if Permission.HR_DOCUMENT_MANAGE in scope.effective_permissions or Permission.HR_EMPLOYEE_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_DOCUMENT_MANAGE)


def authorize_hr_document_verify(scope: AccessScope) -> None:
    if Permission.HR_DOCUMENT_VERIFY in scope.effective_permissions or Permission.HR_EMPLOYEE_VERIFY in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_DOCUMENT_VERIFY)


def authorize_hr_recruitment_read(scope: AccessScope) -> None:
    if Permission.HR_RECRUITMENT_READ in scope.effective_permissions or Permission.HR_RECRUITMENT_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_RECRUITMENT_READ)


def authorize_hr_recruitment_manage(scope: AccessScope) -> None:
    if Permission.HR_RECRUITMENT_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_RECRUITMENT_MANAGE)


def authorize_hr_recruitment_approve(scope: AccessScope) -> None:
    if Permission.HR_RECRUITMENT_APPROVE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_RECRUITMENT_APPROVE)


def authorize_hr_recruitment_manage_or_channel(scope: AccessScope) -> None:
    if (
        Permission.HR_RECRUITMENT_MANAGE in scope.effective_permissions
        or Permission.HR_RECRUITMENT_CHANNEL_APPLY in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_RECRUITMENT_MANAGE)


def authorize_hr_recruitment_channel_apply(scope: AccessScope) -> None:
    if (
        Permission.HR_RECRUITMENT_CHANNEL_APPLY in scope.effective_permissions
        or Permission.HR_RECRUITMENT_MANAGE in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_RECRUITMENT_CHANNEL_APPLY)


def authorize_hr_onboarding_read(scope: AccessScope) -> None:
    if Permission.HR_ONBOARDING_READ in scope.effective_permissions or Permission.HR_ONBOARDING_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_ONBOARDING_READ)


def authorize_hr_onboarding_manage(scope: AccessScope) -> None:
    if Permission.HR_ONBOARDING_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_ONBOARDING_MANAGE)


def authorize_hr_onboarding_complete(scope: AccessScope) -> None:
    if Permission.HR_ONBOARDING_COMPLETE in scope.effective_permissions or Permission.HR_ONBOARDING_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_ONBOARDING_COMPLETE)


def authorize_hr_employment_change_read(scope: AccessScope) -> None:
    if Permission.HR_EMPLOYMENT_CHANGE_READ in scope.effective_permissions or Permission.HR_EMPLOYMENT_CHANGE_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_EMPLOYMENT_CHANGE_READ)


def authorize_hr_employment_change_manage(scope: AccessScope) -> None:
    if Permission.HR_EMPLOYMENT_CHANGE_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_EMPLOYMENT_CHANGE_MANAGE)


def authorize_hr_offboarding_read(scope: AccessScope) -> None:
    if Permission.HR_OFFBOARDING_READ in scope.effective_permissions or Permission.HR_OFFBOARDING_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_OFFBOARDING_READ)


def authorize_hr_offboarding_manage(scope: AccessScope) -> None:
    if Permission.HR_OFFBOARDING_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_OFFBOARDING_MANAGE)


def authorize_hr_leave_read(scope: AccessScope) -> None:
    if (
        Permission.HR_LEAVE_READ in scope.effective_permissions
        or Permission.HR_LEAVE_MANAGE in scope.effective_permissions
        or Permission.HR_LEAVE_REVIEW in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_LEAVE_READ)


def authorize_hr_leave_manage(scope: AccessScope) -> None:
    if Permission.HR_LEAVE_MANAGE in scope.effective_permissions or Permission.HR_LEAVE_REVIEW in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_LEAVE_MANAGE)


def authorize_hr_attendance_read(scope: AccessScope) -> None:
    if Permission.HR_ATTENDANCE_READ in scope.effective_permissions or Permission.HR_ATTENDANCE_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_ATTENDANCE_READ)


def authorize_hr_attendance_manage(scope: AccessScope) -> None:
    if Permission.HR_ATTENDANCE_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_ATTENDANCE_MANAGE)


def authorize_hr_salary_read(scope: AccessScope) -> None:
    if Permission.HR_SALARY_READ in scope.effective_permissions or Permission.HR_SALARY_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_SALARY_READ)


def authorize_hr_salary_manage(scope: AccessScope) -> None:
    if Permission.HR_SALARY_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_SALARY_MANAGE)


def authorize_hr_payroll_read(scope: AccessScope) -> None:
    if (
        Permission.HR_PAYROLL_READ in scope.effective_permissions
        or Permission.HR_PAYROLL_PREPARE in scope.effective_permissions
        or Permission.HR_PAYROLL_APPROVE in scope.effective_permissions
        or Permission.HR_PAYROLL_PAY in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_PAYROLL_READ)


def authorize_hr_payroll_prepare(scope: AccessScope) -> None:
    if Permission.HR_PAYROLL_PREPARE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_PAYROLL_PREPARE)


def authorize_hr_payroll_approve(scope: AccessScope) -> None:
    if Permission.HR_PAYROLL_APPROVE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_PAYROLL_APPROVE)


def authorize_hr_payroll_pay(scope: AccessScope) -> None:
    if Permission.HR_PAYROLL_PAY in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_PAYROLL_PAY)


def authorize_hr_payslip_read(scope: AccessScope) -> None:
    if Permission.HR_PAYSLIP_READ in scope.effective_permissions or Permission.HR_PAYSLIP_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_PAYSLIP_READ)


def authorize_hr_payslip_manage(scope: AccessScope) -> None:
    if Permission.HR_PAYSLIP_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_PAYSLIP_MANAGE)


def authorize_employee_self_service(scope: AccessScope) -> None:
    if Permission.HR_SELF_ACCESS in scope.effective_permissions:
        return
    if Permission.FACULTY_SELF_SERVICE_READ in scope.effective_permissions:
        return
    if Permission.FACULTY_SELF_SERVICE_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_SELF_ACCESS)


def require_employee_tenant_scope(scope: AccessScope) -> PydanticObjectId:
    authorize_employee_self_service(scope)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context is required", status_code=403)
    return scope.tenant_id


def authorize_hr_statutory_read(scope: AccessScope) -> None:
    if (
        Permission.HR_STATUTORY_READ in scope.effective_permissions
        or Permission.HR_STATUTORY_MANAGE in scope.effective_permissions
        or Permission.HR_TAX_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_STATUTORY_READ)


def authorize_hr_statutory_manage(scope: AccessScope) -> None:
    if Permission.HR_STATUTORY_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_STATUTORY_MANAGE)


def authorize_hr_tax_manage(scope: AccessScope) -> None:
    if Permission.HR_TAX_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_TAX_MANAGE)


def authorize_hr_tax_review(scope: AccessScope) -> None:
    if (
        Permission.HR_TAX_REVIEW in scope.effective_permissions
        or Permission.HR_TAX_MANAGE in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_TAX_REVIEW)


def authorize_hr_benefits_read(scope: AccessScope) -> None:
    if (
        Permission.HR_BENEFITS_READ in scope.effective_permissions
        or Permission.HR_BENEFITS_MANAGE in scope.effective_permissions
        or Permission.HR_BENEFITS_APPROVE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_BENEFITS_READ)


def authorize_hr_benefits_manage(scope: AccessScope) -> None:
    if Permission.HR_BENEFITS_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_BENEFITS_MANAGE)


def authorize_hr_benefits_approve(scope: AccessScope) -> None:
    if (
        Permission.HR_BENEFITS_APPROVE in scope.effective_permissions
        or Permission.HR_BENEFITS_MANAGE in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_BENEFITS_APPROVE)


def authorize_hr_benefits_pay(scope: AccessScope) -> None:
    if (
        Permission.HR_BENEFITS_PAY in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_BENEFITS_PAY)


def authorize_hr_performance_read(scope: AccessScope) -> None:
    if (
        Permission.HR_PERFORMANCE_READ in scope.effective_permissions
        or Permission.HR_PERFORMANCE_MANAGE in scope.effective_permissions
        or Permission.HR_PERFORMANCE_REVIEW in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_PERFORMANCE_READ)


def authorize_hr_performance_manage(scope: AccessScope) -> None:
    if Permission.HR_PERFORMANCE_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_PERFORMANCE_MANAGE)


def authorize_hr_performance_review(scope: AccessScope) -> None:
    if (
        Permission.HR_PERFORMANCE_REVIEW in scope.effective_permissions
        or Permission.HR_PERFORMANCE_MANAGE in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_PERFORMANCE_REVIEW)


def authorize_hr_training_read(scope: AccessScope) -> None:
    if Permission.HR_TRAINING_READ in scope.effective_permissions or Permission.HR_TRAINING_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_TRAINING_READ)


def authorize_hr_training_manage(scope: AccessScope) -> None:
    if Permission.HR_TRAINING_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_TRAINING_MANAGE)


def authorize_hr_notify_read(scope: AccessScope) -> None:
    if Permission.HR_NOTIFY_READ in scope.effective_permissions or Permission.HR_NOTIFY_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_NOTIFY_READ)


def authorize_hr_notify_manage(scope: AccessScope) -> None:
    if Permission.HR_NOTIFY_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_NOTIFY_MANAGE)


def authorize_hr_reports_read(scope: AccessScope) -> None:
    if (
        Permission.HR_REPORTS_READ in scope.effective_permissions
        or Permission.HR_REPORTS_MANAGE in scope.effective_permissions
        or Permission.HR_REPORTS_EXPORT in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_REPORTS_READ)


def authorize_hr_reports_manage(scope: AccessScope) -> None:
    if Permission.HR_REPORTS_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_REPORTS_MANAGE)


def authorize_hr_reports_export(scope: AccessScope) -> None:
    if (
        Permission.HR_REPORTS_EXPORT in scope.effective_permissions
        or Permission.HR_REPORTS_MANAGE in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_REPORTS_EXPORT)


def authorize_hr_settings_read(scope: AccessScope) -> None:
    if (
        Permission.HR_SETTINGS_READ in scope.effective_permissions
        or Permission.HR_SETTINGS_MANAGE in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_SETTINGS_READ)


def authorize_hr_settings_manage(scope: AccessScope) -> None:
    if Permission.HR_SETTINGS_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_SETTINGS_MANAGE)


def authorize_hr_audit_read(scope: AccessScope) -> None:
    if (
        Permission.HR_AUDIT_READ in scope.effective_permissions
        or Permission.HR_AUDIT_EXPORT in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_AUDIT_READ)


def authorize_hr_audit_export(scope: AccessScope) -> None:
    if (
        Permission.HR_AUDIT_EXPORT in scope.effective_permissions
        or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    ):
        return
    authorize(scope, Permission.HR_AUDIT_EXPORT)


def authorize_hr_access_manage(scope: AccessScope) -> None:
    if Permission.HR_ACCESS_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.HR_ACCESS_MANAGE)