"""HR announcements, templates, preferences and per-recipient delivery."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import (
    HrAnnouncementStatus,
    HrNotificationDeliveryStatus,
    HrNotificationPriority,
)


class HrNotificationTemplate(Document):
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
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_notification_templates"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("template_code", ASCENDING)], unique=True, name="unique_hr_notify_template"),
        ]


class HrAnnouncement(Document):
    tenant_id: PydanticObjectId
    announcement_code: str = Field(max_length=64)
    title: str = Field(max_length=200)
    body: str = Field(max_length=8000)
    category: str = Field(max_length=64)
    priority: HrNotificationPriority = HrNotificationPriority.NORMAL
    audience: dict[str, Any] = Field(default_factory=dict)
    audience_preview_count: int = 0
    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    document_refs: list[str] = Field(default_factory=list)
    publish_at: datetime | None = None
    expires_at: datetime | None = None
    pinned: bool = False
    requires_acknowledgement: bool = False
    status: HrAnnouncementStatus = HrAnnouncementStatus.DRAFT
    reviewer_id: PydanticObjectId | None = None
    published_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_announcements"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("announcement_code", ASCENDING)], unique=True, name="unique_hr_announcement"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="hr_announcements_status"),
        ]


class HrAnnouncementAudience(Document):
    """Resolved audience snapshot for a published announcement."""

    tenant_id: PydanticObjectId
    announcement_id: PydanticObjectId
    employee_user_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_announcement_audience"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("announcement_id", ASCENDING), ("employee_user_id", ASCENDING)],
                unique=True,
                name="unique_announcement_audience_member",
            ),
        ]


class HrNotificationPreference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    channels_enabled: dict[str, bool] = Field(default_factory=lambda: {"in_app": True, "email": True})
    categories_muted: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_notification_preferences"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("user_id", ASCENDING)], unique=True, name="unique_hr_notify_pref"),
        ]


class HrNotificationDeliveryHistory(Document):
    tenant_id: PydanticObjectId
    notification_id: str = Field(max_length=64)
    dedupe_key: str = Field(max_length=128)
    category: str = Field(max_length=64)
    channel: str = Field(max_length=32)
    recipient_user_id: PydanticObjectId
    title: str = Field(max_length=200)
    body: str = Field(max_length=8000)
    status: HrNotificationDeliveryStatus = HrNotificationDeliveryStatus.QUEUED
    priority: HrNotificationPriority = HrNotificationPriority.NORMAL
    requires_acknowledgement: bool = False
    read_at: datetime | None = None
    acknowledged_at: datetime | None = None
    failed_reason: str | None = Field(default=None, max_length=2000)
    source_type: str = Field(default="broadcast", max_length=32)
    source_id: str | None = None
    outbox_idempotency_key: str | None = None
    sender_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_notification_delivery_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("dedupe_key", ASCENDING)], unique=True, name="unique_hr_notify_dedupe"),
            IndexModel(
                [("tenant_id", ASCENDING), ("recipient_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="hr_notify_by_recipient",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="hr_notify_by_status"),
        ]