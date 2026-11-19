"""Hostel Admin portal authorization."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.core.exceptions import AppError


def _has_college_hostel_read(scope: AccessScope) -> bool:
    return Permission.HOSTEL_ADMIN_READ in scope.effective_permissions


def _has_college_hostel_manage(scope: AccessScope) -> bool:
    return Permission.HOSTEL_ADMIN_MANAGE in scope.effective_permissions


def has_hostel_portal_access(scope: AccessScope) -> bool:
    perms = scope.effective_permissions
    return (
        Permission.HOSTEL_SELF_ACCESS in perms
        or Permission.HOSTEL_DASHBOARD_READ in perms
        or Permission.HOSTEL_INFRASTRUCTURE_READ in perms
        or Permission.HOSTEL_INFRASTRUCTURE_MANAGE in perms
        or Permission.HOSTEL_ALLOCATION_READ in perms
        or Permission.HOSTEL_ALLOCATION_MANAGE in perms
        or Permission.HOSTEL_APPLICATION_READ in perms
        or Permission.HOSTEL_APPLICATION_MANAGE in perms
        or Permission.HOSTEL_RESIDENT_READ in perms
        or Permission.HOSTEL_RESIDENT_MANAGE in perms
        or Permission.HOSTEL_VISITOR_READ in perms
        or Permission.HOSTEL_VISITOR_MANAGE in perms
        or Permission.HOSTEL_MESS_READ in perms
        or Permission.HOSTEL_MESS_MANAGE in perms
        or Permission.HOSTEL_LEAVE_READ in perms
        or Permission.HOSTEL_LEAVE_MANAGE in perms
        or Permission.HOSTEL_GATE_MANAGE in perms
        or Permission.HOSTEL_MAINTENANCE_READ in perms
        or Permission.HOSTEL_MAINTENANCE_MANAGE in perms
        or Permission.HOSTEL_RULES_READ in perms
        or Permission.HOSTEL_RULES_MANAGE in perms
        or Permission.HOSTEL_INCIDENT_READ in perms
        or Permission.HOSTEL_INCIDENT_MANAGE in perms
        or Permission.HOSTEL_INCIDENT_INVESTIGATE in perms
        or Permission.HOSTEL_NOTIFY_READ in perms
        or Permission.HOSTEL_NOTIFY_MANAGE in perms
        or Permission.HOSTEL_REPORTS_READ in perms
        or Permission.HOSTEL_REPORTS_EXPORT in perms
        or Permission.HOSTEL_REPORTS_MANAGE in perms
        or Permission.HOSTEL_INTEGRATION_READ in perms
        or Permission.HOSTEL_INTEGRATION_MANAGE in perms
        or Permission.HOSTEL_AUDIT_READ in perms
        or Permission.HOSTEL_AUDIT_EXPORT in perms
        or Permission.HOSTEL_CONFIG_READ in perms
        or Permission.HOSTEL_CONFIG_MANAGE in perms
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
        or Permission.HOSTEL_ADMIN_ALLOCATE in perms
    )


def authorize_hostel_allocation_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_ALLOCATION_READ in scope.effective_permissions
        or Permission.HOSTEL_ALLOCATION_MANAGE in scope.effective_permissions
        or Permission.HOSTEL_ADMIN_ALLOCATE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_ALLOCATION_READ)


def authorize_hostel_allocation_manage(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_ALLOCATION_MANAGE in scope.effective_permissions
        or Permission.HOSTEL_ADMIN_ALLOCATE in scope.effective_permissions
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_ALLOCATION_MANAGE)


def authorize_hostel_application_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_APPLICATION_READ in scope.effective_permissions
        or Permission.HOSTEL_APPLICATION_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_APPLICATION_READ)


def authorize_hostel_application_manage(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_APPLICATION_MANAGE in scope.effective_permissions
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_APPLICATION_MANAGE)


def authorize_hostel_dashboard(scope: AccessScope) -> None:
    if Permission.HOSTEL_DASHBOARD_READ in scope.effective_permissions or _has_college_hostel_read(scope):
        return
    authorize(scope, Permission.HOSTEL_DASHBOARD_READ)


def authorize_hostel_infrastructure_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_INFRASTRUCTURE_READ in scope.effective_permissions
        or Permission.HOSTEL_INFRASTRUCTURE_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_INFRASTRUCTURE_READ)


def authorize_hostel_infrastructure_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_INFRASTRUCTURE_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_INFRASTRUCTURE_MANAGE)


def authorize_hostel_resident_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_RESIDENT_READ in scope.effective_permissions
        or Permission.HOSTEL_RESIDENT_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_RESIDENT_READ)


def authorize_hostel_resident_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_RESIDENT_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_RESIDENT_MANAGE)


def authorize_hostel_visitor_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_VISITOR_READ in scope.effective_permissions
        or Permission.HOSTEL_VISITOR_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_VISITOR_READ)


def authorize_hostel_visitor_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_VISITOR_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_VISITOR_MANAGE)


def authorize_hostel_mess_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_MESS_READ in scope.effective_permissions
        or Permission.HOSTEL_MESS_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_MESS_READ)


def authorize_hostel_mess_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_MESS_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_MESS_MANAGE)


def authorize_hostel_leave_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_LEAVE_READ in scope.effective_permissions
        or Permission.HOSTEL_LEAVE_MANAGE in scope.effective_permissions
        or Permission.HOSTEL_GATE_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_LEAVE_READ)


def authorize_hostel_leave_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_LEAVE_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_LEAVE_MANAGE)


def authorize_hostel_maintenance_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_MAINTENANCE_READ in scope.effective_permissions
        or Permission.HOSTEL_MAINTENANCE_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_MAINTENANCE_READ)


def authorize_hostel_maintenance_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_MAINTENANCE_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_MAINTENANCE_MANAGE)


def authorize_hostel_rules_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_RULES_READ in scope.effective_permissions
        or Permission.HOSTEL_RULES_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_RULES_READ)


def authorize_hostel_rules_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_RULES_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_RULES_MANAGE)


def authorize_hostel_incident_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_INCIDENT_READ in scope.effective_permissions
        or Permission.HOSTEL_INCIDENT_MANAGE in scope.effective_permissions
        or Permission.HOSTEL_INCIDENT_INVESTIGATE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_INCIDENT_READ)


def authorize_hostel_incident_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_INCIDENT_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_INCIDENT_MANAGE)


def authorize_hostel_notify_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_NOTIFY_READ in scope.effective_permissions
        or Permission.HOSTEL_NOTIFY_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_NOTIFY_READ)


def authorize_hostel_notify_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_NOTIFY_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_NOTIFY_MANAGE)


def authorize_hostel_reports_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_REPORTS_READ in scope.effective_permissions
        or Permission.HOSTEL_REPORTS_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_REPORTS_READ)


def authorize_hostel_reports_export(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_REPORTS_EXPORT in scope.effective_permissions
        or Permission.HOSTEL_REPORTS_MANAGE in scope.effective_permissions
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_REPORTS_EXPORT)


def authorize_hostel_reports_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_REPORTS_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_REPORTS_MANAGE)


def authorize_hostel_incident_investigate(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_INCIDENT_INVESTIGATE in scope.effective_permissions
        or Permission.HOSTEL_INCIDENT_MANAGE in scope.effective_permissions
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_INCIDENT_INVESTIGATE)


def authorize_hostel_gate_manage(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_GATE_MANAGE in scope.effective_permissions
        or Permission.HOSTEL_LEAVE_MANAGE in scope.effective_permissions
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_GATE_MANAGE)


def authorize_hostel_integration_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_INTEGRATION_READ in scope.effective_permissions
        or Permission.HOSTEL_INTEGRATION_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_INTEGRATION_READ)


def authorize_hostel_integration_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_INTEGRATION_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_INTEGRATION_MANAGE)


def authorize_hostel_audit_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_AUDIT_READ in scope.effective_permissions
        or Permission.HOSTEL_AUDIT_EXPORT in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_AUDIT_READ)


def authorize_hostel_audit_export(scope: AccessScope) -> None:
    if Permission.HOSTEL_AUDIT_EXPORT in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_AUDIT_EXPORT)


def authorize_hostel_config_read(scope: AccessScope) -> None:
    if (
        Permission.HOSTEL_CONFIG_READ in scope.effective_permissions
        or Permission.HOSTEL_CONFIG_MANAGE in scope.effective_permissions
        or _has_college_hostel_read(scope)
        or _has_college_hostel_manage(scope)
    ):
        return
    authorize(scope, Permission.HOSTEL_CONFIG_READ)


def authorize_hostel_config_manage(scope: AccessScope) -> None:
    if Permission.HOSTEL_CONFIG_MANAGE in scope.effective_permissions or _has_college_hostel_manage(scope):
        return
    authorize(scope, Permission.HOSTEL_CONFIG_MANAGE)


def require_hostel_tenant_scope(scope: AccessScope) -> PydanticObjectId:
    if not has_hostel_portal_access(scope):
        authorize(scope, Permission.HOSTEL_SELF_ACCESS)
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context is required", status_code=403)
    return scope.tenant_id