"""Hostel integration API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hostel.integration_models import HostelIntegrationCategory, HostelIntegrationBindingStatus, HostelSyncJobStatus


class IntegrationDashboard(BaseModel):
    total_bindings: int
    active_bindings: int
    inactive_bindings: int
    failed_bindings: int
    pending_jobs: int
    failed_jobs: int
    open_failures: int
    last_sync_at: datetime | None


class IntegrationBindingRead(BaseModel):
    category: HostelIntegrationCategory
    integration_key: str
    provider_code: str
    enabled: bool
    status: HostelIntegrationBindingStatus
    sync_method: str
    sync_frequency: str | None
    last_sync_at: datetime | None
    institution_integration_key: str | None


class IntegrationBindingUpsert(BaseModel):
    category: HostelIntegrationCategory
    provider_code: str
    institution_integration_key: str | None = None
    enabled: bool = False
    sync_method: str = "scheduled"
    sync_frequency: str | None = None
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    retry_max: int = Field(default=3, ge=0, le=10)
    backoff_seconds: int = Field(default=60, ge=10, le=3600)
    hostel_codes: list[str] = Field(default_factory=list)
    environment: str = "production"
    signing_secret_ref: str | None = None


class SyncJobRead(BaseModel):
    job_id: str
    category: HostelIntegrationCategory
    status: HostelSyncJobStatus
    records_processed: int
    records_success: int
    records_failed: int
    error_detail: str | None
    started_at: datetime
    completed_at: datetime | None


class ManualSyncRequest(BaseModel):
    category: HostelIntegrationCategory
    full_sync: bool = False


class WebhookIngest(BaseModel):
    external_event_id: str
    payload: dict[str, Any] = Field(default_factory=dict)
    signature: str | None = None


class ReconciliationRead(BaseModel):
    record_id: str
    category: HostelIntegrationCategory
    internal_ref: str
    external_ref: str | None
    status: str
    detail: dict[str, Any]


class IntegrationFailureRead(BaseModel):
    failure_id: str
    category: HostelIntegrationCategory
    reason: str
    retriable: bool
    retry_count: int
    resolved: bool


class IntegrationEventRead(BaseModel):
    event_id: str
    category: HostelIntegrationCategory
    external_event_id: str
    status: str
    signature_valid: bool | None
    created_at: datetime