"""Leave and outpass API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus, HostelOutpassType


class LeaveTypeUpsert(BaseModel):
    type_code: str = Field(max_length=32)
    label: str = Field(max_length=120)
    requires_document: bool = False
    max_duration_hours: int | None = Field(default=None, ge=1)
    policy: dict = Field(default_factory=dict)
    active: bool = True


class LeaveSubmit(BaseModel):
    leave_type_code: str
    reason: str = Field(max_length=2000)
    destination: str | None = None
    departure_at: datetime
    expected_return_at: datetime
    emergency_contact_ref: str | None = None
    document_ref: str | None = None


class OutpassSubmit(BaseModel):
    outpass_type: HostelOutpassType = HostelOutpassType.DAY
    reason: str = Field(max_length=1000)
    destination: str | None = None
    from_at: datetime
    to_at: datetime


class LeaveOutpassRead(BaseModel):
    request_id: str
    kind: str
    student_user_id: str
    resident_id: str | None
    status: HostelLeaveOutpassStatus
    departure_at: datetime | None = None
    expected_return_at: datetime | None = None
    from_at: datetime | None = None
    to_at: datetime | None = None
    reason: str
    leave_type_code: str | None = None
    outpass_type: str | None = None
    created_at: datetime


class ApprovalDecision(BaseModel):
    request_id: str
    kind: str = Field(pattern="^(leave|outpass)$")
    approve: bool
    comment: str | None = None
    return_for_correction: bool = False


class GateMovementInput(BaseModel):
    request_id: str
    kind: str = Field(pattern="^(leave|outpass)$")
    movement_type: str = Field(pattern="^(departure|return|cancel_departure|emergency_return)$")
    note: str | None = None


class LeaveOutpassOverview(BaseModel):
    pending_leave: int
    pending_outpass: int
    approved_leave: int
    approved_outpass: int
    currently_outside: int
    overdue_returns: int
    cancelled: int