"""Faculty communication and notification collections."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class AnnouncementPublishEvent(BaseModel):
    published_at: datetime
    action: str
    note: str | None = None


class FacultyAnnouncement(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    course_code: str
    section: str | None = None
    title: str = Field(max_length=200)
    body: str = Field(max_length=8000)
    status: str = "draft"
    assignment_id: str | None = None
    withdrawn_at: datetime | None = None
    publish_history: list[AnnouncementPublishEvent] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_announcements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("status", ASCENDING)],
                name="announcements_by_faculty",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("course_code", ASCENDING), ("section", ASCENDING)],
                name="announcements_by_course",
            ),
        ]


class AcademicMessage(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    course_code: str
    section: str | None = None
    subject: str = Field(max_length=200)
    body: str = Field(max_length=4000)
    related_announcement_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "academic_messages"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="messages_by_faculty",
            ),
        ]


class CommunicationRecipient(Document):
    tenant_id: PydanticObjectId
    announcement_id: PydanticObjectId
    student_user_id: PydanticObjectId
    course_code: str
    section: str
    delivery_status: str = "queued"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "communication_recipients"
        indexes = [
            IndexModel(
                [("announcement_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_recipient_per_announcement",
            ),
        ]


class FacultyNotificationPreferences(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    email_enabled: bool = True
    push_enabled: bool = False
    digest_only: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_notification_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_notification_prefs",
            ),
        ]


class FacultyNotificationDeliveryLog(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    channel: str
    template: str
    status: str = "pending"
    error: str | None = None
    payload_ref: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_notification_delivery_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="delivery_logs_by_user",
            ),
        ]
