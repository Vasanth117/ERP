"""Hostel announcements, templates and delivery tracking."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HostelAnnouncementStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    ARCHIVED = "archived"


class HostelNotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class HostelNotificationDeliveryStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"


class HostelNotificationTemplate(Document):
    tenant_id: PydanticObjectId
    template_code: str = Field(max_length=64)
    category: str = Field(max_length=64)
    title_pattern: str = Field(max_length=200)
    body_pattern: str = Field(max_length=8000)
    default_channels: list[str] = Field(default_factory=lambda: ["in_app"])
    variables: list[str] = Field(default_factory=list)
    requires_acknowledgement: bool = False
    is_active: bool = True
    actor_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_notification_templates"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("template_code", ASCENDING)], unique=True, name="unique_hostel_notify_template"),
        ]


class HostelAnnouncement(Document):
    tenant_id: PydanticObjectId
    announcement_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    body: str = Field(max_length=8000)
    category: str = Field(max_length=64)
    priority: HostelNotificationPriority = HostelNotificationPriority.NORMAL
    audience: dict[str, Any] = Field(default_factory=dict)
    audience_preview_count: int = 0
    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    document_refs: list[str] = Field(default_factory=list)
    hostel_code: str | None = None
    publish_at: datetime | None = None
    expires_at: datetime | None = None
    requires_acknowledgement: bool = False
    requires_action: bool = False
    status: HostelAnnouncementStatus = HostelAnnouncementStatus.DRAFT
    reviewer_id: PydanticObjectId | None = None
    published_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_announcements"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("announcement_code", ASCENDING)], unique=True, name="unique_hostel_announcement"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="hostel_announcements_status"),
        ]


class HostelAnnouncementAudience(Document):
    tenant_id: PydanticObjectId
    announcement_code: str
    student_user_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_announcement_audience"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("announcement_code", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_hostel_announcement_audience",
            ),
        ]


class HostelAnnouncementAcknowledgement(Document):
    tenant_id: PydanticObjectId
    announcement_code: str
    student_user_id: PydanticObjectId
    acknowledged_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_announcement_acknowledgements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("announcement_code", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_hostel_announcement_ack",
            ),
        ]


class HostelNotificationDeliveryHistory(Document):
    tenant_id: PydanticObjectId
    notification_id: str = Field(max_length=64)
    dedupe_key: str = Field(max_length=128)
    category: str = Field(max_length=64)
    channel: str = Field(max_length=32)
    recipient_user_id: PydanticObjectId
    title: str = Field(max_length=200)
    body: str = Field(max_length=8000)
    status: HostelNotificationDeliveryStatus = HostelNotificationDeliveryStatus.QUEUED
    priority: HostelNotificationPriority = HostelNotificationPriority.NORMAL
    requires_acknowledgement: bool = False
    requires_action: bool = False
    read_at: datetime | None = None
    acknowledged_at: datetime | None = None
    failed_reason: str | None = Field(default=None, max_length=2000)
    source_type: str = Field(default="broadcast", max_length=32)
    source_id: str | None = None
    related_record_type: str | None = None
    related_record_id: str | None = None
    outbox_idempotency_key: str | None = None
    sender_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_notification_delivery_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("dedupe_key", ASCENDING)], unique=True, name="unique_hostel_notify_dedupe"),
            IndexModel(
                [("tenant_id", ASCENDING), ("recipient_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="hostel_notify_by_recipient",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="hostel_notify_by_status"),
        ]