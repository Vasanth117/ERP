"""Hostel communication API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hostel.communication_models import (
    HostelAnnouncementStatus,
    HostelNotificationDeliveryStatus,
    HostelNotificationPriority,
)


class NotificationDashboard(BaseModel):
    total_notifications: int = 0
    unread_notifications: int = 0
    sent_notifications: int = 0
    scheduled_notifications: int = 0
    failed_notifications: int = 0
    draft_announcements: int = 0
    published_announcements: int = 0
    pending_acknowledgements: int = 0
    requires_action: int = 0


class AudiencePreview(BaseModel):
    recipient_count: int
    sample_user_ids: list[str]


class NotificationTemplateUpsert(BaseModel):
    template_code: str
    category: str
    title_pattern: str
    body_pattern: str
    default_channels: list[str] = Field(default_factory=lambda: ["in_app"])
    variables: list[str] = Field(default_factory=list)
    requires_acknowledgement: bool = False
    is_active: bool = True


class NotificationTemplateRead(BaseModel):
    template_code: str
    category: str
    title_pattern: str
    body_pattern: str
    default_channels: list[str]
    is_active: bool


class AnnouncementCreate(BaseModel):
    announcement_code: str
    title: str = Field(max_length=200)
    body: str = Field(max_length=8000)
    category: str = Field(max_length=64)
    priority: HostelNotificationPriority = HostelNotificationPriority.NORMAL
    audience: dict[str, Any] = Field(default_factory=dict)
    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    document_refs: list[str] = Field(default_factory=list)
    hostel_code: str | None = None
    publish_at: datetime | None = None
    expires_at: datetime | None = None
    requires_acknowledgement: bool = False
    requires_action: bool = False


class AnnouncementRead(BaseModel):
    announcement_code: str
    title: str
    status: HostelAnnouncementStatus
    category: str
    priority: HostelNotificationPriority
    audience_preview_count: int
    published_at: datetime | None
    requires_acknowledgement: bool


class AnnouncementTransition(BaseModel):
    action: str = Field(pattern="^(submit|approve|schedule|publish|withdraw|archive|expire)$")


class AudiencePreviewRequest(BaseModel):
    audience: dict[str, Any]


class InboxItemRead(BaseModel):
    notification_id: str
    title: str
    body: str
    category: str
    status: HostelNotificationDeliveryStatus
    requires_acknowledgement: bool
    read_at: datetime | None
    acknowledged_at: datetime | None
    created_at: datetime


class InboxAcknowledge(BaseModel):
    notification_id: str