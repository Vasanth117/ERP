"""Examination security, audit and integration API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.examinations.exam_cell_security_enums import ExamAccessReviewStatus, ExamIntegrationTarget
from app.modules.examinations.exam_cell_security_models import (
    ExamAccessReviewRecord,
    ExamAuditLog,
    ExamIntegrationConfig,
    ExamIntegrationFailure,
    ExamIntegrationSyncLog,
    ExamSecurityEvent,
)


class ExamIntegrationConfigUpdate(BaseModel):
    enabled: bool | None = None
    platform_provider_code: str | None = None
    webhook_enabled: bool | None = None
    webhook_secret_ref: str | None = Field(default=None, max_length=120)
    settings: dict[str, Any] | None = None


class ExamIntegrationConfigRead(BaseModel):
    config_id: str
    integration_target: str
    enabled: bool
    platform_provider_code: str | None
    platform_configuration_id: str | None
    webhook_enabled: bool
    webhook_secret_ref: str | None
    settings: dict[str, Any]
    updated_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamIntegrationConfig) -> "ExamIntegrationConfigRead":
        return cls(
            config_id=doc.config_id,
            integration_target=doc.integration_target,
            enabled=doc.enabled,
            platform_provider_code=doc.platform_provider_code,
            platform_configuration_id=str(doc.platform_configuration_id) if doc.platform_configuration_id else None,
            webhook_enabled=doc.webhook_enabled,
            webhook_secret_ref=doc.webhook_secret_ref,
            settings=dict(doc.settings or {}),
            updated_at=doc.updated_at,
        )


class ExamIntegrationSyncRequest(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=80)


class ExamIntegrationSyncLogRead(BaseModel):
    sync_id: str
    config_id: str
    integration_target: str
    status: str
    correlation_id: str | None
    duration_ms: int | None
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamIntegrationSyncLog) -> "ExamIntegrationSyncLogRead":
        return cls(
            sync_id=doc.sync_id,
            config_id=doc.config_id,
            integration_target=doc.integration_target,
            status=doc.status,
            correlation_id=doc.correlation_id,
            duration_ms=doc.duration_ms,
            created_at=doc.created_at,
        )


class ExamIntegrationFailureRead(BaseModel):
    failure_id: str
    integration_target: str
    error_code: str
    error_message: str
    retry_count: int
    recovered: bool
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamIntegrationFailure) -> "ExamIntegrationFailureRead":
        return cls(
            failure_id=doc.failure_id,
            integration_target=doc.integration_target,
            error_code=doc.error_code,
            error_message=doc.error_message,
            retry_count=doc.retry_count,
            recovered=doc.recovered,
            created_at=doc.created_at,
        )


class ExamIntegrationHealthReport(BaseModel):
    targets_total: int
    targets_enabled: int
    open_failures: int
    last_sync_at: datetime | None
    targets: list[dict[str, Any]]


class ExamAuditLogRead(BaseModel):
    audit_id: str
    actor_id: str | None
    action: str
    resource_type: str
    resource_id: str | None
    exam_session_id: str | None
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    reason: str | None
    approval_reference: str | None
    request_id: str | None
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamAuditLog) -> "ExamAuditLogRead":
        return cls(
            audit_id=doc.audit_id,
            actor_id=str(doc.actor_id) if doc.actor_id else None,
            action=doc.action,
            resource_type=doc.resource_type,
            resource_id=doc.resource_id,
            exam_session_id=str(doc.exam_session_id) if doc.exam_session_id else None,
            before_state=dict(doc.before_state or {}),
            after_state=dict(doc.after_state or {}),
            reason=doc.reason,
            approval_reference=doc.approval_reference,
            request_id=doc.request_id,
            created_at=doc.created_at,
        )


class ExamAuditSearch(BaseModel):
    resource_type: str | None = None
    resource_id: str | None = None
    action_prefix: str | None = None
    actor_id: str | None = None
    exam_session_id: str | None = None


class ExamSecurityEventRead(BaseModel):
    event_id: str
    event_type: str
    actor_id: str | None
    resource_type: str | None
    resource_id: str | None
    detail: str
    request_id: str | None
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamSecurityEvent) -> "ExamSecurityEventRead":
        return cls(
            event_id=doc.event_id,
            event_type=doc.event_type,
            actor_id=str(doc.actor_id) if doc.actor_id else None,
            resource_type=doc.resource_type,
            resource_id=doc.resource_id,
            detail=doc.detail,
            request_id=doc.request_id,
            created_at=doc.created_at,
        )


class ExamAccessReviewCreate(BaseModel):
    subject_user_id: str
    permission_codes: list[str] = Field(min_length=1, max_length=30)
    findings: str | None = Field(default=None, max_length=2000)


class ExamAccessReviewRead(BaseModel):
    review_id: str
    subject_user_id: str
    permission_codes: list[str]
    status: str
    findings: str | None
    reviewer_id: str | None
    completed_at: datetime | None
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamAccessReviewRecord) -> "ExamAccessReviewRead":
        return cls(
            review_id=doc.review_id,
            subject_user_id=str(doc.subject_user_id),
            permission_codes=list(doc.permission_codes),
            status=doc.status,
            findings=doc.findings,
            reviewer_id=str(doc.reviewer_id) if doc.reviewer_id else None,
            completed_at=doc.completed_at,
            created_at=doc.created_at,
        )


class ExamAccessReviewComplete(BaseModel):
    findings: str = Field(min_length=3, max_length=2000)


class ExamIntegrationWebhookPayload(BaseModel):
    idempotency_key: str = Field(min_length=8, max_length=80)
    event_type: str = Field(max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)
    signature: str | None = Field(default=None, max_length=256)


DEFAULT_INTEGRATION_TARGETS = [t.value for t in ExamIntegrationTarget]