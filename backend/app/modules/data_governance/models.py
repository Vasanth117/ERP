"""MongoDB documents for export, retention and offboarding."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.data_governance.enums import (
    ArchivalStatus,
    DeletionRequestStatus,
    ExportFormat,
    ExportJobStatus,
    ExportRequestStatus,
    LegalHoldStatus,
    OffboardingWorkflowStage,
    RetentionExecutionStatus,
)


class TenantExportRequest(Document):
    tenant_id: PydanticObjectId
    requested_by: PydanticObjectId
    status: ExportRequestStatus = ExportRequestStatus.PENDING_REVIEW
    formats: list[ExportFormat] = Field(default_factory=lambda: [ExportFormat.JSON])
    module_scopes: list[str] = Field(default_factory=list)
    include_document_metadata: bool = False
    include_sensitive: bool = False
    review_note: str | None = None
    reviewed_by: PydanticObjectId | None = None
    reviewed_at: datetime | None = None
    idempotency_key: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_export_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="tenant_export_requests_tenant"),
            IndexModel(
                [("tenant_id", ASCENDING), ("idempotency_key", ASCENDING)],
                unique=True,
                partialFilterExpression={"idempotency_key": {"$type": "string"}},
                name="unique_export_idempotency",
            ),
        ]


class TenantExportJob(Document):
    tenant_id: PydanticObjectId
    request_id: PydanticObjectId
    status: ExportJobStatus = ExportJobStatus.PENDING
    progress_percent: int = 0
    attempt_count: int = 0
    safe_to_retry: bool = True
    last_error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_export_jobs"
        indexes = [
            IndexModel([("request_id", ASCENDING)], unique=True, name="unique_export_job_per_request"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="tenant_export_jobs_status"),
        ]


class TenantExportArtifact(Document):
    tenant_id: PydanticObjectId
    job_id: PydanticObjectId
    format: ExportFormat
    storage_key: str
    byte_size: int = 0
    checksum_sha256: str | None = None
    validated: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_export_artifacts"
        indexes = [
            IndexModel([("job_id", ASCENDING)], name="export_artifacts_job"),
            IndexModel([("tenant_id", ASCENDING)], name="export_artifacts_tenant"),
        ]


class TenantExportDownload(Document):
    tenant_id: PydanticObjectId
    artifact_id: PydanticObjectId
    issued_to: PydanticObjectId
    token_hash: str
    expires_at: datetime
    download_count: int = 0
    max_downloads: int = 3
    revoked: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    last_access_at: datetime | None = None

    class Settings:
        name = "tenant_export_downloads"
        indexes = [
            IndexModel([("token_hash", ASCENDING)], unique=True, name="unique_export_download_token"),
            IndexModel([("artifact_id", ASCENDING)], name="export_downloads_artifact"),
        ]


class TenantRetentionPolicy(Document):
    tenant_id: PydanticObjectId | None = None
    name: str = "default"
    retention_days: int = 90
    post_offboarding_days: int = 30
    allow_deletion: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_retention_policies"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("name", ASCENDING)],
                unique=True,
                name="unique_retention_policy",
            ),
        ]


class TenantRetentionExecution(Document):
    tenant_id: PydanticObjectId
    policy_id: PydanticObjectId
    status: RetentionExecutionStatus = RetentionExecutionStatus.SCHEDULED
    scheduled_for: datetime
    executed_at: datetime | None = None
    detail: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_retention_executions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("scheduled_for", ASCENDING)], name="retention_exec_tenant"),
        ]


class TenantArchivalRecord(Document):
    tenant_id: PydanticObjectId
    offboarding_id: PydanticObjectId
    status: ArchivalStatus = ArchivalStatus.PENDING
    storage_key: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_archival_records"
        indexes = [IndexModel([("tenant_id", ASCENDING)], name="archival_tenant")]


class TenantDeletionRequest(Document):
    tenant_id: PydanticObjectId
    requested_by: PydanticObjectId
    status: DeletionRequestStatus = DeletionRequestStatus.PENDING_APPROVAL
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    reason: str = ""
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_deletion_requests"
        indexes = [IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="deletion_requests_tenant")]


class TenantDeletionManifest(Document):
    tenant_id: PydanticObjectId
    deletion_request_id: PydanticObjectId
    collections: list[dict[str, Any]] = Field(default_factory=list)
    records_removed: int = 0
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_deletion_manifests"
        indexes = [
            IndexModel([("deletion_request_id", ASCENDING)], unique=True, name="unique_deletion_manifest"),
        ]


class TenantLegalHold(Document):
    tenant_id: PydanticObjectId
    reference: str
    status: LegalHoldStatus = LegalHoldStatus.ACTIVE
    reason: str = ""
    placed_by: PydanticObjectId
    released_by: PydanticObjectId | None = None
    released_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_legal_holds"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="legal_holds_tenant_status"),
        ]


class TenantOffboardingRecord(Document):
    tenant_id: PydanticObjectId
    stage: OffboardingWorkflowStage = OffboardingWorkflowStage.OFFBOARDING_REQUESTED
    lifecycle_operation_id: PydanticObjectId | None = None
    export_request_id: PydanticObjectId | None = None
    archival_record_id: PydanticObjectId | None = None
    deletion_request_id: PydanticObjectId | None = None
    report: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)
    created_by: PydanticObjectId
    updated_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "tenant_offboarding_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_tenant_offboarding"),
        ]
