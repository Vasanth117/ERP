"""Least-privilege platform role → permission mapping."""

from app.authorization.permissions import Permission
from app.modules.platform_identity.enums import PlatformRoleCode

_PLATFORM_OWNER: frozenset[Permission] = frozenset(
    {
        Permission.PLATFORM_DASHBOARD_READ,
        Permission.PLATFORM_TENANT_MANAGE,
        Permission.PLATFORM_TENANT_READ,
        Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE,
        Permission.PLATFORM_TENANT_LIFECYCLE_READ,
        Permission.PLATFORM_CONFIG_MANAGE,
        Permission.PLATFORM_CONFIG_READ,
        Permission.PLATFORM_USER_MANAGE,
        Permission.PLATFORM_USER_READ,
        Permission.PLATFORM_SECURITY_MANAGE,
        Permission.PLATFORM_SECURITY_READ,
        Permission.PLATFORM_AUDIT_READ,
        Permission.PLATFORM_AUDIT_EXPORT,
        Permission.SUPPORT_ACCESS_APPROVE,
        Permission.SUPPORT_ACCESS_REQUEST,
        Permission.SUPPORT_ACCESS_EXECUTE,
        Permission.PLATFORM_ACCESS_REVIEW_MANAGE,
        Permission.AUTH_SESSION_MANAGE,
        Permission.PLATFORM_OPS_READ,
        Permission.PLATFORM_OPS_MANAGE,
        Permission.INTEGRATION_READ,
        Permission.INTEGRATION_MANAGE,
        Permission.PLATFORM_EXPORT_READ,
        Permission.PLATFORM_EXPORT_MANAGE,
        Permission.PLATFORM_RETENTION_READ,
        Permission.PLATFORM_RETENTION_MANAGE,
        Permission.PLATFORM_OFFBOARDING_MANAGE,
        Permission.SUBSCRIPTION_READ,
        Permission.SUBSCRIPTION_MANAGE,
    }
)

_PLATFORM_SUPER_ADMIN: frozenset[Permission] = frozenset(
    {
        Permission.PLATFORM_DASHBOARD_READ,
        Permission.PLATFORM_TENANT_MANAGE,
        Permission.PLATFORM_TENANT_READ,
        Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE,
        Permission.PLATFORM_TENANT_LIFECYCLE_READ,
        Permission.PLATFORM_CONFIG_MANAGE,
        Permission.PLATFORM_CONFIG_READ,
        Permission.PLATFORM_USER_READ,
        Permission.PLATFORM_USER_MANAGE,
        Permission.PLATFORM_SECURITY_READ,
        Permission.PLATFORM_AUDIT_READ,
        Permission.SUPPORT_ACCESS_APPROVE,
        Permission.SUPPORT_ACCESS_REQUEST,
        Permission.SUPPORT_ACCESS_EXECUTE,
        Permission.PLATFORM_ACCESS_REVIEW_MANAGE,
        Permission.AUTH_SESSION_MANAGE,
        Permission.PLATFORM_OPS_READ,
        Permission.PLATFORM_OPS_MANAGE,
        Permission.INTEGRATION_READ,
        Permission.INTEGRATION_MANAGE,
        Permission.PLATFORM_EXPORT_READ,
        Permission.PLATFORM_EXPORT_MANAGE,
        Permission.PLATFORM_RETENTION_READ,
        Permission.PLATFORM_RETENTION_MANAGE,
        Permission.PLATFORM_OFFBOARDING_MANAGE,
        Permission.SUBSCRIPTION_READ,
        Permission.SUBSCRIPTION_MANAGE,
    }
)

_PLATFORM_OPS: frozenset[Permission] = frozenset(
    {
        Permission.PLATFORM_DASHBOARD_READ,
        Permission.PLATFORM_TENANT_READ,
        Permission.PLATFORM_TENANT_LIFECYCLE_READ,
        Permission.PLATFORM_CONFIG_READ,
        Permission.PLATFORM_SECURITY_READ,
        Permission.PLATFORM_AUDIT_READ,
        Permission.SUPPORT_ACCESS_REQUEST,
        Permission.PLATFORM_OPS_READ,
        Permission.PLATFORM_OPS_MANAGE,
        Permission.INTEGRATION_READ,
        Permission.PLATFORM_EXPORT_READ,
        Permission.PLATFORM_RETENTION_READ,
    }
)

_PLATFORM_SUPPORT: frozenset[Permission] = frozenset(
    {
        Permission.PLATFORM_TENANT_READ,
        Permission.SUPPORT_ACCESS_REQUEST,
        Permission.SUPPORT_ACCESS_EXECUTE,
        Permission.PLATFORM_SECURITY_READ,
    }
)

_PLATFORM_AUDITOR: frozenset[Permission] = frozenset(
    {
        Permission.PLATFORM_SECURITY_READ,
        Permission.PLATFORM_AUDIT_READ,
        Permission.PLATFORM_AUDIT_EXPORT,
        Permission.PLATFORM_ACCESS_REVIEW_MANAGE,
    }
)

_PLATFORM_BILLING: frozenset[Permission] = frozenset(
    {
        Permission.PLATFORM_DASHBOARD_READ,
        Permission.PLATFORM_TENANT_READ,
        Permission.PLATFORM_AUDIT_READ,
        Permission.SUBSCRIPTION_READ,
        Permission.SUBSCRIPTION_MANAGE,
        Permission.PLATFORM_EXPORT_READ,
    }
)

PLATFORM_ROLE_PERMISSIONS: dict[PlatformRoleCode, frozenset[Permission]] = {
    PlatformRoleCode.PLATFORM_OWNER: _PLATFORM_OWNER,
    PlatformRoleCode.PLATFORM_SUPER_ADMIN: _PLATFORM_SUPER_ADMIN,
    PlatformRoleCode.PLATFORM_OPS_ADMIN: _PLATFORM_OPS,
    PlatformRoleCode.PLATFORM_SUPPORT_OPERATOR: _PLATFORM_SUPPORT,
    PlatformRoleCode.PLATFORM_SECURITY_AUDITOR: _PLATFORM_AUDITOR,
    PlatformRoleCode.PLATFORM_BILLING_ADMIN: _PLATFORM_BILLING,
}
