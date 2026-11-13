"""Allowlisted configuration keys and validation."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

ALLOWED_ERP_MODULES = frozenset(
    {
        "academics",
        "students",
        "faculty",
        "attendance",
        "examinations",
        "finance",
        "hr",
        "library",
        "hostel",
    }
)

PLATFORM_SETTINGS_ALLOWLIST: dict[str, type] = {
    "maintenance_mode": bool,
    "maintenance_message": str,
    "default_locale": str,
    "default_timezone": str,
    "max_tenants": int,
    "support_email": str,
}

PROTECTED_PLATFORM_KEYS = frozenset(
    {
        "jwt_policy",
        "session_policy",
        "password_policy",
        "mfa_required",
        "cors_policy",
    }
)

TENANT_SETTINGS_ALLOWLIST: dict[str, type] = {
    "locale": str,
    "timezone": str,
    "date_format": str,
    "time_format": str,
    "enabled_modules": list,
    "operational_limits": dict,
    "subdomain": str,
}

TENANT_FEATURE_FLAGS_ALLOWLIST = frozenset(
    {
        "attendance_beta",
        "finance_v2",
        "examination_analytics",
        "parent_portal",
    }
)

BRANDING_THEME_KEYS = frozenset({"surface", "accent", "font_family", "border_radius"})


class PlatformSettingsUpdate(BaseModel):
    maintenance_mode: bool | None = None
    maintenance_message: str | None = Field(default=None, max_length=500)
    default_locale: str | None = Field(default=None, max_length=16)
    default_timezone: str | None = Field(default=None, max_length=64)
    max_tenants: int | None = Field(default=None, ge=1, le=100000)
    support_email: str | None = Field(default=None, max_length=200)

    def to_settings_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.model_dump(exclude_none=True).items()}


class TenantSettingsUpdate(BaseModel):
    locale: str | None = Field(default=None, max_length=16)
    timezone: str | None = Field(default=None, max_length=64)
    date_format: str | None = Field(default=None, max_length=32)
    time_format: str | None = Field(default=None, max_length=32)
    enabled_modules: list[str] | None = None
    operational_limits: dict[str, int] | None = None
    subdomain: str | None = Field(default=None, max_length=63)

    @field_validator("enabled_modules")
    @classmethod
    def validate_modules(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        invalid = [module for module in value if module not in ALLOWED_ERP_MODULES]
        if invalid:
            raise ValueError(f"Unknown modules: {', '.join(invalid)}")
        return value

    @field_validator("operational_limits")
    @classmethod
    def validate_limits(cls, value: dict[str, int] | None) -> dict[str, int] | None:
        if value is None:
            return None
        for key, limit in value.items():
            if not key.isidentifier() or limit < 0 or limit > 1_000_000:
                raise ValueError("Invalid operational limit entry")
        return value

    def to_settings_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.model_dump(exclude_none=True).items()}


class TenantBrandingUpdate(BaseModel):
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


class TenantFeatureFlagsUpdate(BaseModel):
    flags: dict[str, bool]

    @field_validator("flags")
    @classmethod
    def validate_flags(cls, value: dict[str, bool]) -> dict[str, bool]:
        unknown = set(value.keys()) - TENANT_FEATURE_FLAGS_ALLOWLIST
        if unknown:
            raise ValueError(f"Unknown feature flags: {', '.join(sorted(unknown))}")
        return value


def merge_allowlisted_settings(
    current: dict[str, Any],
    updates: dict[str, Any],
    allowlist: dict[str, type],
) -> dict[str, Any]:
    merged = dict(current)
    for key, value in updates.items():
        if key not in allowlist:
            raise ValueError(f"Configuration key '{key}' is not permitted")
        if key in PROTECTED_PLATFORM_KEYS:
            raise ValueError(f"Configuration key '{key}' is protected")
        expected = allowlist[key]
        if expected is list and not isinstance(value, list):
            raise TypeError(f"Key '{key}' must be a list")
        if expected is dict and not isinstance(value, dict):
            raise TypeError(f"Key '{key}' must be an object")
        if expected not in (list, dict) and not isinstance(value, expected):
            raise TypeError(f"Key '{key}' must be {expected.__name__}")
        merged[key] = value
    return merged
