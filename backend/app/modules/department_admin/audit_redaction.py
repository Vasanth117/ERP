"""Redact sensitive audit metadata before department admin visibility."""

from typing import Any

_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "token",
        "access_token",
        "refresh_token",
        "secret",
        "api_key",
        "authorization",
        "storage_token",
    }
)


def redact_audit_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    out: dict[str, Any] = {}
    for key, value in metadata.items():
        lower = key.lower()
        if lower in _SENSITIVE_KEYS or any(part in lower for part in ("password", "token", "secret")):
            out[key] = "[redacted]"
        elif isinstance(value, dict):
            out[key] = redact_audit_metadata(value)
        else:
            out[key] = value
    return out


def action_category(action: str) -> str:
    if not action or "." not in action:
        return "other"
    parts = action.split(".")
    if len(parts) >= 2 and parts[0] == "department":
        return parts[1]
    return parts[0]