"""HR reports & analytics API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrReportExportFormat, HrScheduledReportFrequency
from app.modules.hr.hr_reports_models import HrReportExecutionHistory, HrSavedReport, HrScheduledReport


class HrAnalyticsDashboard(BaseModel):
    workforce_size: int = 0
    active_employees: int = 0
    pending_leaves: int = 0
    pending_claims: int = 0
    open_payroll_runs: int = 0
    pending_reviews: int = 0
    training_in_progress: int = 0
    recruitment_applications: int = 0
    comparisons: dict[str, Any] = Field(default_factory=dict)


class ReportCatalogItemRead(BaseModel):
    report_key: str
    title: str
    category: str
    supported_formats: list[str]


class ReportRunRequest(BaseModel):
    report_key: str
    filters: dict[str, Any] = Field(default_factory=dict)


class ReportDataRead(BaseModel):
    report_key: str
    row_count: int
    totals: dict[str, Any] = Field(default_factory=dict)
    rows: list[dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime


class ReportExportRequest(BaseModel):
    report_key: str
    export_format: HrReportExportFormat = HrReportExportFormat.CSV
    filters: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None


class ReportExportRead(BaseModel):
    execution_id: str
    report_key: str
    status: str
    row_count: int
    has_download: bool

    @classmethod
    def from_doc(cls, doc: HrReportExecutionHistory) -> "ReportExportRead":
        return cls(
            execution_id=str(doc.id),
            report_key=doc.report_key,
            status=doc.status,
            row_count=doc.row_count,
            has_download=bool(doc.file_content_base64),
        )


class SavedReportUpsert(BaseModel):
    report_key: str
    name: str
    selected_fields: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    group_by: str | None = None
    sort_by: str | None = None


class SavedReportRead(BaseModel):
    id: str
    report_key: str
    name: str

    @classmethod
    def from_doc(cls, doc: HrSavedReport) -> "SavedReportRead":
        return cls(id=str(doc.id), report_key=doc.report_key, name=doc.name)


class ScheduledReportUpsert(BaseModel):
    schedule_code: str
    report_key: str
    saved_report_id: str | None = None
    frequency: HrScheduledReportFrequency = HrScheduledReportFrequency.MONTHLY
    filters: dict[str, Any] = Field(default_factory=dict)
    export_format: HrReportExportFormat = HrReportExportFormat.CSV
    recipient_user_ids: list[str] = Field(default_factory=list)
    delivery_channel: str = "email"


class ScheduledReportRead(BaseModel):
    id: str
    schedule_code: str
    report_key: str
    is_active: bool

    @classmethod
    def from_doc(cls, doc: HrScheduledReport) -> "ScheduledReportRead":
        return cls(id=str(doc.id), schedule_code=doc.schedule_code, report_key=doc.report_key, is_active=doc.is_active)