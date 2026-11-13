"""Configuration allowlist tests."""

import pytest

from app.modules.configuration.registry import (
    PLATFORM_SETTINGS_ALLOWLIST,
    PROTECTED_PLATFORM_KEYS,
    merge_allowlisted_settings,
)


def test_rejects_unknown_platform_key() -> None:
    with pytest.raises(ValueError):
        merge_allowlisted_settings({}, {"unknown_key": True}, PLATFORM_SETTINGS_ALLOWLIST)


def test_rejects_protected_keys_in_merge() -> None:
    allowlist = {**PLATFORM_SETTINGS_ALLOWLIST, "jwt_policy": dict}
    with pytest.raises(ValueError):
        merge_allowlisted_settings({}, {"jwt_policy": {}}, allowlist)


def test_protected_keys_frozen() -> None:
    assert "jwt_policy" in PROTECTED_PLATFORM_KEYS
