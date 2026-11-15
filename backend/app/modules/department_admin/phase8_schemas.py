"""Department Admin phase 8 — reports and data transfer."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.department_admin.models import (
    DepartmentDataTransferStatus,
    DepartmentReportJobStatus,
)


class ReportFilters(BaseModel):
    academic_year_label: str | None = Field(default=None, max_length=32)
    semester_label: str | None = Field(default=None, max_length=32)
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    section_code: str | None = Field(default=None, max_length=16)
    course_code: str | None = Field(default=None, max_length=32)
    faculty_user_id: str | None = None
    status: str | None = Field(default=None, max_length=32)
    date_from: datetime | None = None
    date_to: datetime | None = None

    @field_validator("date_to")
    @classmethod
    def range_ok(cls, date_to: datetime | None, info) -> datetime | None:
        start = info.data.get("date_from")
        if start and date_to and start > date_to:
            raise ValueError("date_from must be on or before date_to")
        return date_to


class ReportCatalogItem(BaseModel):
    report_type: str
    name: str
    description: str
    category: str
    supported_formats: list[str]
    required_permission: str
    filter_fields: list[str]


class ReportsOverviewRead(BaseModel):
    catalogue_count: int
    recent_jobs: int
    pending_jobs: int
    categories: list[str]
    generated_at: datetime
    advisory: str


class ReportDataRead(BaseModel):
    report_type: str
    filters: ReportFilters
    generated_at: datetime
    row_count: int
    totals: dict = Field(default_factory=dict)
    rows: list[dict] = Field(default_factory=list)
    meta: dict = Field(default_factory=dict)


class ReportGenerateBody(BaseModel):
    report_type: str = Field(max_length=64)
    output_format: str = Field(default="json", pattern="^(json|csv)$")
    filters: ReportFilters = Field(default_factory=ReportFilters)
    idempotency_key: str | None = Field(default=None, max_length=128)
    async_large: bool = False


class ReportJobRead(BaseModel):
    job_id: str
    report_type: str
    output_format: str
    status: DepartmentReportJobStatus
    row_count: int
    filters: dict
    expires_at: datetime | None
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None = None
    has_download: bool = False


class ReportDownloadRead(BaseModel):
    job_id: str
    content_type: str
    file_name: str
    content_base64: str
    expires_at: datetime | None


class ImportTemplateRead(BaseModel):
    template_id: str
    entity_type: str
    version: str
    required_columns: list[str]
    optional_columns: list[str]
    max_rows: int
    description: str
    permission: str


class ExportDatasetRead(BaseModel):
    dataset_id: str
    description: str
    allowed_fields: list[str]
    default_fields: list[str]
    permission: str


class ImportUploadBody(BaseModel):
    template_id: str = Field(max_length=64)
    file_name: str = Field(max_length=256)
    file_content_base64: str
    idempotency_key: str | None = Field(default=None, max_length=128)


class DataTransferJobRead(BaseModel):
    job_id: str
    operation: str
    dataset_type: str
    template_version: str
    status: DepartmentDataTransferStatus
    file_name: str | None
    valid_row_count: int
    invalid_row_count: int
    executed_row_count: int
    validation_summary: dict
    expires_at: datetime | None
    created_at: datetime
    completed_at: datetime | None
    dry_run: bool
    has_download: bool = False


class ExportRequestBody(BaseModel):
    dataset_id: str = Field(max_length=64)
    output_format: str = Field(default="csv", pattern="^(csv|json)$")
    fields: list[str] = Field(default_factory=list)
    filters: ReportFilters = Field(default_factory=ReportFilters)
    idempotency_key: str | None = Field(default=None, max_length=128)


class DataTransferHistoryFilters(BaseModel):
    operation: str | None = Field(default=None, pattern="^(import|export)$")