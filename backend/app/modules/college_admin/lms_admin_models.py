"""College admin LMS administration collections."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class LmsAccessPolicy(str, Enum):
    ENROLLED_ONLY = "enrolled_only"
    DEPARTMENT = "department"
    INSTITUTION = "institution"


class InstitutionLmsSettings(Document):
    tenant_id: PydanticObjectId
    settings_id: str = "default"
    default_access: LmsAccessPolicy = LmsAccessPolicy.ENROLLED_ONLY
    allowed_material_types: list[str] = Field(default_factory=lambda: ["document", "video", "link"])
    assignment_late_penalty_cap: float = Field(default=100, ge=0, le=100)
    quiz_enabled: bool = True
    moderation_required: bool = False
    integration_provider_code: str | None = None
    version: int = 1
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_lms_settings"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("settings_id", ASCENDING)], unique=True, name="unique_lms_settings"),
        ]


class LmsCourseMapping(Document):
    tenant_id: PydanticObjectId
    course_id: str
    course_code: str
    lms_course_key: str
    department_id: PydanticObjectId | None = None
    published: bool = True
    actor_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "lms_course_mappings"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("course_code", ASCENDING)], unique=True, name="unique_lms_course_mapping"),
        ]


class LmsContentCategory(Document):
    tenant_id: PydanticObjectId
    category_code: str
    title: str
    parent_code: str | None = None
    sort_order: int = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "lms_content_categories"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("category_code", ASCENDING)], unique=True, name="unique_lms_category"),
        ]


class LmsPublishingPolicy(Document):
    tenant_id: PydanticObjectId
    policy_code: str
    material_requires_approval: bool = False
    assignment_publish_window_hours: int = Field(default=168, ge=0)
    rules: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "lms_publishing_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_code", ASCENDING)], unique=True, name="unique_lms_publish_policy"),
        ]


class LmsReportExportFormat(str, Enum):
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


class LmsScheduledReportFrequency(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class LmsScheduledReport(Document):
    tenant_id: PydanticObjectId
    schedule_code: str = Field(max_length=64)
    report_key: str = Field(max_length=64)
    title: str = Field(max_length=200)
    export_formats: list[str] = Field(default_factory=list)
    frequency: LmsScheduledReportFrequency = LmsScheduledReportFrequency.MONTHLY
    filters: dict[str, Any] = Field(default_factory=dict)
    last_run_at: datetime | None = None
    is_active: bool = True
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "lms_scheduled_reports"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("schedule_code", ASCENDING)],
                unique=True,
                name="unique_lms_scheduled_report",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("report_key", ASCENDING), ("is_active", ASCENDING)],
                name="lms_scheduled_report_key",
            ),
        ]


class LmsConfigurationHistory(Document):
    tenant_id: PydanticObjectId
    scope: str
    resource_id: str
    version_number: int
    snapshot: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "lms_configuration_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="lms_config_history_recent"),
        ]