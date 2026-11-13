"""Tenant access guard tests."""

import pytest
from beanie import PydanticObjectId

from app.api.deps import assert_tenant_access
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.exceptions import AppError


def test_super_admin_without_header_can_read_any_tenant() -> None:
    scope = AccessScope(
        role=Role.SUPER_ADMIN,
        user_id=PydanticObjectId(),
        tenant_id=None,
        department_id=None,
    )
    assert_tenant_access(scope, PydanticObjectId())


def test_college_user_cannot_access_other_tenant() -> None:
    tenant_a = PydanticObjectId()
    tenant_b = PydanticObjectId()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=PydanticObjectId(),
        tenant_id=tenant_a,
        department_id=None,
    )
    with pytest.raises(AppError) as exc:
        assert_tenant_access(scope, tenant_b)
    assert exc.value.code == "FORBIDDEN"
