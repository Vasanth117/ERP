"""Configuration API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.modules.configuration.models import (
    ConfigurationChangeHistory,
    ConfigurationVersion,
    PlatformConfiguration,
    TenantBranding,
    TenantConfiguration,
    TenantFeatureFlags,
)
from app.modules.tenants.enums import DomainVerificationStatus
from app.modules.tenants.lifecycle_models import DomainVerificationRecord
from app.modules.tenants.models import Tenant
from app.modules.tenants.platform_models import TenantDomain


class PlatformConfigurationRead(BaseModel):
    scope_key: str
    settings: dict[str, Any]
    version: int
    updated_at: datetime

    @classmethod
    def from_document(cls, doc: PlatformConfiguration) -> "PlatformConfigurationRead":
        return cls(
            scope_key=doc.scope_key,
            settings=doc.settings,
            version=doc.version,
            updated_at=doc.updated_at,
        )


class TenantConfigurationRead(BaseModel):
    tenant_id: str
    settings: dict[str, Any]
    version: int
    timezone: str
    locale: str
    feature_flags: dict[str, bool]
    branding_display_name: str | None
    updated_at: datetime

    @classmethod
    def from_parts(
        cls,
        doc: TenantConfiguration,
        *,
        flags: TenantFeatureFlags | None,
        branding: TenantBranding | None,
        tenant: Tenant,
    ) -> "TenantConfigurationRead":
        return cls(
            tenant_id=str(doc.tenant_id),
            settings=doc.settings,
            version=doc.version,
            timezone=tenant.timezone,
            locale=tenant.locale,
            feature_flags=flags.flags if flags else {},
            branding_display_name=branding.display_name if branding else tenant.name,
            updated_at=doc.updated_at,
        )


class BrandingRead(BaseModel):
    tenant_id: str
    display_name: str
    logo_file_id: str | None
    favicon_file_id: str | None
    primary_color: str
    secondary_color: str
    theme: dict[str, str]
    version: int
    updated_at: datetime

    @classmethod
    def from_document(cls, doc: TenantBranding) -> "BrandingRead":
        return cls(
            tenant_id=str(doc.tenant_id),
            display_name=doc.display_name,
            logo_file_id=doc.logo_file_id,
            favicon_file_id=doc.favicon_file_id,
            primary_color=doc.primary_color,
            secondary_color=doc.secondary_color,
            theme=doc.theme,
            version=doc.version,
            updated_at=doc.updated_at,
        )


class FeatureFlagsRead(BaseModel):
    tenant_id: str
    flags: dict[str, bool]
    version: int
    updated_at: datetime

    @classmethod
    def from_document(cls, doc: TenantFeatureFlags) -> "FeatureFlagsRead":
        return cls(
            tenant_id=str(doc.tenant_id),
            flags=doc.flags,
            version=doc.version,
            updated_at=doc.updated_at,
        )


class ConfigurationHistoryItem(BaseModel):
    scope: str
    version_number: int
    changed_keys: list[str]
    actor_id: str | None
    created_at: datetime

    @classmethod
    def from_document(cls, row: ConfigurationChangeHistory) -> "ConfigurationHistoryItem":
        return cls(
            scope=row.scope,
            version_number=row.version_number,
            changed_keys=row.changed_keys,
            actor_id=str(row.actor_id) if row.actor_id else None,
            created_at=row.created_at,
        )


class ConfigurationVersionRead(BaseModel):
    scope: str
    version_number: int
    created_at: datetime

    @classmethod
    def from_document(cls, doc: ConfigurationVersion) -> "ConfigurationVersionRead":
        return cls(scope=doc.scope, version_number=doc.version_number, created_at=doc.created_at)


class DomainVerificationInitResult(BaseModel):
    domain_id: str
    dns_record_name: str
    dns_record_value: str
    verification_token: str
    expires_at: datetime


class DomainVerificationStatusRead(BaseModel):
    domain_id: str
    normalized_domain: str
    verification_status: DomainVerificationStatus
    record_status: str | None
    verified_at: datetime | None

    @classmethod
    def from_domain(
        cls,
        domain: TenantDomain,
        record: DomainVerificationRecord | None,
    ) -> "DomainVerificationStatusRead":
        return cls(
            domain_id=str(domain.id),
            normalized_domain=domain.normalized_domain,
            verification_status=domain.verification_status,
            record_status=record.status if record else None,
            verified_at=domain.verified_at,
        )
