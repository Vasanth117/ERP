"""Examination report API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.examinations.exam_cell_enums import ExamSessionType


class ExamReportCatalogItem(BaseModel):
    report_type: str
    name: str
    description: str
    category: str
    supported_formats: list[str]
    sensitive: bool = False


class ExamReportFilters(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None
    exam_session_id: str | None = None
    programme_code: str | None = None
    department_code: str | None = None
    course_code: str | None = None
    examination_type: ExamSessionType | None = None
    date_from: date | None = None
    date_to: date | None = None


class ExamReportDataRead(BaseModel):
    report_type: str
    filters: ExamReportFilters
    row_count: int
    totals: dict[str, Any] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime


class ExamReportGenerateBody(BaseModel):
    report_type: str
    filters: ExamReportFilters = Field(default_factory=ExamReportFilters)
    output_format: str = "json"
    idempotency_key: str | None = Field(default=None, max_length=80)


class ExamReportJobRead(BaseModel):
    job_id: str
    report_type: str
    output_format: str
    status: str
    row_count: int
    filters: dict[str, Any]
    expires_at: datetime
    created_at: datetime
    completed_at: datetime | None
    has_download: bool
    error_message: str | None


class ExamReportDownloadRead(BaseModel):
    job_id: str
    report_type: str
    output_format: str
    file_content_base64: str