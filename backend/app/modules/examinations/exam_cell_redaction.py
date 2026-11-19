"""Redact sensitive fields from audit and integration payloads."""

from typing import Any

_SENSITIVE_KEYS = {
    "password",
    "hashed_password",
    "token",
    "access_token",
    "refresh_token",
    "verification_code",
    "secret",
    "webhook_secret",
    "api_key",
    "pan",
    "aadhaar",
    "account_number",
    "card_number",
    "otp",
}


def _redact_value(value: Any) -> Any:
    if isinstance(value, dict):
        return redact_mapping(value)
    if isinstance(value, list):
        return [_redact_value(v) for v in value]
    return value


def redact_mapping(data: dict[str, Any] | None) -> dict[str, Any]:
    if not data:
        return {}
    out: dict[str, Any] = {}
    for key, value in data.items():
        lower = key.lower()
        if lower in _SENSITIVE_KEYS or any(part in lower for part in ("password", "secret", "token")):
            out[key] = "[REDACTED]"
            continue
        out[key] = _redact_value(value)
    return out