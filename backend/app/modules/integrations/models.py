"""Integration provider configuration (secret references only)."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.integrations.enums import IntegrationOperationalStatus, IntegrationProviderType, IntegrationScope


class IntegrationProvider(Document):
    code: str
    name: str
    provider_type: IntegrationProviderType
    version: str = "1"
    description: str = ""
    supports_tenant_credentials: bool = False
    supports_global_shared: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "integration_providers"
        indexes = [IndexModel([("code", ASCENDING)], unique=True, name="unique_integration_provider")]


class ProviderCredentialReference(Document):
    configuration_id: PydanticObjectId
    credential_key: str
    secret_ref: str
    rotated_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "provider_credential_references"
        indexes = [
            IndexModel(
                [("configuration_id", ASCENDING), ("credential_key", ASCENDING)],
                unique=True,
                name="unique_credential_ref",
            ),
        ]


class IntegrationConfiguration(Document):
    provider_code: str
    scope: IntegrationScope = IntegrationScope.GLOBAL
    tenant_id: PydanticObjectId | None = None
    enabled: bool = False
    connection_url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "integration_configurations"
        indexes = [
            IndexModel(
                [("provider_code", ASCENDING), ("scope", ASCENDING), ("tenant_id", ASCENDING)],
                unique=True,
                name="unique_integration_config",
            ),
        ]


class IntegrationHealth(Document):
    configuration_id: PydanticObjectId
    status: IntegrationOperationalStatus = IntegrationOperationalStatus.DISABLED
    last_check_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    detail: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "integration_health"
        indexes = [IndexModel([("configuration_id", ASCENDING)], unique=True, name="unique_integration_health")]


class IntegrationSyncHistory(Document):
    configuration_id: PydanticObjectId
    status: str
    detail: str | None = None
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None

    class Settings:
        name = "integration_sync_history"
        indexes = [IndexModel([("configuration_id", ASCENDING), ("started_at", DESCENDING)])]


class WebhookDeliveryEvent(Document):
    configuration_id: PydanticObjectId
    tenant_id: PydanticObjectId | None = None
    event_type: str
    destination_url: str
    idempotency_key: str
    signature_valid: bool | None = None
    status: str = "pending"
    attempt_count: int = 0
    last_error: str | None = None
    delivered_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "webhook_delivery_events"
        indexes = [
            IndexModel([("idempotency_key", ASCENDING)], unique=True, name="unique_webhook_idempotency"),
            IndexModel([("configuration_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)]),
        ]


class IntegrationConfigurationHistory(Document):
    configuration_id: PydanticObjectId
    version_number: int
    changed_keys: list[str] = Field(default_factory=list)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "integration_configuration_history"
        indexes = [
            IndexModel([("configuration_id", ASCENDING), ("version_number", DESCENDING)]),
        ]
