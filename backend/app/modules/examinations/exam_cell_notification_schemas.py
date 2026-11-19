"""Examination notification API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.examinations.exam_cell_notification_enums import (
    ExamAnnouncementAudience,
    ExamNotificationChannel,
    ExamNotificationEvent,
)
from app.modules.examinations.exam_cell_notification_models import (
    ExamAnnouncementRecord,
    ExamNotificationDeliveryLog,
    ExamNotificationEventRecord,
    ExamNotificationTemplate,
)


class ExamNotificationPreferenceUpdate(BaseModel):
    in_app_enabled: bool | None = None
    email_enabled: bool | None = None
    sms_enabled: bool | None = None


class ExamNotificationPreferenceRead(BaseModel):
    user_id: str
    in_app_enabled: bool
    email_enabled: bool
    sms_enabled: bool

    @classmethod
    def from_template(cls, doc: ExamNotificationTemplate) -> "ExamNotificationPreferenceRead":
        return cls(
            user_id=str(doc.user_id),
            in_app_enabled=doc.in_app_enabled,
            email_enabled=doc.email_enabled,
            sms_enabled=doc.sms_enabled,
        )


class ExamNotificationTemplateUpsert(BaseModel):
    event_type: ExamNotificationEvent
    title_template: str = Field(min_length=1, max_length=300)
    body_template: str = Field(min_length=1, max_length=4000)
    is_active: bool = True


class ExamNotificationTemplateRead(BaseModel):
    template_id: str
    event_type: str
    title_template: str
    body_template: str
    is_active: bool

    @classmethod
    def from_doc(cls, doc: ExamNotificationTemplate) -> "ExamNotificationTemplateRead":
        return cls(
            template_id=doc.template_id,
            event_type=doc.event_type,
            title_template=doc.title_template,
            body_template=doc.body_template,
            is_active=doc.is_active,
        )


class ExamManualNotificationRequest(BaseModel):
    event_type: ExamNotificationEvent
    recipient_user_id: str
    dedupe_key: str | None = None
    exam_session_id: str | None = None
    template_kwargs: dict[str, str] = Field(default_factory=dict)
    channels: list[ExamNotificationChannel] | None = None
    restricted: bool = False


class ExamNotificationEventRead(BaseModel):
    event_record_id: str
    event_type: str
    recipient_user_id: str
    title: str
    body: str
    exam_session_id: str | None
    restricted: bool
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamNotificationEventRecord) -> "ExamNotificationEventRead":
        return cls(
            event_record_id=doc.event_record_id,
            event_type=doc.event_type,
            recipient_user_id=str(doc.recipient_user_id),
            title=doc.title,
            body=doc.body,
            exam_session_id=str(doc.exam_session_id) if doc.exam_session_id else None,
            restricted=doc.restricted,
            created_at=doc.created_at,
        )


class ExamNotificationDeliveryRead(BaseModel):
    delivery_id: str
    event_record_id: str
    channel: str
    status: str
    retry_count: int
    error: str | None

    @classmethod
    def from_doc(cls, doc: ExamNotificationDeliveryLog) -> "ExamNotificationDeliveryRead":
        return cls(
            delivery_id=doc.delivery_id,
            event_record_id=doc.event_record_id,
            channel=doc.channel,
            status=doc.status,
            retry_count=doc.retry_count,
            error=doc.error,
        )


class ExamAnnouncementCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    body: str = Field(min_length=3, max_length=8000)
    audience: ExamAnnouncementAudience
    exam_session_id: str | None = None
    recipient_user_ids: list[str] = Field(default_factory=list)


class ExamAnnouncementRead(BaseModel):
    announcement_id: str
    title: str
    body: str
    audience: str
    exam_session_id: str | None
    published: bool
    published_at: datetime | None
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamAnnouncementRecord) -> "ExamAnnouncementRead":
        return cls(
            announcement_id=doc.announcement_id,
            title=doc.title,
            body=doc.body,
            audience=doc.audience,
            exam_session_id=str(doc.exam_session_id) if doc.exam_session_id else None,
            published=doc.published,
            published_at=doc.published_at,
            created_at=doc.created_at,
        )