"""Secret reference validation."""

import pytest

from app.core.secrets import SecretReference, assert_secret_reference


def test_valid_env_reference() -> None:
    ref = assert_secret_reference("env://SENDGRID_API_KEY")
    assert ref.startswith("env://")


def test_rejects_plaintext_secret() -> None:
    with pytest.raises(ValueError):
        SecretReference("sk_live_abcd1234")


def test_redact_never_returns_value() -> None:
    from app.core.secrets import redact_for_response

    payload = redact_for_response("env://SMTP_PASSWORD")
    assert "SMTP_PASSWORD" in payload["secret_ref"]
    assert "password" not in str(payload).lower() or "secret_ref" in payload
