"""Department Admin phase 6 — calendar and announcements."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.department_admin.models import DepartmentAnnouncementStatus, DepartmentEventStatus


class CalendarFilters(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None
    category: str | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    audience_scope: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    status: DepartmentEventStatus | None = None

    @field_validator("date_to")
    @classmethod
    def range_ok(cls, date_to: datetime | None, info) -> datetime | None:
        start = info.data.get("date_from")
        if start and date_to and start > date_to:
            raise ValueError("date_from must be on or before date_to")
        return date_to


class CalendarEventCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str = Field(min_length=2, max_length=64)
    starts_at: datetime
    ends_at: datetime
    timezone: str = Field(default="UTC", max_length=64)
    venue: str | None = Field(default=None, max_length=200)
    room: str | None = Field(default=None, max_length=64)
    laboratory: str | None = Field(default=None, max_length=64)
    organizer_user_id: str
    responsible_faculty_user_id: str | None = None
    audience_scope: str = Field(default="department", max_length=32)
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    visibility: str = Field(default="department_admin", max_length=32)
    academic_year_label: str | None = None
    semester_label: str | None = None
    related_course_code: str | None = None
    registration_required: bool = False
    idempotency_key: str | None = Field(default=None, max_length=128)

    @field_validator("ends_at")
    @classmethod
    def ends_after_start(cls, ends_at: datetime, info) -> datetime:
        starts = info.data.get("starts_at")
        if starts and ends_at <= starts:
            raise ValueError("ends_at must be after starts_at")
        return ends_at


class CalendarEventUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, max_length=64)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    venue: str | None = None
    room: str | None = None
    laboratory: str | None = None
    responsible_faculty_user_id: str | None = None
    audience_scope: str | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    visibility: str | None = None
    status: DepartmentEventStatus | None = None
    change_reason: str | None = Field(default=None, max_length=500)


class CalendarEventRead(BaseModel):
    event_id: str
    title: str
    description: str | None
    category: str
    starts_at: datetime
    ends_at: datetime
    timezone: str
    venue: str | None
    room: str | None
    laboratory: str | None
    organizer_user_id: str
    responsible_faculty_user_id: str | None
    audience_scope: str
    programme_code: str | None
    batch_label: str | None
    section_code: str | None
    visibility: str
    academic_year_label: str | None
    semester_label: str | None
    related_course_code: str | None
    registration_required: bool
    status: DepartmentEventStatus
    source: str = "department_calendar_events"
    created_at: datetime
    updated_at: datetime


class CollegeCalendarEventRead(BaseModel):
    event_id: str
    title: str
    description: str | None
    event_at: datetime
    event_type: str
    audience: str
    source: str = "academic_calendar_events"


class CalendarOverviewRead(BaseModel):
    department_events: list[CalendarEventRead]
    college_events: list[CollegeCalendarEventRead]
    total_department: int


class CalendarConflictRead(BaseModel):
    conflicts: list[dict[str, str]]


class CalendarCancelBody(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    body: str = Field(min_length=2, max_length=16000)
    category: str = Field(default="general", max_length=64)
    priority: str = Field(default="normal", max_length=16)
    audience_type: str = Field(max_length=32)
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    expires_at: datetime | None = None
    attachment_refs: list[str] = Field(default_factory=list)
    idempotency_key: str | None = Field(default=None, max_length=128)


class AnnouncementUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    body: str | None = Field(default=None, max_length=16000)
    category: str | None = None
    priority: str | None = None
    audience_type: str | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    expires_at: datetime | None = None
    attachment_refs: list[str] | None = None


class AnnouncementRead(BaseModel):
    announcement_id: str
    title: str
    body: str
    category: str
    priority: str
    audience_type: str
    programme_code: str | None
    batch_label: str | None
    section_code: str | None
    status: DepartmentAnnouncementStatus
    author_user_id: str
    publish_at: datetime | None
    expires_at: datetime | None
    scheduled_publish_at: datetime | None
    approved_by: str | None
    approved_at: datetime | None
    delivery_summary: dict
    attachment_refs: list[str]
    created_at: datetime
    updated_at: datetime


class AnnouncementScheduleBody(BaseModel):
    scheduled_publish_at: datetime
    idempotency_key: str | None = Field(default=None, max_length=128)


class AnnouncementDecisionBody(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class AnnouncementDeliveryStatusRead(BaseModel):
    announcement_id: str
    status: str
    delivery_summary: dict
    last_outbox_event_id: str | None = None


class AnnouncementAcknowledgementRead(BaseModel):
    user_id: str
    acknowledged_at: datetime