"""Examination integration, security and audit persistence."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class ExamIntegrationConfig(Document):
    tenant_id: PydanticObjectId
    config_id: str
    integration_target: str
    enabled: bool = True
    platform_provider_code: str | None = None
    platform_configuration_id: PydanticObjectId | None = None
    webhook_enabled: bool = False
    webhook_secret_ref: str | None = None
    settings: dict[str, Any] = Field(default_factory=dict)
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_integration_configs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("config_id", ASCENDING)],
                unique=True,
                name="unique_exam_integration_config",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("integration_target", ASCENDING)],
                unique=True,
                name="unique_exam_integration_target",
            ),
        ]


class ExamIntegrationSyncLog(Document):
    tenant_id: PydanticObjectId
    sync_id: str
    config_id: str
    integration_target: str
    idempotency_key: str
    status: str
    request_redacted: dict[str, Any] = Field(default_factory=dict)
    response_redacted: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    correlation_id: str | None = None
    duration_ms: int | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_integration_sync_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("sync_id", ASCENDING)],
                unique=True,
                name="unique_exam_integration_sync",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                name="unique_exam_integration_sync_idempotency",
            ),
            IndexModel([("tenant_id", ASCENDING), ("config_id", ASCENDING), ("created_at", DESCENDING)], name="exam_sync_by_config"),
        ]


class ExamIntegrationFailure(Document):
    tenant_id: PydanticObjectId
    failure_id: str
    config_id: str
    integration_target: str
    sync_id: str | None = None
    error_code: str
    error_message: str = Field(max_length=500)
    retry_count: int = 0
    recovered: bool = False
    recovered_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_integration_failures"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("failure_id", ASCENDING)],
                unique=True,
                name="unique_exam_integration_failure",
            ),
            IndexModel([("tenant_id", ASCENDING), ("recovered", ASCENDING), ("created_at", DESCENDING)], name="exam_failures_open"),
        ]


class ExamSecurityEvent(Document):
    tenant_id: PydanticObjectId
    event_id: str
    event_type: str
    actor_id: PydanticObjectId | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    detail: str = Field(max_length=1000)
    request_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_security_events"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("event_id", ASCENDING)],
                unique=True,
                name="unique_exam_security_event",
            ),
            IndexModel([("tenant_id", ASCENDING), ("event_type", ASCENDING), ("created_at", DESCENDING)], name="exam_security_by_type"),
        ]


class ExamAuditLog(Document):
    """Append-only examination audit trail (no update/delete APIs)."""

    tenant_id: PydanticObjectId
    audit_id: str
    actor_id: PydanticObjectId | None = None
    action: str
    resource_type: str
    resource_id: str | None = None
    exam_session_id: PydanticObjectId | None = None
    before_state: dict[str, Any] = Field(default_factory=dict)
    after_state: dict[str, Any] = Field(default_factory=dict)
    reason: str | None = None
    approval_reference: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_audit_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("audit_id", ASCENDING)],
                unique=True,
                name="unique_exam_audit_log",
            ),
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="exam_audit_recent"),
            IndexModel(
                [("tenant_id", ASCENDING), ("resource_type", ASCENDING), ("resource_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_audit_resource_timeline",
            ),
        ]


class ExamAccessReviewRecord(Document):
    tenant_id: PydanticObjectId
    review_id: str
    subject_user_id: PydanticObjectId
    permission_codes: list[str] = Field(default_factory=list)
    status: str
    findings: str | None = Field(default=None, max_length=2000)
    reviewer_id: PydanticObjectId | None = None
    completed_at: datetime | None = None
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_access_review_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("review_id", ASCENDING)],
                unique=True,
                name="unique_exam_access_review",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], name="exam_access_reviews_status"),
        ]