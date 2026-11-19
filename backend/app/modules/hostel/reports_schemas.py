"""Hostel reports API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hostel.reports_models import HostelReportExportFormat, HostelScheduledReportFrequency


class ReportCatalogItemRead(BaseModel):
    report_key: str
    title: str
    category: str
    supported_formats: list[str]
    confidential: bool = False


class ReportRunRequest(BaseModel):
    report_key: str
    filters: dict[str, Any] = Field(default_factory=dict)


class ReportDataRead(BaseModel):
    report_key: str
    row_count: int
    rows: list[dict[str, Any]]


class ReportExportRequest(BaseModel):
    report_key: str
    filters: dict[str, Any] = Field(default_factory=dict)
    export_format: HostelReportExportFormat = HostelReportExportFormat.CSV


class ReportExportRead(BaseModel):
    execution_id: str
    report_key: str
    export_format: HostelReportExportFormat
    status: str
    row_count: int
    file_content_base64: str | None = None


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
    filters: dict[str, Any]


class ScheduledReportUpsert(BaseModel):
    schedule_code: str
    report_key: str
    saved_report_id: str | None = None
    frequency: HostelScheduledReportFrequency = HostelScheduledReportFrequency.MONTHLY
    filters: dict[str, Any] = Field(default_factory=dict)
    export_format: HostelReportExportFormat = HostelReportExportFormat.CSV
    recipient_user_ids: list[str] = Field(default_factory=list)
    delivery_channel: str = "email"
    is_active: bool = True


class ScheduledReportRead(BaseModel):
    schedule_code: str
    report_key: str
    frequency: HostelScheduledReportFrequency
    is_active: bool
    last_status: str


class HostelAnalyticsOverview(BaseModel):
    occupied_beds: int = 0
    available_beds: int = 0
    active_residents: int = 0
    open_complaints: int = 0
    visitors_inside: int = 0
    overdue_outpass: int = 0
    mess_enrollments_active: int = 0
    open_incidents: int = 0
    derived_estimate_note: str = "Trend metrics require sufficient history; counts are point-in-time actuals."