"""Department Admin phase 6 — RBAC matrix (unit)."""

from app.authorization.permissions import Permission, permissions_for_role
from app.common.roles import Role


def test_department_admin_has_calendar_and_communication_permissions():
    perms = permissions_for_role(Role.DEPARTMENT_ADMIN)
    assert Permission.DEPARTMENT_CALENDAR_READ in perms
    assert Permission.DEPARTMENT_CALENDAR_MANAGE in perms
    assert Permission.DEPARTMENT_COMMUNICATION_READ in perms
    assert Permission.DEPARTMENT_COMMUNICATION_MANAGE in perms


def test_faculty_lacks_department_calendar_manage():
    perms = permissions_for_role(Role.FACULTY)
    assert Permission.DEPARTMENT_CALENDAR_MANAGE not in perms
    assert Permission.DEPARTMENT_COMMUNICATION_MANAGE not in perms