"""College admin communication administration collections."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class AnnouncementAudience(str, Enum):
    ALL = "all"
    STUDENTS = "students"
    FACULTY = "faculty"
    DEPARTMENT = "department"
    CUSTOM = "custom"


class DeliveryStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


class InstitutionAnnouncement(Document):
    tenant_id: PydanticObjectId
    announcement_id: str
    title: str = Field(max_length=200)
    body: str = Field(max_length=16000)
    audience: AnnouncementAudience = AnnouncementAudience.ALL
    department_id: PydanticObjectId | None = None
    audience_group_id: str | None = None
    status: str = "draft"
    scheduled_for: datetime | None = None
    published_at: datetime | None = None
    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_announcements"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("announcement_id", ASCENDING)], unique=True, name="unique_institution_announcement"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("scheduled_for", ASCENDING)], name="announcements_by_schedule"),
        ]


class CommunicationTemplate(Document):
    tenant_id: PydanticObjectId
    template_code: str
    channel: str
    subject: str | None = None
    body: str
    version: int = 1
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "communication_templates"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("template_code", ASCENDING), ("channel", ASCENDING)], unique=True, name="unique_comm_template"),
        ]


class CommunicationAudienceGroup(Document):
    tenant_id: PydanticObjectId
    group_id: str
    name: str
    member_user_ids: list[PydanticObjectId] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "communication_audience_groups"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("group_id", ASCENDING)], unique=True, name="unique_audience_group"),
        ]


class CommunicationDeliveryLog(Document):
    tenant_id: PydanticObjectId
    log_id: str
    announcement_id: str
    channel: str
    recipient_user_id: PydanticObjectId | None = None
    status: DeliveryStatus = DeliveryStatus.QUEUED
    error: str | None = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "communication_delivery_logs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("log_id", ASCENDING)], unique=True, name="unique_delivery_log"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="delivery_by_status"),
        ]


class CommunicationSchedule(Document):
    tenant_id: PydanticObjectId
    schedule_id: str
    announcement_id: str
    run_at: datetime
    executed: bool = False
    executed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "communication_schedules"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("schedule_id", ASCENDING)], unique=True, name="unique_comm_schedule"),
        ]


class CommunicationProviderSettings(Document):
    tenant_id: PydanticObjectId
    channel: str
    provider_name: str
    credential_ref: str
    config: dict[str, Any] = Field(default_factory=dict)
    push_enabled: bool = False
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "communication_provider_settings"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("channel", ASCENDING)], unique=True, name="unique_provider_channel"),
        ]