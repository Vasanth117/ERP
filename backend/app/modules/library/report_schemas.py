"""Library reports API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class LibraryReportFilters(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    branch_code: str | None = None
    category: str | None = None
    member_category: str | None = None
    status: str | None = None


class LibraryReportCatalogItem(BaseModel):
    report_type: str
    name: str
    description: str
    category: str
    supported_formats: list[str]
    requires_finance_permission: bool = False


class LibraryReportDataRead(BaseModel):
    report_type: str
    filters: LibraryReportFilters
    row_count: int
    totals: dict[str, Any] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime


class LibraryReportGenerateBody(BaseModel):
    report_type: str = Field(min_length=2, max_length=64)
    filters: LibraryReportFilters = Field(default_factory=LibraryReportFilters)
    output_format: str = Field(default="json", pattern="^(json|csv)$")
    idempotency_key: str | None = Field(default=None, max_length=128)


class LibraryReportJobRead(BaseModel):
    job_id: str
    report_type: str
    output_format: str
    status: str
    row_count: int
    filters: dict[str, Any]
    expires_at: datetime | None
    created_at: datetime
    completed_at: datetime | None
    has_download: bool
    error_message: str | None = None


class LibraryReportDownloadRead(BaseModel):
    job_id: str
    content_type: str
    file_name: str
    content_base64: str | None
    row_count: int