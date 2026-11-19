"""Department Admin phase 7 — unit tests (no Mongo)."""

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.roles import Role
from app.core.exceptions import AppError
from app.modules.department_admin import request_categories as cat
from app.modules.department_admin.request_categories import compose_request_id, parse_request_id


def test_department_admin_phase7_permissions():
    perms = permissions_for_role(Role.DEPARTMENT_ADMIN)
    assert Permission.DEPARTMENT_REQUESTS_READ in perms
    assert Permission.DEPARTMENT_REQUESTS_MANAGE in perms
    assert Permission.DEPARTMENT_RESOURCES_READ in perms
    assert Permission.DEPARTMENT_RESOURCES_MANAGE in perms


def test_request_id_roundtrip():
    rid = compose_request_id(cat.STUDENT_CORRECTION, "507f1f77bcf86cd799439011")
    category, source = parse_request_id(rid)
    assert category == cat.STUDENT_CORRECTION
    assert source == "507f1f77bcf86cd799439011"


def test_request_id_invalid():
    with pytest.raises(AppError):
        parse_request_id("not-a-valid-id")