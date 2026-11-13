"""Platform and tenant configuration documents."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class PlatformConfiguration(Document):
    """Singleton platform settings (`scope_key` = 'global')."""

    scope_key: str = "global"
    settings: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "platform_configurations"
        indexes = [
            IndexModel([("scope_key", ASCENDING)], unique=True, name="unique_platform_config_scope"),
        ]


class TenantConfiguration(Document):
    tenant_id: PydanticObjectId
    settings: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "tenant_configurations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_tenant_configuration"),
        ]


class TenantBranding(Document):
    tenant_id: PydanticObjectId
    display_name: str
    logo_file_id: str | None = None
    favicon_file_id: str | None = None
    primary_color: str = "#1E40AF"
    secondary_color: str = "#64748B"
    theme: dict[str, str] = Field(default_factory=dict)
    version: int = 1
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "tenant_branding"
        indexes = [
            IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_tenant_branding"),
        ]


class TenantFeatureFlags(Document):
    tenant_id: PydanticObjectId
    flags: dict[str, bool] = Field(default_factory=dict)
    version: int = 1
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "tenant_feature_flags"
        indexes = [
            IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_tenant_feature_flags"),
        ]


class ConfigurationVersion(Document):
    tenant_id: PydanticObjectId | None = None
    scope: str
    version_number: int
    snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId | None = None

    class Settings:
        name = "configuration_versions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("scope", ASCENDING), ("version_number", DESCENDING)],
                name="config_versions_by_tenant_scope",
            ),
            IndexModel(
                [("scope", ASCENDING), ("version_number", DESCENDING)],
                name="config_versions_platform",
            ),
        ]


class ConfigurationChangeHistory(Document):
    tenant_id: PydanticObjectId | None = None
    scope: str
    version_number: int
    changed_keys: list[str] = Field(default_factory=list)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "configuration_change_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("created_at", DESCENDING)],
                name="config_change_by_tenant",
            ),
        ]
