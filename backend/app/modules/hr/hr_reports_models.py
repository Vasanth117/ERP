"""HR saved and scheduled reports."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import HrReportExportFormat, HrScheduledReportFrequency


class HrSavedReport(Document):
    tenant_id: PydanticObjectId
    report_key: str = Field(max_length=64)
    name: str = Field(max_length=200)
    selected_fields: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    group_by: str | None = None
    sort_by: str | None = None
    owner_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_saved_reports"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("owner_id", ASCENDING), ("name", ASCENDING)], name="hr_saved_reports_owner"),
        ]


class HrScheduledReport(Document):
    tenant_id: PydanticObjectId
    schedule_code: str = Field(max_length=64)
    report_key: str = Field(max_length=64)
    saved_report_id: PydanticObjectId | None = None
    frequency: HrScheduledReportFrequency = HrScheduledReportFrequency.MONTHLY
    filters: dict[str, Any] = Field(default_factory=dict)
    export_format: HrReportExportFormat = HrReportExportFormat.CSV
    recipient_user_ids: list[PydanticObjectId] = Field(default_factory=list)
    delivery_channel: str = "email"
    next_run_at: datetime | None = None
    last_run_at: datetime | None = None
    last_status: str = "pending"
    is_active: bool = True
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_scheduled_reports"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("schedule_code", ASCENDING)], unique=True, name="unique_hr_scheduled_report"),
            IndexModel([("tenant_id", ASCENDING), ("is_active", ASCENDING), ("next_run_at", ASCENDING)], name="hr_scheduled_due"),
        ]


class HrReportExecutionHistory(Document):
    tenant_id: PydanticObjectId
    report_key: str = Field(max_length=64)
    saved_report_id: PydanticObjectId | None = None
    scheduled_report_id: PydanticObjectId | None = None
    export_format: HrReportExportFormat = HrReportExportFormat.CSV
    status: str = "completed"
    row_count: int = 0
    filters: dict[str, Any] = Field(default_factory=dict)
    file_content_base64: str | None = None
    error_message: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "hr_report_execution_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("report_key", ASCENDING), ("created_at", DESCENDING)], name="hr_report_exec_history"),
        ]