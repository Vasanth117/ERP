"""Hostel visitor API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.hostel.visitor_models import HostelVisitorStatus


class VisitorRegisterInput(BaseModel):
    resident_user_id: str
    hostel_code: str | None = None
    visitor_name: str
    mobile_number: str | None = None
    id_type: str | None = None
    id_reference: str | None = None
    photo_ref: str | None = None
    visitor_address: str | None = None
    organization: str | None = None
    purpose: str
    relationship_to_resident: str | None = None
    accompanying_count: int = 0
    expected_arrival: datetime | None = None
    expected_departure: datetime | None = None
    vehicle_info: str | None = None
    remarks: str | None = None
    walk_in: bool = False
    approval_required: bool | None = None


class VisitorApprovalInput(BaseModel):
    visit_id: str
    approved: bool
    remarks: str | None = None
    approver_role: str = "hostel_admin"


class VisitorEntryInput(BaseModel):
    visit_id: str
    pass_reference: str | None = None


class VisitorExitInput(BaseModel):
    visit_id: str
    note: str | None = None


class VisitorDenyInput(BaseModel):
    visit_id: str
    reason: str


class VisitorRestrictionUpsert(BaseModel):
    hostel_code: str | None = None
    visiting_hours: dict = Field(default_factory=dict)
    max_visitors_per_resident: int | None = None
    allowed_weekdays: list[int] = Field(default_factory=list)
    restricted_visitor_types: list[str] = Field(default_factory=list)
    policy_notes: str | None = None


class VisitorEntryRead(BaseModel):
    visit_id: str
    visitor_name: str
    resident_user_id: str
    hostel_code: str | None
    status: HostelVisitorStatus
    purpose: str
    expected_arrival: datetime | None
    expected_departure: datetime | None
    actual_entry_at: datetime | None
    actual_exit_at: datetime | None
    created_at: datetime