"""Lifecycle confirmation and authorization."""

import pytest
from beanie import PydanticObjectId

from app.authorization.policy import authorize
from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.tenants.enums import LifecycleOperationType
from app.authorization.platform_roles import PLATFORM_ROLE_PERMISSIONS
from app.modules.platform_identity.enums import PlatformRoleCode
from app.modules.tenants.lifecycle_service import _validate_confirmation
from app.modules.tenants.models import Tenant
from app.modules.tenants.schemas_lifecycle import LifecycleConfirmation


def _scope(role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=PydanticObjectId(),
        tenant_id=None,
        department_id=None,
        effective_permissions=PLATFORM_ROLE_PERMISSIONS[PlatformRoleCode.PLATFORM_OWNER],
    )


def test_lifecycle_manage_requires_super_admin() -> None:
    with pytest.raises(AppError):
        authorize(
            AccessScope(
                role=Role.COLLEGE_ADMIN,
                user_id=PydanticObjectId(),
                tenant_id=PydanticObjectId(),
                department_id=None,
                effective_permissions=frozenset(),
            ),
            Permission.PLATFORM_TENANT_LIFECYCLE_MANAGE,
        )


def test_suspend_requires_matching_confirmation_phrase() -> None:
    tenant = Tenant(name="X", code="demo-college")
    with pytest.raises(AppError) as exc:
        _validate_confirmation(
            tenant,
            LifecycleOperationType.SUSPEND,
            LifecycleConfirmation(acknowledged=True, confirmation_phrase="wrong"),
        )
    assert exc.value.code == "CONFIRMATION_MISMATCH"
