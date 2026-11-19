"""Hostel allocation and availability API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.college_admin.hostel_admin_models import HostelAllocationStatus, HostelBedStatus
from app.modules.hostel.application_models import HostelTransferType


class BedAvailabilityItem(BaseModel):
    bed_id: str
    bed_label: str
    status: HostelBedStatus
    hostel_code: str | None = None
    building_code: str
    block_code: str
    room_code: str
    floor_id: str | None = None
    room_type: str | None = None


class RoomAvailabilityItem(BaseModel):
    building_code: str
    block_code: str
    room_code: str
    hostel_code: str | None = None
    floor_id: str | None = None
    room_type: str | None = None
    capacity: int
    bed_capacity: int
    occupied_beds: int
    available_beds: int
    beds: list[BedAvailabilityItem] = Field(default_factory=list)


class AllocationCreate(BaseModel):
    student_user_id: str
    application_id: str | None = None
    hostel_code: str
    bed_id: str
    start_date: date | None = None
    expected_end_date: date | None = None
    allocation_reason: str | None = None
    require_approval: bool = False


class AllocationConfirm(BaseModel):
    allocation_id: str
    note: str | None = None


class AllocationCancel(BaseModel):
    allocation_id: str
    reason: str | None = None


class AllocationExtend(BaseModel):
    allocation_id: str
    expected_end_date: date


class AllocationTransferCreate(BaseModel):
    allocation_id: str
    transfer_type: HostelTransferType = HostelTransferType.ROOM
    target_bed_id: str
    reason: str


class AllocationRead(BaseModel):
    allocation_id: str
    student_user_id: str
    application_id: str | None
    hostel_code: str | None
    bed_id: str
    building_code: str
    block_code: str
    room_code: str
    bed_label: str
    status: HostelAllocationStatus
    start_date: date | None
    expected_end_date: date | None
    allocation_reason: str | None
    created_at: datetime
    updated_at: datetime