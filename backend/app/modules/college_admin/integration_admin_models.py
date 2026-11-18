"""College admin institution integration collections."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class InstitutionIntegrationStatus(str, Enum):
    DISABLED = "disabled"
    ENABLED = "enabled"
    REVOKED = "revoked"


class InstitutionIntegration(Document):
    tenant_id: PydanticObjectId
    integration_key: str
    provider_code: str
    title: str
    configuration_id: PydanticObjectId | None = None
    version: int = 1
    status: InstitutionIntegrationStatus = InstitutionIntegrationStatus.DISABLED
    actor_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_integrations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("integration_key", ASCENDING)], unique=True, name="unique_institution_integration"),
        ]


class InstitutionIntegrationConfiguration(Document):
    tenant_id: PydanticObjectId
    integration_key: str
    configuration_id: PydanticObjectId
    connection_url: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_integration_configurations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("integration_key", ASCENDING)], unique=True, name="unique_inst_integration_config"),
        ]


class InstitutionIntegrationHealth(Document):
    tenant_id: PydanticObjectId
    integration_key: str
    status: str = "unknown"
    last_check_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    detail: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_integration_health"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("integration_key", ASCENDING)], unique=True, name="unique_inst_integration_health"),
        ]


class InstitutionSyncHistory(Document):
    tenant_id: PydanticObjectId
    integration_key: str
    sync_id: str
    status: str
    detail: str | None = None
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: datetime | None = None

    class Settings:
        name = "institution_sync_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("integration_key", ASCENDING), ("started_at", DESCENDING)], name="inst_sync_history"),
        ]


class InstitutionWebhookEndpoint(Document):
    tenant_id: PydanticObjectId
    endpoint_id: str
    integration_key: str
    path_suffix: str
    signing_secret_ref: str
    enabled: bool = True
    replay_window_seconds: int = Field(default=300, ge=60, le=3600)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_webhook_endpoints"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("endpoint_id", ASCENDING)], unique=True, name="unique_webhook_endpoint"),
        ]


class InstitutionWebhookDeliveryLog(Document):
    tenant_id: PydanticObjectId
    delivery_id: str
    endpoint_id: str
    event_type: str
    idempotency_key: str
    signature_valid: bool | None = None
    status: str = "pending"
    attempt_count: int = 0
    last_error: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_webhook_delivery_logs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)], unique=True, name="unique_webhook_delivery"),
        ]


class InstitutionProviderCredentialReference(Document):
    tenant_id: PydanticObjectId
    integration_key: str
    credential_key: str
    secret_ref: str
    configuration_id: PydanticObjectId | None = None
    rotated_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_provider_credential_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("integration_key", ASCENDING), ("credential_key", ASCENDING)],
                unique=True,
                name="unique_inst_credential_ref",
            ),
        ]


class InstitutionIntegrationAuditLog(Document):
    tenant_id: PydanticObjectId
    integration_key: str
    action: str
    actor_id: PydanticObjectId | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_integration_audit_logs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="integration_audit"),
        ]