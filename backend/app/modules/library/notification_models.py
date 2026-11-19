"""Library notifications, deliveries, preferences and announcements."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class LibraryNotification(Document):
    tenant_id: PydanticObjectId
    notification_id: str
    event_type: str
    recipient_user_id: PydanticObjectId
    branch_code: str | None = None
    title: str = Field(max_length=200)
    body: str = Field(max_length=4000)
    reference_type: str | None = None
    reference_id: str | None = None
    dedupe_key: str = Field(max_length=160)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_notifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("notification_id", ASCENDING)],
                unique=True,
                name="unique_library_notification",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("dedupe_key", ASCENDING)],
                unique=True,
                name="unique_library_notification_dedupe",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("recipient_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="library_notifications_recipient",
            ),
            IndexModel([("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("created_at", DESCENDING)], name="library_notifications_branch"),
        ]


class LibraryNotificationDelivery(Document):
    tenant_id: PydanticObjectId
    delivery_id: str
    notification_id: str
    channel: str
    status: str = "queued"
    retry_count: int = 0
    error: str | None = None
    outbox_event_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_notification_deliveries"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("delivery_id", ASCENDING)],
                unique=True,
                name="unique_library_notification_delivery",
            ),
            IndexModel([("tenant_id", ASCENDING), ("notification_id", ASCENDING)], name="library_delivery_by_notification"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="library_delivery_by_status"),
        ]


class LibraryNotificationPreference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    in_app_enabled: bool = True
    email_enabled: bool = True
    issue_enabled: bool = True
    due_reminder_enabled: bool = True
    overdue_enabled: bool = True
    reservation_enabled: bool = True
    fine_enabled: bool = True
    membership_enabled: bool = True
    announcement_enabled: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_notification_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_library_notification_prefs",
            ),
        ]


class LibraryAnnouncement(Document):
    tenant_id: PydanticObjectId
    announcement_id: str
    branch_code: str | None = None
    title: str = Field(max_length=200)
    body: str = Field(max_length=8000)
    status: str = "draft"
    published_at: datetime | None = None
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_announcements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("announcement_id", ASCENDING)],
                unique=True,
                name="unique_library_announcement",
            ),
            IndexModel([("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("status", ASCENDING)], name="library_announcements_branch"),
        ]