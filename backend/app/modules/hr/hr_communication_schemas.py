"""HR notifications & communication API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrAnnouncementStatus, HrNotificationPriority
from app.modules.hr.hr_communication_models import HrAnnouncement, HrNotificationDeliveryHistory, HrNotificationTemplate


class NotificationDashboard(BaseModel):
    total_notifications: int = 0
    unread_notifications: int = 0
    sent_notifications: int = 0
    scheduled_notifications: int = 0
    failed_notifications: int = 0
    published_announcements: int = 0
    pending_announcements: int = 0
    pending_acknowledgements: int = 0


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
    id: str
    template_code: str
    category: str

    @classmethod
    def from_doc(cls, doc: HrNotificationTemplate) -> "NotificationTemplateRead":
        return cls(id=str(doc.id), template_code=doc.template_code, category=doc.category)


class AudienceSpec(BaseModel):
    all_employees: bool = False
    department_ids: list[str] = Field(default_factory=list)
    campus_ids: list[str] = Field(default_factory=list)
    designations: list[str] = Field(default_factory=list)
    employee_categories: list[str] = Field(default_factory=list)
    employee_user_ids: list[str] = Field(default_factory=list)


class AudiencePreview(BaseModel):
    recipient_count: int
    sample_user_ids: list[str] = Field(default_factory=list)


class AnnouncementCreate(BaseModel):
    announcement_code: str
    title: str
    body: str
    category: str
    priority: HrNotificationPriority = HrNotificationPriority.NORMAL
    audience: dict[str, Any] = Field(default_factory=dict)
    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    document_refs: list[str] = Field(default_factory=list)
    publish_at: datetime | None = None
    expires_at: datetime | None = None
    pinned: bool = False
    requires_acknowledgement: bool = False


class AnnouncementTransition(BaseModel):
    action: str = Field(pattern="^(submit|approve|schedule|publish|withdraw|archive)$")
    note: str | None = None


class AnnouncementRead(BaseModel):
    id: str
    announcement_code: str
    title: str
    status: HrAnnouncementStatus
    audience_preview_count: int

    @classmethod
    def from_doc(cls, doc: HrAnnouncement) -> "AnnouncementRead":
        return cls(
            id=str(doc.id),
            announcement_code=doc.announcement_code,
            title=doc.title,
            status=doc.status,
            audience_preview_count=doc.audience_preview_count,
        )


class HrBroadcastCreate(BaseModel):
    title: str
    body: str
    category: str
    priority: HrNotificationPriority = HrNotificationPriority.NORMAL
    audience: dict[str, Any] = Field(default_factory=dict)
    channels: list[str] = Field(default_factory=lambda: ["in_app"])
    requires_acknowledgement: bool = False
    template_code: str | None = None


class NotificationPreferenceUpsert(BaseModel):
    channels_enabled: dict[str, bool] = Field(default_factory=lambda: {"in_app": True, "email": True})
    categories_muted: list[str] = Field(default_factory=list)


class InboxItemRead(BaseModel):
    id: str
    title: str
    status: str
    category: str
    requires_acknowledgement: bool
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: HrNotificationDeliveryHistory) -> "InboxItemRead":
        return cls(
            id=str(doc.id),
            title=doc.title,
            status=doc.status.value,
            category=doc.category,
            requires_acknowledgement=doc.requires_acknowledgement,
            created_at=doc.created_at,
        )