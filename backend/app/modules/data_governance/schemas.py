"""Data governance API schemas."""

from datetime import datetime
from typing import Any

from beanie import PydanticObjectId
from pydantic import BaseModel, Field, field_validator

from app.modules.data_governance.enums import (
    ExportFormat,
    ExportRequestStatus,
    OffboardingWorkflowStage,
)
from app.modules.data_governance.models import (
    TenantExportArtifact,
    TenantExportDownload,
    TenantExportJob,
    TenantExportRequest,
    TenantOffboardingRecord,
    TenantRetentionPolicy,
)


class ExportRequestCreate(BaseModel):
    formats: list[ExportFormat] = Field(default_factory=lambda: [ExportFormat.JSON])
    module_scopes: list[str] = Field(default_factory=list)
    include_document_metadata: bool = False
    include_sensitive: bool = False
    idempotency_key: str | None = None

    @field_validator("module_scopes")
    @classmethod
    def non_empty_modules(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("At least one export module is required")
        return value


class ExportReviewRequest(BaseModel):
    approved: bool
    note: str | None = None


class ExportRequestRead(BaseModel):
    id: str
    tenant_id: str
    status: ExportRequestStatus
    formats: list[ExportFormat]
    module_scopes: list[str]
    include_document_metadata: bool
    include_sensitive: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_document(cls, doc: TenantExportRequest) -> "ExportRequestRead":
        return cls(
            id=str(doc.id),
            tenant_id=str(doc.tenant_id),
            status=doc.status,
            formats=doc.formats,
            module_scopes=doc.module_scopes,
            include_document_metadata=doc.include_document_metadata,
            include_sensitive=doc.include_sensitive,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


class ExportJobRead(BaseModel):
    id: str
    request_id: str
    status: str
    progress_percent: int
    last_error: str | None

    @classmethod
    def from_document(cls, doc: TenantExportJob) -> "ExportJobRead":
        return cls(
            id=str(doc.id),
            request_id=str(doc.request_id),
            status=doc.status.value,
            progress_percent=doc.progress_percent,
            last_error=doc.last_error,
        )


class ExportArtifactRead(BaseModel):
    id: str
    format: ExportFormat
    byte_size: int
    validated: bool
    checksum_sha256: str | None

    @classmethod
    def from_document(cls, doc: TenantExportArtifact) -> "ExportArtifactRead":
        return cls(
            id=str(doc.id),
            format=doc.format,
            byte_size=doc.byte_size,
            validated=doc.validated,
            checksum_sha256=doc.checksum_sha256,
        )


class ExportDownloadIssueResponse(BaseModel):
    download_id: str
    token: str
    signature: str
    expires_at: datetime
    artifact_id: str


class RetentionPolicyRead(BaseModel):
    id: str
    tenant_id: str | None
    name: str
    retention_days: int
    post_offboarding_days: int
    allow_deletion: bool

    @classmethod
    def from_document(cls, doc: TenantRetentionPolicy) -> "RetentionPolicyRead":
        return cls(
            id=str(doc.id),
            tenant_id=str(doc.tenant_id) if doc.tenant_id else None,
            name=doc.name,
            retention_days=doc.retention_days,
            post_offboarding_days=doc.post_offboarding_days,
            allow_deletion=doc.allow_deletion,
        )


class RetentionPolicyUpdate(BaseModel):
    retention_days: int | None = Field(default=None, ge=1, le=3650)
    post_offboarding_days: int | None = Field(default=None, ge=0, le=3650)
    allow_deletion: bool | None = None


class OffboardingInitiate(BaseModel):
    reason: str = ""
    require_export: bool = True


class OffboardingRead(BaseModel):
    id: str
    tenant_id: str
    stage: OffboardingWorkflowStage
    history: list[dict[str, Any]]

    @classmethod
    def from_document(cls, doc: TenantOffboardingRecord) -> "OffboardingRead":
        return cls(
            id=str(doc.id),
            tenant_id=str(doc.tenant_id),
            stage=doc.stage,
            history=doc.history,
        )


class LegalHoldCreate(BaseModel):
    reference: str
    reason: str = ""


class DeletionRequestCreate(BaseModel):
    reason: str = ""


class DeletionManifestRead(BaseModel):
    id: str
    tenant_id: str
    collections: list[dict[str, Any]]
    records_removed: int
    completed_at: datetime | None
