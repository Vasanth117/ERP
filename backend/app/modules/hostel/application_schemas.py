"""Hostel application API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.hostel.hostel_enums import HostelApplicationStatus


class HostelApplicationSubmit(BaseModel):
    academic_year_label: str
    semester_label: str | None = None
    requested_hostel_category: str | None = None
    preferred_hostel_code: str | None = None
    preferred_room_type: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    reason: str | None = None
    eligibility_payload: dict = Field(default_factory=dict)
    document_refs: list[str] = Field(default_factory=list)


class HostelApplicationStaffSubmit(HostelApplicationSubmit):
    student_user_id: str


class HostelApplicationReviewInput(BaseModel):
    application_id: str
    decision: HostelApplicationStatus
    remarks: str | None = None
    internal_remarks: str | None = None


class HostelApplicationRead(BaseModel):
    application_id: str
    student_user_id: str
    academic_year_label: str
    semester_label: str | None
    preferred_hostel_code: str | None
    preferred_room_type: str | None
    status: HostelApplicationStatus
    reason: str | None
    eligibility_result: dict | None
    internal_remarks: str | None
    active_offer_id: str | None
    allocation_id: str | None
    submitted_at: datetime
    updated_at: datetime


class WaitingListAdd(BaseModel):
    application_id: str
    list_id: str | None = None
    hostel_code: str | None = None
    room_type: str | None = None
    priority_score: int = 0
    priority_override_reason: str | None = None


class WaitingListPriorityUpdate(BaseModel):
    application_id: str
    position: int = Field(ge=1)
    priority_score: int | None = None
    priority_override_reason: str | None = None


class AllocationOfferCreate(BaseModel):
    application_id: str
    bed_id: str
    response_hours: int = Field(default=72, ge=1, le=168)


class OfferResponse(BaseModel):
    offer_id: str
    accept: bool