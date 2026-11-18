"""Library report RBAC."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.library.report_catalog import catalog_item


def authorize_report_read(scope: AccessScope) -> None:
    if Permission.LIBRARY_REPORT_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_READ in scope.effective_permissions:
        return
    if Permission.LIBRARY_DASHBOARD_READ in scope.effective_permissions:
        return
    authorize(scope, Permission.LIBRARY_REPORT_READ)


def authorize_report_export(scope: AccessScope) -> None:
    if Permission.LIBRARY_REPORT_EXPORT in scope.effective_permissions:
        return
    if Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions or scope.role == Role.COLLEGE_ADMIN:
        return
    authorize(scope, Permission.LIBRARY_REPORT_EXPORT)


def can_view_finance_reports(scope: AccessScope) -> bool:
    return (
        Permission.LIBRARY_REPORT_FINANCE in scope.effective_permissions
        or Permission.LIBRARY_FINE_MANAGE in scope.effective_permissions
        or Permission.LIBRARY_ADMIN_MANAGE in scope.effective_permissions
        or scope.role == Role.COLLEGE_ADMIN
    )


def require_report_type(scope: AccessScope, report_type: str) -> None:
    item = catalog_item(report_type)
    if item is None:
        raise AppError(code="NOT_FOUND", message="Unknown report type", status_code=404)
    if item.requires_finance_permission and not can_view_finance_reports(scope):
        raise AppError(code="FORBIDDEN", message="Financial report access denied", status_code=403)