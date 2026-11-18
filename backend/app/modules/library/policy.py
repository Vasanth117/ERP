"""Library (librarian portal) authorization helpers."""

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.core.exceptions import AppError


def _has_dashboard_read(scope: AccessScope) -> bool:
    return Permission.LIBRARY_DASHBOARD_READ in scope.effective_permissions or Permission.LIBRARY_ADMIN_READ in scope.effective_permissions


def _has_library_portal_access(scope: AccessScope) -> bool:
    return (
        _has_dashboard_read(scope)
        or Permission.LIBRARY_FACILITY_READ in scope.effective_permissions
        or Permission.LIBRARY_FACILITY_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_CATALOGUE_READ in scope.effective_permissions
        or Permission.LIBRARY_CATALOGUE_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_INVENTORY_READ in scope.effective_permissions
        or Permission.LIBRARY_INVENTORY_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_MEMBER_READ in scope.effective_permissions
        or Permission.LIBRARY_MEMBER_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_CIRCULATION_READ in scope.effective_permissions
        or Permission.LIBRARY_CIRCULATION_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_RESERVATION_READ in scope.effective_permissions
        or Permission.LIBRARY_RESERVATION_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_FINE_READ in scope.effective_permissions
        or Permission.LIBRARY_FINE_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_FINE_APPROVE in scope.effective_permissions
        or Permission.LIBRARY_ACQUISITION_READ in scope.effective_permissions
        or Permission.LIBRARY_ACQUISITION_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_ACQUISITION_APPROVE in scope.effective_permissions
        or Permission.LIBRARY_ACQUISITION_PROCURE in scope.effective_permissions
        or Permission.LIBRARY_DIGITAL_READ in scope.effective_permissions
        or Permission.LIBRARY_DIGITAL_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_NOTIFICATION_READ in scope.effective_permissions
        or Permission.LIBRARY_NOTIFICATION_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_NOTIFICATION_PUBLISH in scope.effective_permissions
        or Permission.LIBRARY_NOTIFICATION_RUN in scope.effective_permissions
        or Permission.LIBRARY_REPORT_READ in scope.effective_permissions
        or Permission.LIBRARY_REPORT_EXPORT in scope.effective_permissions
        or Permission.LIBRARY_REPORT_FINANCE in scope.effective_permissions
        or Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions
    )


def authorize_library_dashboard(scope: AccessScope) -> None:
    """Librarian dashboard or college library administration read access."""
    if _has_dashboard_read(scope):
        return
    authorize(scope, Permission.LIBRARY_DASHBOARD_READ)


def authorize_library_portal(scope: AccessScope) -> None:
    """Any librarian portal capability (dashboard or facility management)."""
    if _has_library_portal_access(scope):
        return
    authorize(scope, Permission.LIBRARY_SELF_ACCESS)


def require_library_tenant_scope(scope: AccessScope) -> PydanticObjectId:
    """Resolve tenant from trusted authentication context only."""
    authorize_library_portal(scope)
    if scope.tenant_id is None:
        raise AppError(
            code="TENANT_REQUIRED",
            message="College context is required",
            status_code=403,
        )
    return scope.tenant_id