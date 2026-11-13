"""Platform API authorization tests."""

import pytest
from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.platform_roles import PLATFORM_ROLE_PERMISSIONS
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.platform_identity.enums import PlatformRoleCode


def _scope(role: Role, *, permissions=None) -> AccessScope:
    if permissions is None:
        permissions = PLATFORM_ROLE_PERMISSIONS.get(PlatformRoleCode.PLATFORM_OPS_ADMIN, frozenset())
    return AccessScope(
        role=role,
        user_id=PydanticObjectId(),
        tenant_id=None,
        department_id=None,
        effective_permissions=permissions,
    )


def test_college_admin_cannot_manage_tenants() -> None:
    with pytest.raises(AppError) as exc:
        authorize(_scope(Role.COLLEGE_ADMIN), Permission.PLATFORM_TENANT_MANAGE)
    assert exc.value.status_code == 403


def test_platform_admin_can_read_dashboard() -> None:
    perms = PLATFORM_ROLE_PERMISSIONS[PlatformRoleCode.PLATFORM_OPS_ADMIN]
    authorize(_scope(Role.PLATFORM_ADMIN, permissions=perms), Permission.PLATFORM_DASHBOARD_READ)


def test_college_admin_cannot_read_platform_dashboard() -> None:
    from app.authorization.permissions import permissions_for_role

    with pytest.raises(AppError) as exc:
        authorize(
            AccessScope(
                role=Role.COLLEGE_ADMIN,
                user_id=PydanticObjectId(),
                tenant_id=PydanticObjectId(),
                department_id=None,
                effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
            ),
            Permission.PLATFORM_DASHBOARD_READ,
        )
    assert exc.value.status_code == 403
