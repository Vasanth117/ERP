"""Import and migration API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.college_admin.import_admin_models import ImportEntityType, ImportJobStatus


class ImportUploadRequest(BaseModel):
    template_id: str
    file_name: str
    content_base64: str = Field(min_length=16)
    idempotency_key: str = Field(min_length=8, max_length=64)


class ImportTemplateRead(BaseModel):
    template_id: str
    entity_type: ImportEntityType
    title: str
    version: int
    required_columns: list[str]
    optional_columns: list[str]
    max_rows: int
    requires_approval: bool


class ImportMappingUpsert(BaseModel):
    mapping_id: str
    template_id: str
    column_map: dict[str, str]
    duplicate_key_field: str | None = None


class ImportMappingRead(BaseModel):
    mapping_id: str
    template_id: str
    column_map: dict[str, str]
    duplicate_key_field: str | None


class ImportJobRead(BaseModel):
    job_id: str
    template_id: str
    entity_type: ImportEntityType
    status: ImportJobStatus
    file_name: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    executed_rows: int
    failed_rows: int
    progress_percent: float
    requires_approval: bool
    approved_at: datetime | None
    created_at: datetime
    completed_at: datetime | None


class ImportValidationReport(BaseModel):
    job_id: str
    valid_rows: int
    invalid_rows: int
    duplicate_rows: int
    errors: list[dict[str, Any]]


class ImportPreviewRead(BaseModel):
    job_id: str
    preview_rows: list[dict[str, Any]]
    truncated: bool


class ImportApproveRequest(BaseModel):
    authorized: bool = True


class MigrationHistoryItem(BaseModel):
    migration_id: str
    job_id: str
    action: str
    summary: str
    created_at: datetime


class ImportErrorReportRead(BaseModel):
    job_id: str
    download_token: str | None
    expires_at: datetime | None