"""Permission policy unit tests."""

from app.authorization.permissions import Permission, permissions_for_role
from app.common.roles import Role


def test_college_admin_can_manage_users() -> None:
    perms = permissions_for_role(Role.COLLEGE_ADMIN)
    assert Permission.TENANT_USER_MANAGE in perms
    assert Permission.PLATFORM_TENANT_MANAGE not in perms


def test_student_has_minimal_permissions() -> None:
    perms = permissions_for_role(Role.STUDENT)
    assert Permission.TENANT_USER_MANAGE not in perms
    assert Permission.TENANT_READ in perms
