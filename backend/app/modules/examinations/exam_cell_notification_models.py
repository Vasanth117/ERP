"""Examination notification templates, events, delivery logs and announcements."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class ExamNotificationTemplate(Document):
    """Tenant templates or per-user delivery preferences (when user_id is set)."""

    tenant_id: PydanticObjectId
    template_id: str
    event_type: str
    user_id: PydanticObjectId | None = None
    title_template: str = Field(max_length=300)
    body_template: str = Field(max_length=4000)
    in_app_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    is_active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_notification_templates"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("template_id", ASCENDING)],
                unique=True,
                name="unique_exam_notification_template",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("event_type", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_exam_template_or_pref",
            ),
        ]


class ExamNotificationEventRecord(Document):
    tenant_id: PydanticObjectId
    event_record_id: str
    event_type: str
    recipient_user_id: PydanticObjectId
    title: str = Field(max_length=300)
    body: str = Field(max_length=4000)
    exam_session_id: PydanticObjectId | None = None
    restricted: bool = False
    reference_type: str | None = None
    reference_id: str | None = None
    dedupe_key: str = Field(max_length=160)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_notification_events"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("event_record_id", ASCENDING)],
                unique=True,
                name="unique_exam_notification_event",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("dedupe_key", ASCENDING)],
                unique=True,
                name="unique_exam_notification_dedupe",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("recipient_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_notification_by_recipient",
            ),
        ]


class ExamNotificationDeliveryLog(Document):
    tenant_id: PydanticObjectId
    delivery_id: str
    event_record_id: str
    channel: str
    status: str = "queued"
    retry_count: int = 0
    error: str | None = None
    outbox_event_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_notification_delivery_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("delivery_id", ASCENDING)],
                unique=True,
                name="unique_exam_notification_delivery",
            ),
            IndexModel([("tenant_id", ASCENDING), ("event_record_id", ASCENDING)], name="exam_delivery_by_event"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="exam_delivery_by_status"),
        ]


class ExamAnnouncementRecord(Document):
    tenant_id: PydanticObjectId
    announcement_id: str
    title: str = Field(max_length=300)
    body: str = Field(max_length=8000)
    audience: str
    exam_session_id: PydanticObjectId | None = None
    recipient_user_ids: list[PydanticObjectId] = Field(default_factory=list)
    published: bool = False
    published_at: datetime | None = None
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_announcement_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("announcement_id", ASCENDING)],
                unique=True,
                name="unique_exam_announcement",
            ),
            IndexModel([("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("published", ASCENDING)], name="exam_announcements_session"),
        ]