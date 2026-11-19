"""Hostel administration API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.hostel.hostel_enums import HostelApplicationStatus


class HostelBuildingCreate(BaseModel):
    building_code: str
    name: str
    campus_id: str | None = None


class HostelBlockCreate(BaseModel):
    building_code: str
    block_code: str
    name: str


class HostelRoomCreate(BaseModel):
    building_code: str
    block_code: str
    room_code: str
    capacity: int = Field(ge=1, default=1)
    gender_policy: str | None = None


class HostelBedCreate(BaseModel):
    bed_id: str
    building_code: str
    block_code: str
    room_code: str
    bed_label: str


class HostelApplicationReview(BaseModel):
    application_id: str
    decision: HostelApplicationStatus
    note: str | None = None


class AllocationApprove(BaseModel):
    application_id: str
    bed_id: str


class CheckInOut(BaseModel):
    allocation_id: str


class VisitorLogCreate(BaseModel):
    resident_user_id: str
    visitor_name: str
    purpose: str | None = None


class OutpassDecision(BaseModel):
    request_id: str
    approved: bool
    note: str | None = None


class MaintenanceCreate(BaseModel):
    building_code: str
    room_code: str
    description: str


class IncidentCreate(BaseModel):
    incident_id: str
    building_code: str | None = None
    description: str
    severity: str = "low"


class HostelRuleUpsert(BaseModel):
    rule_code: str
    title: str
    body: str


class MessPlanUpsert(BaseModel):
    plan_code: str
    title: str
    monthly_amount: float = Field(ge=0)
    finance_reference: str | None = None