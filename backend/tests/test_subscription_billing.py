"""Subscription module toggles and entitlements."""

import os

import pytest

os.environ["SAAS_BILLING_ENABLED"] = "false"

from app.core.config import get_settings
from app.modules.subscriptions.enforcement import billing_enabled, require_billing_enabled
from app.core.exceptions import AppError


def test_billing_disabled_by_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAAS_BILLING_ENABLED", "false")
    get_settings.cache_clear()
    assert billing_enabled() is False
    with pytest.raises(AppError) as exc:
        require_billing_enabled()
    assert exc.value.code == "BILLING_DISABLED"
    get_settings.cache_clear()
    monkeypatch.setenv("SAAS_BILLING_ENABLED", "true")
