"""College admin reports and analytics collections."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class ReportJobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class InstitutionReportDefinition(Document):
    tenant_id: PydanticObjectId
    report_key: str
    title: str
    required_permission: str
    description: str | None = None
    supports_schedule: bool = True
    data_classification: str = "internal"
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_report_definitions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("report_key", ASCENDING)], unique=True, name="unique_report_definition"),
        ]


class InstitutionReportFilter(Document):
    tenant_id: PydanticObjectId
    filter_id: str
    report_key: str
    department_id: PydanticObjectId | None = None
    campus_id: PydanticObjectId | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    academic_year_label: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    owner_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_report_filters"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("filter_id", ASCENDING)], unique=True, name="unique_report_filter"),
        ]


class InstitutionReportJob(Document):
    tenant_id: PydanticObjectId
    job_id: str
    report_key: str
    filter_id: str | None = None
    status: ReportJobStatus = ReportJobStatus.PENDING
    error_message: str | None = None
    snapshot_id: str | None = None
    schedule_cron: str | None = None
    next_run_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "institution_report_jobs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("job_id", ASCENDING)], unique=True, name="unique_report_job"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)], name="report_jobs_by_status"),
        ]


class InstitutionReportExport(Document):
    tenant_id: PydanticObjectId
    export_id: str
    job_id: str
    format: str = "json"
    storage_key: str | None = None
    download_token_hash: str | None = None
    expires_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_report_exports"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("export_id", ASCENDING)], unique=True, name="unique_report_export"),
        ]


class InstitutionAnalyticsSnapshot(Document):
    tenant_id: PydanticObjectId
    snapshot_id: str
    report_key: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=utcnow)
    generated_by: PydanticObjectId | None = None

    class Settings:
        name = "institution_analytics_snapshots"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("snapshot_id", ASCENDING)], unique=True, name="unique_analytics_snapshot"),
            IndexModel([("tenant_id", ASCENDING), ("report_key", ASCENDING), ("generated_at", DESCENDING)], name="snapshots_by_report"),
        ]


class InstitutionReportAccessLog(Document):
    tenant_id: PydanticObjectId
    report_key: str
    action: str
    resource_id: str | None = None
    actor_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_report_access_logs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="report_access_logs"),
        ]