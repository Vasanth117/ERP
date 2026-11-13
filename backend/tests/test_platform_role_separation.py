"""Least-privilege platform role mapping."""

from app.authorization.permissions import Permission
from app.authorization.platform_roles import PLATFORM_ROLE_PERMISSIONS
from app.modules.platform_identity.enums import PlatformRoleCode


def test_support_operator_cannot_manage_tenants() -> None:
    perms = PLATFORM_ROLE_PERMISSIONS[PlatformRoleCode.PLATFORM_SUPPORT_OPERATOR]
    assert Permission.PLATFORM_TENANT_MANAGE not in perms
    assert Permission.SUPPORT_ACCESS_EXECUTE in perms


def test_auditor_read_only_security() -> None:
    perms = PLATFORM_ROLE_PERMISSIONS[PlatformRoleCode.PLATFORM_SECURITY_AUDITOR]
    assert Permission.PLATFORM_SECURITY_MANAGE not in perms
    assert Permission.PLATFORM_AUDIT_EXPORT in perms
