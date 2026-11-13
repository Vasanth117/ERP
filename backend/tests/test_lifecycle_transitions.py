"""Lifecycle state machine tests."""

import pytest

from app.modules.tenants.enums import TenantLifecycleStatus, assert_lifecycle_transition


def test_active_to_suspended() -> None:
    assert_lifecycle_transition(TenantLifecycleStatus.ACTIVE, TenantLifecycleStatus.SUSPENDED)


def test_closed_is_terminal() -> None:
    with pytest.raises(ValueError):
        assert_lifecycle_transition(TenantLifecycleStatus.CLOSED, TenantLifecycleStatus.ACTIVE)


def test_suspended_to_active() -> None:
    assert_lifecycle_transition(TenantLifecycleStatus.SUSPENDED, TenantLifecycleStatus.ACTIVE)
