"""Parent portal phase 5 schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.parents.enums import ParentMeetingMode, ParentReportCategory, ParentStudentServiceType


class ParentMeetingCategoryRead(BaseModel):
    category_code: str
    title: str
    requires_staff_selection: bool


class ParentMeetingDashboardRead(BaseModel):
    upcoming: int
    pending_requests: int
    confirmed: int
    awaiting_staff: int
    rescheduled: int
    cancelled: int
    completed: int
    followups_open: int


class ParentMeetingSlotRead(BaseModel):
    slot_start: datetime
    slot_end: datetime
    available: bool


class ParentMeetingRepresentativeRead(BaseModel):
    staff_user_id: str
    full_name: str
    department_id: str | None = None
    department_name: str | None = None


class ParentMeetingRequestCreate(BaseModel):
    category_code: str = Field(max_length=64)
    department_id: str | None = None
    staff_user_id: str | None = None
    purpose: str = Field(min_length=10, max_length=2000)
    remarks: str | None = Field(default=None, max_length=2000)
    preferred_date: date
    preferred_start: datetime
    preferred_end: datetime
    alternate_preferences: list[dict] = Field(default_factory=list, max_length=5)
    meeting_mode: ParentMeetingMode
    supporting_document_refs: list[str] = Field(default_factory=list, max_length=10)


class ParentMeetingRequestRead(BaseModel):
    request_id: str
    category_code: str
    status: str
    purpose: str
    meeting_mode: str
    preferred_start: datetime
    preferred_end: datetime
    appointment_id: str | None = None
    rejection_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class ParentMeetingAppointmentRead(BaseModel):
    appointment_id: str
    request_id: str
    category_code: str
    scheduled_start: datetime
    scheduled_end: datetime
    meeting_mode: str
    venue_or_link: str | None = None
    parent_visible_agenda: str | None = None
    status: str
    outcome_summary: str | None = None


class ParentMeetingRescheduleCreate(BaseModel):
    preferred_start: datetime
    preferred_end: datetime
    reason: str = Field(min_length=5, max_length=1000)


class ParentMeetingCancelCreate(BaseModel):
    reason: str = Field(min_length=5, max_length=1000)


class ParentMeetingOutcomeRead(BaseModel):
    appointment_id: str
    parent_visible_summary: str
    agreed_next_steps: str | None = None
    completed_at: datetime
    followups: list[dict] = Field(default_factory=list)


class ParentMeetingAdminDecision(BaseModel):
    decision: str = Field(max_length=32)
    rejection_reason: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    venue_or_link: str | None = None
    staff_user_id: str | None = None
    parent_visible_agenda: str | None = None
    staff_preparation_notes: str | None = None


class ParentMeetingOutcomeRecord(BaseModel):
    parent_visible_summary: str = Field(min_length=5, max_length=4000)
    agreed_next_steps: str | None = Field(default=None, max_length=2000)
    staff_internal_notes: str | None = Field(default=None, max_length=4000)
    mark_completed: bool = True


class ParentStudentServicesOverviewRead(BaseModel):
    hostel_enabled: bool
    transport_enabled: bool
    library_enabled: bool
    mess_enabled: bool
    welfare_enabled: bool


class ParentHostelSummaryRead(BaseModel):
    allocated: bool
    hostel_name: str | None = None
    block: str | None = None
    room: str | None = None
    status: str | None = None
    notices: list[dict] = Field(default_factory=list)


class ParentTransportSummaryRead(BaseModel):
    enrolled: bool
    route_name: str | None = None
    pickup_stop: str | None = None
    drop_stop: str | None = None
    notifications: list[dict] = Field(default_factory=list)


class ParentLibrarySummaryRead(BaseModel):
    active_loans: int
    overdue_loans: int
    reservations: int
    items: list[dict] = Field(default_factory=list)


class ParentMessSummaryRead(BaseModel):
    enabled: bool
    summary: str | None = None


class ParentServiceEnquiryCreate(BaseModel):
    service_type: ParentStudentServiceType
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=4000)


class ParentServiceEnquiryRead(BaseModel):
    enquiry_id: str
    service_type: str
    subject: str
    status: str
    created_at: datetime


class ParentReportsDashboardRead(BaseModel):
    linked_students: int
    categories_available: list[str]


class ParentReportExportRead(BaseModel):
    report_category: str
    student_user_id: str | None = None
    generated_at: datetime
    export_token: str
    format: str
    payload: dict


class ParentSecurityAccountRead(BaseModel):
    account_status: str
    email: str
    email_verified: bool
    contact_phone: str | None = None
    mobile_verified: bool
    linked_students: int
    mfa_hint: str | None = None


class ParentSecuritySessionRead(BaseModel):
    family_id: str
    issued_at: datetime
    revoked: bool


class ParentContactChangeRequestCreate(BaseModel):
    channel: str = Field(max_length=16)
    proposed_value: str = Field(max_length=254)


class ParentRelationshipReviewCreate(BaseModel):
    action: str = Field(max_length=32)
    reason: str = Field(min_length=10, max_length=2000)