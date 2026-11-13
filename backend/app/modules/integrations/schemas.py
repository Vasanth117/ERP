"""Integration API schemas."""

from datetime import datetime
from typing import Any

from beanie import PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field

from app.modules.integrations.enums import IntegrationProviderType, IntegrationScope
from app.modules.integrations.models import (
    IntegrationConfiguration,
    IntegrationHealth,
    IntegrationProvider,
    ProviderCredentialReference,
    WebhookDeliveryEvent,
)
from app.core.secrets import redact_for_response


class IntegrationProviderCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9_]+$")
    name: str = Field(min_length=2, max_length=200)
    provider_type: IntegrationProviderType
    version: str = Field(default="1", max_length=32)
    description: str = Field(default="", max_length=500)
    supports_tenant_credentials: bool = False
    supports_global_shared: bool = True


class IntegrationProviderRead(BaseModel):
    code: str
    name: str
    provider_type: IntegrationProviderType
    version: str
    description: str
    supports_tenant_credentials: bool
    supports_global_shared: bool

    @classmethod
    def from_document(cls, doc: IntegrationProvider) -> "IntegrationProviderRead":
        return cls(
            code=doc.code,
            name=doc.name,
            provider_type=doc.provider_type,
            version=doc.version,
            description=doc.description,
            supports_tenant_credentials=doc.supports_tenant_credentials,
            supports_global_shared=doc.supports_global_shared,
        )


class IntegrationConfigUpdate(BaseModel):
    scope: IntegrationScope = IntegrationScope.GLOBAL
    tenant_id: PydanticObjectId | None = None
    connection_url: str | None = Field(default=None, max_length=500)
    metadata: dict[str, Any] | None = None
    credential_refs: dict[str, str] = Field(default_factory=dict)


class IntegrationConfigRead(BaseModel):
    id: str
    provider_code: str
    scope: IntegrationScope
    tenant_id: str | None
    enabled: bool
    connection_url: str | None
    metadata: dict[str, Any]
    version: int
    credentials: list[dict[str, str]]
    health_status: str | None

    @classmethod
    def from_parts(
        cls,
        doc: IntegrationConfiguration,
        creds: list[ProviderCredentialReference],
        health: IntegrationHealth | None,
    ) -> "IntegrationConfigRead":
        return cls(
            id=str(doc.id),
            provider_code=doc.provider_code,
            scope=doc.scope,
            tenant_id=str(doc.tenant_id) if doc.tenant_id else None,
            enabled=doc.enabled,
            connection_url=doc.connection_url,
            metadata=doc.metadata,
            version=doc.version,
            credentials=[{"key": c.credential_key, **redact_for_response(c.secret_ref)} for c in creds],
            health_status=health.status.value if health else None,
        )


class WebhookDeliveryRead(BaseModel):
    id: str
    event_type: str
    status: str
    attempt_count: int
    signature_valid: bool | None
    created_at: datetime

    @classmethod
    def from_document(cls, doc: WebhookDeliveryEvent) -> "WebhookDeliveryRead":
        return cls(
            id=str(doc.id),
            event_type=doc.event_type,
            status=doc.status,
            attempt_count=doc.attempt_count,
            signature_valid=doc.signature_valid,
            created_at=doc.created_at,
        )
