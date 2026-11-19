"""Hostel integration bindings, sync and reconciliation (no plaintext secrets)."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HostelIntegrationCategory(str, Enum):
    STUDENT = "student"
    FINANCE = "finance"
    NOTIFICATION = "notification"
    DOCUMENT = "document"
    GATE_SECURITY = "gate_security"
    CAMPUS = "campus"


class HostelIntegrationBindingStatus(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    FAILED = "failed"


class HostelSyncJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class HostelIntegrationBinding(Document):
    tenant_id: PydanticObjectId
    category: HostelIntegrationCategory
    integration_key: str
    provider_code: str
    platform_configuration_id: PydanticObjectId | None = None
    institution_integration_key: str | None = None
    enabled: bool = False
    sync_method: str = "scheduled"
    sync_frequency: str | None = None
    timeout_seconds: int = 30
    retry_max: int = 3
    backoff_seconds: int = 60
    owner_user_id: PydanticObjectId | None = None
    hostel_codes: list[str] = Field(default_factory=list)
    environment: str = "production"
    status: HostelIntegrationBindingStatus = HostelIntegrationBindingStatus.INACTIVE
    last_sync_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_integrations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("category", ASCENDING)], unique=True, name="unique_hostel_integration_category"),
            IndexModel([("tenant_id", ASCENDING), ("integration_key", ASCENDING)], unique=True, name="unique_hostel_integration_key"),
        ]


class HostelIntegrationMapping(Document):
    tenant_id: PydanticObjectId
    category: HostelIntegrationCategory
    external_ref: str
    internal_ref: str
    internal_type: str
    hostel_code: str | None = None
    verified_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_integration_mappings"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("category", ASCENDING), ("external_ref", ASCENDING)],
                unique=True,
                name="unique_hostel_integration_mapping",
            ),
            IndexModel([("tenant_id", ASCENDING), ("internal_ref", ASCENDING)], name="hostel_mapping_internal"),
        ]


class HostelIntegrationSyncJob(Document):
    tenant_id: PydanticObjectId
    job_id: str
    category: HostelIntegrationCategory
    direction: str = "outgoing"
    trigger: str = "manual"
    status: HostelSyncJobStatus = HostelSyncJobStatus.PENDING
    records_processed: int = 0
    records_success: int = 0
    records_failed: int = 0
    error_detail: str | None = None
    retry_count: int = 0
    started_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None
    actor_id: PydanticObjectId | None = None

    class Settings:
        name = "hostel_integration_sync_jobs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("job_id", ASCENDING)], unique=True, name="unique_hostel_sync_job"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("started_at", DESCENDING)], name="hostel_sync_by_status"),
        ]


class HostelIntegrationEvent(Document):
    tenant_id: PydanticObjectId
    event_id: str
    category: HostelIntegrationCategory
    external_event_id: str
    payload_hash: str
    signature_valid: bool | None = None
    status: str = "received"
    processing_note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    processed_at: datetime | None = None

    class Settings:
        name = "hostel_integration_events"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("event_id", ASCENDING)], unique=True, name="unique_hostel_integration_event"),
            IndexModel(
                [("tenant_id", ASCENDING), ("external_event_id", ASCENDING)],
                unique=True,
                name="unique_hostel_external_event",
            ),
        ]


class HostelIntegrationFailure(Document):
    tenant_id: PydanticObjectId
    failure_id: str
    category: HostelIntegrationCategory
    job_id: str | None = None
    event_id: str | None = None
    reason: str
    retriable: bool = True
    retry_count: int = 0
    resolved: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None

    class Settings:
        name = "hostel_integration_failures"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("failure_id", ASCENDING)], unique=True, name="unique_hostel_integration_failure"),
            IndexModel([("tenant_id", ASCENDING), ("resolved", ASCENDING), ("created_at", DESCENDING)], name="hostel_failures_open"),
        ]


class HostelIntegrationReconciliation(Document):
    tenant_id: PydanticObjectId
    record_id: str
    category: HostelIntegrationCategory
    internal_ref: str
    external_ref: str | None = None
    status: str = "pending"
    detail: dict[str, Any] = Field(default_factory=dict)
    last_checked_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_integration_reconciliation_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("record_id", ASCENDING)], unique=True, name="unique_hostel_recon"),
            IndexModel([("tenant_id", ASCENDING), ("category", ASCENDING), ("status", ASCENDING)], name="hostel_recon_by_cat"),
        ]


class HostelWebhookSubscription(Document):
    tenant_id: PydanticObjectId
    subscription_id: str
    category: HostelIntegrationCategory
    endpoint_path: str
    signing_secret_ref: str
    enabled: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_webhook_subscriptions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("subscription_id", ASCENDING)], unique=True, name="unique_hostel_webhook"),
        ]