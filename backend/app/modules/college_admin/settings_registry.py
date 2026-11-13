"""Allowlisted institution settings (college-admin writable only)."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.modules.configuration.registry import BRANDING_THEME_KEYS

PROTECTED_INSTITUTION_KEYS = frozenset(
    {
        "lifecycle_status",
        "subscription_plan",
        "platform_feature_flags",
        "tenant_code",
        "max_users",
        "entitlements",
    }
)

INSTITUTION_SETTINGS_ALLOWLIST: dict[str, type] = {
    "locale": str,
    "timezone": str,
    "date_format": str,
    "time_format": str,
    "academic_year_display": str,
    "semester_display": str,
    "grade_display_scale": str,
    "show_department_in_reports": bool,
    "notification_digest_enabled": bool,
}


class InstitutionSettingsUpdate(BaseModel):
    locale: str | None = Field(default=None, max_length=16)
    timezone: str | None = Field(default=None, max_length=64)
    date_format: str | None = Field(default=None, max_length=32)
    time_format: str | None = Field(default=None, max_length=32)
    academic_year_display: str | None = Field(default=None, max_length=32)
    semester_display: str | None = Field(default=None, max_length=32)
    grade_display_scale: str | None = Field(default=None, max_length=32)
    show_department_in_reports: bool | None = None
    notification_digest_enabled: bool | None = None

    def to_settings_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.model_dump(exclude_none=True).items()}


class InstitutionBrandingUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    logo_file_id: str | None = Field(default=None, max_length=128)
    favicon_file_id: str | None = Field(default=None, max_length=128)
    primary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    theme: dict[str, str] | None = None

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, value: dict[str, str] | None) -> dict[str, str] | None:
        if value is None:
            return None
        unknown = set(value.keys()) - BRANDING_THEME_KEYS
        if unknown:
            raise ValueError(f"Unknown theme keys: {', '.join(sorted(unknown))}")
        return value


def merge_institution_settings(current: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    merged = dict(current)
    for key, value in updates.items():
        if key in PROTECTED_INSTITUTION_KEYS:
            raise ValueError(f"Setting '{key}' is controlled by the platform")
        if key not in INSTITUTION_SETTINGS_ALLOWLIST:
            raise ValueError(f"Setting '{key}' is not permitted")
        expected = INSTITUTION_SETTINGS_ALLOWLIST[key]
        if expected is bool and not isinstance(value, bool):
            raise TypeError(f"Key '{key}' must be a boolean")
        if expected is str and not isinstance(value, str):
            raise TypeError(f"Key '{key}' must be a string")
        merged[key] = value
    return merged
