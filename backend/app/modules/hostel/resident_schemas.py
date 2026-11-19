"""Hostel resident API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.hostel.resident_models import HostelResidentStatus


class ResidentOperationalView(BaseModel):
    resident_id: str
    student_user_id: str
    student_name: str | None = None
    roll_number: str | None = None
    student_id: str | None = None
    contact_phone: str | None = None
    photo_ref: str | None = None
    allocation_id: str
    hostel_code: str | None
    building_code: str
    block_code: str
    floor_id: str | None
    room_code: str
    bed_id: str
    bed_label: str
    status: HostelResidentStatus
    accommodation_start: date | None
    expected_checkout: date | None
    checked_in_at: datetime | None
    checked_out_at: datetime | None
    emergency_contacts: list[dict] = Field(default_factory=list)
    mess_enrollment_status: str | None = None
    active_outpass: bool = False


class ResidentCheckinInput(BaseModel):
    allocation_id: str
    keys_issued: list[str] = Field(default_factory=list)
    room_condition_ack: bool = False
    belongings_notes: str | None = None
    exception_reason: str | None = None
    verify_student_user_id: str | None = None


class ResidentCheckoutInput(BaseModel):
    allocation_id: str
    checkout_type: str = "planned"
    keys_returned: bool = True
    room_condition_notes: str | None = None
    clearance_status: dict = Field(default_factory=dict)
    exception_reason: str | None = None


class ResidentNoShowInput(BaseModel):
    allocation_id: str
    note: str | None = None