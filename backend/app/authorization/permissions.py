"""Permission codes and role-to-permission mapping."""

from enum import Enum

from app.common.roles import Role


class Permission(str, Enum):
  PLATFORM_TENANT_MANAGE = "platform:tenant:manage"
  PLATFORM_TENANT_READ = "platform:tenant:read"
  TENANT_READ = "tenant:read"
  TENANT_DEPARTMENT_MANAGE = "tenant:department:manage"
  TENANT_DEPARTMENT_READ = "tenant:department:read"
  TENANT_USER_MANAGE = "tenant:user:manage"
  TENANT_USER_READ = "tenant:user:read"
  TENANT_AUDIT_READ = "tenant:audit:read"
  AUTH_SESSION_MANAGE = "auth:session:manage"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
  Role.SUPER_ADMIN: frozenset(
    {
      Permission.PLATFORM_TENANT_MANAGE,
      Permission.PLATFORM_TENANT_READ,
      Permission.TENANT_READ,
      Permission.TENANT_DEPARTMENT_MANAGE,
      Permission.TENANT_DEPARTMENT_READ,
      Permission.TENANT_USER_MANAGE,
      Permission.TENANT_USER_READ,
      Permission.TENANT_AUDIT_READ,
      Permission.AUTH_SESSION_MANAGE,
    }
  ),
  Role.PLATFORM_ADMIN: frozenset(
    {
      Permission.PLATFORM_TENANT_READ,
      Permission.TENANT_READ,
      Permission.TENANT_AUDIT_READ,
    }
  ),
  Role.COLLEGE_ADMIN: frozenset(
    {
      Permission.TENANT_READ,
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
