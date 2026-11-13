"""Faculty communication API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class AnnouncementCreate(BaseModel):
    course_code: str
    section: str | None = None
    title: str = Field(max_length=200)
    body: str = Field(max_length=8000)
    assignment_id: str | None = None

    model_config = {"extra": "forbid"}


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    body: str | None = Field(default=None, max_length=8000)

    model_config = {"extra": "forbid"}


class AnnouncementRead(BaseModel):
    id: str
    course_code: str
    section: str | None
    title: str
    body: str
    status: str
    created_at: datetime
    publish_history: list[dict]


class MessageRead(BaseModel):
    id: str
    subject: str
    body: str
    course_code: str
    section: str | None
    created_at: datetime


class AssignmentUpdateShare(BaseModel):
    assignment_id: str
    body: str | None = Field(default=None, max_length=4000)

    model_config = {"extra": "forbid"}


class RecipientRead(BaseModel):
    student_user_id: str
    course_code: str
    section: str
    delivery_status: str


class NotificationItemRead(BaseModel):
    id: str
    source: str
    title: str
    body: str
    created_at: datetime
    read_at: datetime | None


class NotificationReadUpdate(BaseModel):
    read: bool = True

    model_config = {"extra": "forbid"}


class NotificationPreferencesRead(BaseModel):
    email_enabled: bool
    push_enabled: bool
    digest_only: bool


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: bool | None = None
    push_enabled: bool | None = None
    digest_only: bool | None = None

    model_config = {"extra": "forbid"}
