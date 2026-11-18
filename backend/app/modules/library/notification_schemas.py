"""Library notification API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class LibraryNotificationRead(BaseModel):
    notification_id: str
    event_type: str
    recipient_user_id: str
    branch_code: str | None
    title: str
    body: str
    reference_type: str | None
    reference_id: str | None
    created_at: datetime

    @classmethod
    def model_validate(cls, obj, **kwargs):  # type: ignore[override]
        if hasattr(obj, "recipient_user_id"):
            data = {
                "notification_id": obj.notification_id,
                "event_type": obj.event_type,
                "recipient_user_id": str(obj.recipient_user_id),
                "branch_code": obj.branch_code,
                "title": obj.title,
                "body": obj.body,
                "reference_type": obj.reference_type,
                "reference_id": obj.reference_id,
                "created_at": obj.created_at,
            }
            return cls(**data)
        return super().model_validate(obj, **kwargs)


class NotificationDeliveryRead(BaseModel):
    delivery_id: str
    notification_id: str
    channel: str
    status: str
    retry_count: int
    error: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LibraryNotificationPreferenceRead(BaseModel):
    in_app_enabled: bool
    email_enabled: bool
    issue_enabled: bool
    due_reminder_enabled: bool
    overdue_enabled: bool
    reservation_enabled: bool
    fine_enabled: bool
    membership_enabled: bool
    announcement_enabled: bool

    model_config = {"from_attributes": True}


class LibraryNotificationPreferenceUpdate(BaseModel):
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    issue_enabled: bool | None = None
    due_reminder_enabled: bool | None = None
    overdue_enabled: bool | None = None
    reservation_enabled: bool | None = None
    fine_enabled: bool | None = None
    membership_enabled: bool | None = None
    announcement_enabled: bool | None = None

    model_config = {"extra": "forbid"}


class ManualNotificationRequest(BaseModel):
    recipient_user_id: str
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=4000)
    branch_code: str | None = None
    dedupe_key: str | None = Field(default=None, max_length=160)


class LibraryAnnouncementCreate(BaseModel):
    announcement_id: str | None = Field(default=None, max_length=64)
    branch_code: str | None = None
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=8000)


class LibraryAnnouncementRead(BaseModel):
    announcement_id: str
    branch_code: str | None
    title: str
    body: str
    status: str
    published_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}