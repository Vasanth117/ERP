"""Digital resource RBAC."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.library.policy import require_library_tenant_scope


def authorize_digital_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_DIGITAL_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_DIGITAL_MANAGE in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_DIGITAL_READ)


def authorize_digital_manage(scope: AccessScope) -> None:
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_DIGITAL_MANAGE)


def authorize_digital_patron(scope: AccessScope) -> None:
    """Student or staff patron catalogue access."""
    if Permission.STUDENT_LIBRARY_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_DIGITAL_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.STUDENT_LIBRARY_READ)


def require_digital_tenant(scope: AccessScope):
    return require_library_tenant_scope(scope)


def require_patron_tenant(scope: AccessScope):
    """Tenant context for students/staff accessing e-resources (not librarian portal)."""
    authorize_digital_patron(scope)
    if scope.tenant_id is None:
        raise AppError(
            code="TENANT_REQUIRED",
            message="College context is required",
            status_code=403,
        )
    return scope.tenant_id