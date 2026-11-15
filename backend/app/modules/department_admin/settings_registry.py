"""Allowlisted department-level settings."""

from typing import Any

DEPARTMENT_SETTINGS_ALLOWLIST: dict[str, type] = {
    "default_notification_channel": str,
    "coordination_email": str,
    "calendar_view_preference": str,
    "attendance_alert_enabled": bool,
    "assessment_deadline_reminder_days": int,
    "department_display_timezone": str,
}

PROTECTED_DEPARTMENT_SETTING_KEYS = frozenset({"delegation_enabled"})


def validate_department_setting(key: str, value: Any) -> Any:
    if key in PROTECTED_DEPARTMENT_SETTING_KEYS:
        raise ValueError(f"Setting {key} is managed by college administration")
    expected = DEPARTMENT_SETTINGS_ALLOWLIST.get(key)
    if expected is None:
        raise ValueError(f"Unknown department setting: {key}")
    if not isinstance(value, expected):
        raise ValueError(f"Setting {key} must be of type {expected.__name__}")
    if key == "calendar_view_preference" and value not in {"week", "month", "agenda"}:
        raise ValueError("calendar_view_preference must be week, month, or agenda")
    if key == "assessment_deadline_reminder_days" and not (1 <= int(value) <= 90):
        raise ValueError("assessment_deadline_reminder_days must be between 1 and 90")
    return value