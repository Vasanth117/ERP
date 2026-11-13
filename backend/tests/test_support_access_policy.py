"""Support access scope tests."""

import pytest

from app.modules.support_access.models import SUPPORT_ACCESS_SCOPES, SupportAccessScope


def test_support_scopes_are_narrow() -> None:
    assert SupportAccessScope.VIEW_TENANT_CONFIG.value in SUPPORT_ACCESS_SCOPES
    assert "view_student_records" not in SUPPORT_ACCESS_SCOPES


def test_support_scope_enum_complete() -> None:
    assert len(SUPPORT_ACCESS_SCOPES) == len(SupportAccessScope)
