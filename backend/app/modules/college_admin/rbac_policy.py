"""Institutional RBAC policy — escalation prevention and assignable permissions."""

from app.authorization.permissions import Permission
from app.common.roles import Role, PLATFORM_ROLES

PRIVILEGED_INSTITUTION_ROLES = frozenset({Role.COLLEGE_ADMIN, Role.SUPER_ADMIN, Role.PLATFORM_ADMIN})

ROLE_RANK: dict[Role, int] = {
    Role.STUDENT: 10,
    Role.PARENT: 15,
    Role.FACULTY: 30,
    Role.LIBRARIAN: 35,
    Role.HOSTEL_ADMIN: 35,
    Role.ACCOUNTS_STAFF: 40,
    Role.FINANCE_STAFF: 40,
    Role.HR_STAFF: 40,
    Role.EXAMINATION_CELL: 45,
    Role.DEPARTMENT_ADMIN: 50,
    Role.COLLEGE_ADMIN: 90,
    Role.PLATFORM_ADMIN: 100,
    Role.SUPER_ADMIN: 110,
}

NON_ASSIGNABLE_ROLES = PLATFORM_ROLES | {Role.SUPER_ADMIN}

INSTITUTION_ASSIGNABLE_PERMISSIONS: frozenset[Permission] = frozenset(
    perm
    for perm in Permission
    if not perm.value.startswith("platform:")
    and perm
    not in (
        Permission.AUTH_SESSION_MANAGE,
        Permission.TENANT_USER_MANAGE,
        Permission.TENANT_CONFIG_MANAGE,
        Permission.TENANT_DEPARTMENT_MANAGE,
    )
)


def actor_may_assign_role(actor_role: Role, target_role: Role, *, has_privileged_grant: bool) -> None:
    from app.core.exceptions import AppError

    if target_role in NON_ASSIGNABLE_ROLES:
        raise AppError(code="FORBIDDEN", message="Cannot assign platform-level roles", status_code=403)
    if target_role in PRIVILEGED_INSTITUTION_ROLES and not has_privileged_grant:
        raise AppError(
            code="FORBIDDEN",
            message="Privileged role assignment is not permitted",
            status_code=403,
        )
    actor_rank = ROLE_RANK.get(actor_role, 0)
    target_rank = ROLE_RANK.get(target_role, 0)
    if target_rank >= actor_rank and actor_role != Role.SUPER_ADMIN:
        raise AppError(
            code="FORBIDDEN",
            message="Cannot assign a role at or above your privilege level",
            status_code=403,
        )


def validate_custom_permissions(
    granted: list[str],
    denied: list[str],
    *,
    base_role: Role,
) -> tuple[list[str], list[str]]:
    base_perms = {p.value for p in Permission if p in _permissions_for_base(base_role)}
    valid_codes = {p.value for p in INSTITUTION_ASSIGNABLE_PERMISSIONS}
    cleaned_grant: list[str] = []
    for code in granted:
        if code not in valid_codes:
            raise ValueError(f"Permission '{code}' cannot be assigned to custom roles")
        cleaned_grant.append(code)
    cleaned_deny: list[str] = []
    for code in denied:
        if code not in valid_codes:
            raise ValueError(f"Permission '{code}' cannot be used in custom roles")
        cleaned_deny.append(code)
    return cleaned_grant, cleaned_deny


def _permissions_for_base(role: Role) -> frozenset[Permission]:
    from app.authorization.permissions import permissions_for_role

    return permissions_for_role(role)
