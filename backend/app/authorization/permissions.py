"""Permission codes and role-to-permission mapping."""

from enum import Enum

from app.common.roles import Role


class Permission(str, Enum):
  PLATFORM_DASHBOARD_READ = "platform:dashboard:read"
  PLATFORM_TENANT_MANAGE = "platform:tenant:manage"
  PLATFORM_TENANT_READ = "platform:tenant:read"
  PLATFORM_TENANT_LIFECYCLE_MANAGE = "platform:tenant:lifecycle:manage"
  PLATFORM_TENANT_LIFECYCLE_READ = "platform:tenant:lifecycle:read"
  PLATFORM_CONFIG_MANAGE = "platform:config:manage"
  PLATFORM_CONFIG_READ = "platform:config:read"
  TENANT_CONFIG_MANAGE = "tenant:config:manage"
  TENANT_CONFIG_READ = "tenant:config:read"
  TENANT_READ = "tenant:read"
  TENANT_DEPARTMENT_MANAGE = "tenant:department:manage"
  TENANT_DEPARTMENT_READ = "tenant:department:read"
  TENANT_USER_MANAGE = "tenant:user:manage"
  TENANT_USER_READ = "tenant:user:read"
  TENANT_AUDIT_READ = "tenant:audit:read"
  AUTH_SESSION_MANAGE = "auth:session:manage"
  PLATFORM_USER_MANAGE = "platform:user:manage"
  PLATFORM_USER_READ = "platform:user:read"
  PLATFORM_SECURITY_READ = "platform:security:read"
  PLATFORM_SECURITY_MANAGE = "platform:security:manage"
  PLATFORM_AUDIT_READ = "platform:audit:read"
  PLATFORM_AUDIT_EXPORT = "platform:audit:export"
  SUPPORT_ACCESS_REQUEST = "platform:support:request"
  SUPPORT_ACCESS_APPROVE = "platform:support:approve"
  SUPPORT_ACCESS_EXECUTE = "platform:support:execute"
  PLATFORM_ACCESS_REVIEW_MANAGE = "platform:access_review:manage"
  PLATFORM_OPS_READ = "platform:ops:read"
  PLATFORM_OPS_MANAGE = "platform:ops:manage"
  INTEGRATION_READ = "platform:integration:read"
  INTEGRATION_MANAGE = "platform:integration:manage"
  PLATFORM_EXPORT_READ = "platform:export:read"
  PLATFORM_EXPORT_MANAGE = "platform:export:manage"
  PLATFORM_RETENTION_READ = "platform:retention:read"
  PLATFORM_RETENTION_MANAGE = "platform:retention:manage"
  PLATFORM_OFFBOARDING_MANAGE = "platform:offboarding:manage"
  SUBSCRIPTION_READ = "platform:subscription:read"
  SUBSCRIPTION_MANAGE = "platform:subscription:manage"
  SUBSCRIPTION_BILLING_WEBHOOK = "platform:subscription:webhook"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
  # Legacy bootstrap account; new operators use platform role assignments (least privilege).
  Role.SUPER_ADMIN: frozenset({Permission.AUTH_SESSION_MANAGE}),
  Role.PLATFORM_ADMIN: frozenset(
    {
      Permission.PLATFORM_DASHBOARD_READ,
      Permission.PLATFORM_TENANT_READ,
      Permission.PLATFORM_TENANT_LIFECYCLE_READ,
      Permission.PLATFORM_CONFIG_READ,
      Permission.TENANT_READ,
      Permission.TENANT_AUDIT_READ,
    }
  ),
  Role.COLLEGE_ADMIN: frozenset(
    {
      Permission.TENANT_READ,
      Permission.TENANT_CONFIG_MANAGE,
      Permission.TENANT_CONFIG_READ,
      Permission.TENANT_DEPARTMENT_MANAGE,
      Permission.TENANT_DEPARTMENT_READ,
      Permission.TENANT_USER_MANAGE,
      Permission.TENANT_USER_READ,
      Permission.TENANT_AUDIT_READ,
      Permission.AUTH_SESSION_MANAGE,
    }
  ),
  Role.DEPARTMENT_ADMIN: frozenset(
    {
      Permission.TENANT_READ,
      Permission.TENANT_DEPARTMENT_READ,
      Permission.TENANT_USER_READ,
    }
  ),
  Role.FACULTY: frozenset({Permission.TENANT_READ}),
  Role.STUDENT: frozenset({Permission.TENANT_READ}),
  Role.PARENT: frozenset({Permission.TENANT_READ}),
  Role.FINANCE_STAFF: frozenset({Permission.TENANT_READ, Permission.TENANT_AUDIT_READ}),
  Role.HR_STAFF: frozenset({Permission.TENANT_USER_READ}),
  Role.EXAMINATION_CELL: frozenset({Permission.TENANT_READ, Permission.TENANT_AUDIT_READ}),
  Role.HOSTEL_ADMIN: frozenset({Permission.TENANT_READ}),
  Role.LIBRARIAN: frozenset({Permission.TENANT_READ}),
  Role.ACCOUNTS_STAFF: frozenset({Permission.TENANT_READ, Permission.TENANT_AUDIT_READ}),
}


def permissions_for_role(role: Role) -> frozenset[Permission]:
  return ROLE_PERMISSIONS.get(role, frozenset())
