"""Reports and analytics API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.modules.college_admin.reports_admin_models import ReportJobStatus


class ReportFilterCreate(BaseModel):
    filter_id: str
    report_key: str
    department_id: str | None = None
    campus_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    academic_year_label: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_dates(self) -> "ReportFilterCreate":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be before date_to")
        return self


class ReportFilterRead(BaseModel):
    filter_id: str
    report_key: str
    department_id: str | None
    campus_id: str | None
    date_from: datetime | None
    date_to: datetime | None
    academic_year_label: str | None


class ReportDefinitionUpsert(BaseModel):
    report_key: str
    title: str
    required_permission: str
    description: str | None = None
    supports_schedule: bool = True
    data_classification: str = "internal"


class ReportDefinitionRead(BaseModel):
    report_key: str
    title: str
    required_permission: str
    description: str | None
    supports_schedule: bool
    data_classification: str


class ReportGenerateRequest(BaseModel):
    report_key: str
    filter_id: str | None = None
    department_id: str | None = None
    campus_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    academic_year_label: str | None = None


class ReportJobRead(BaseModel):
    job_id: str
    report_key: str
    filter_id: str | None
    status: ReportJobStatus
    error_message: str | None
    snapshot_id: str | None
    schedule_cron: str | None
    next_run_at: datetime | None
    created_at: datetime
    completed_at: datetime | None


class ReportScheduleRequest(BaseModel):
    report_key: str
    filter_id: str | None = None
    schedule_cron: str = Field(min_length=5, max_length=120)


class AnalyticsSnapshotRead(BaseModel):
    snapshot_id: str
    report_key: str
    metrics: dict[str, Any]
    filters: dict[str, Any]
    generated_at: datetime


class DashboardAnalyticsRead(BaseModel):
    academic_year_label: str
    semester_label: str
    headcount: dict[str, Any]
    attendance: dict[str, Any]
    finance_summary: dict[str, Any] | None = None
    lms_engagement: dict[str, Any] | None = None
    pending_approvals: int


class ReportExportCreate(BaseModel):
    job_id: str
    format: str = "json"


class ReportExportRead(BaseModel):
    export_id: str
    job_id: str
    format: str
    download_token: str | None = None
    expires_at: datetime | None


class ReportAccessLogRead(BaseModel):
    report_key: str
    action: str
    resource_id: str | None
    created_at: datetime