"""Communication administration API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.college_admin.communication_admin_models import AnnouncementAudience, InstitutionAnnouncement


class AnnouncementCreate(BaseModel):
    announcement_id: str
    title: str
    body: str
    audience: AnnouncementAudience = AnnouncementAudience.ALL
    department_id: str | None = None
    audience_group_id: str | None = None
    channels: list[str] = Field(default_factory=lambda: ["in_app"])


class AnnouncementSchedule(BaseModel):
    announcement_id: str
    run_at: datetime


class TemplateUpsert(BaseModel):
    template_code: str
    channel: str
    subject: str | None = None
    body: str


class AudienceGroupUpsert(BaseModel):
    group_id: str
    name: str
    member_user_ids: list[str] = Field(default_factory=list)


class ProviderSettingsUpsert(BaseModel):
    channel: str
    provider_name: str
    credential_ref: str
    push_enabled: bool = False


class RetryDelivery(BaseModel):
    log_id: str


class AnnouncementRead(BaseModel):
    announcement_id: str
    title: str
    status: str
    audience: AnnouncementAudience

    @classmethod
    def from_document(cls, doc: InstitutionAnnouncement) -> "AnnouncementRead":
        return cls(
            announcement_id=doc.announcement_id,
            title=doc.title,
            status=doc.status,
            audience=doc.audience,
        )