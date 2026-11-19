"""Hostel resident operational collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HostelResidentStatus(str, Enum):
    AWAITING_CHECKIN = "awaiting_checkin"
    CHECKED_IN = "checked_in"
    TEMPORARILY_OUTSIDE = "temporarily_outside"
    TRANSFER_PENDING = "transfer_pending"
    CHECKOUT_REQUESTED = "checkout_requested"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


class HostelResident(Document):
    tenant_id: PydanticObjectId
    resident_id: str
    student_user_id: PydanticObjectId
    allocation_id: str
    hostel_code: str | None = None
    building_code: str
    block_code: str
    floor_id: str | None = None
    room_code: str
    bed_id: str
    bed_label: str
    status: HostelResidentStatus = HostelResidentStatus.AWAITING_CHECKIN
    accommodation_start: date | None = None
    expected_checkout: date | None = None
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    keys_issued: list[str] = Field(default_factory=list)
    room_condition_ack: bool = False
    checkin_note: str | None = None
    checkout_note: str | None = None
    clearance_status: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_residents"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("resident_id", ASCENDING)], unique=True, name="unique_hostel_resident"),
            IndexModel([("tenant_id", ASCENDING), ("allocation_id", ASCENDING)], unique=True, name="unique_resident_per_allocation"),
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING)], name="residents_by_student"),
            IndexModel([("tenant_id", ASCENDING), ("hostel_code", ASCENDING), ("status", ASCENDING)], name="residents_by_hostel_status"),
            IndexModel([("tenant_id", ASCENDING), ("bed_id", ASCENDING)], name="residents_by_bed"),
        ]


class HostelResidentStatusHistory(Document):
    tenant_id: PydanticObjectId
    resident_id: str
    from_status: str | None = None
    to_status: str
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_resident_status_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("resident_id", ASCENDING), ("created_at", DESCENDING)], name="resident_status_hist"),
        ]


class HostelResidentCheckinRecord(Document):
    tenant_id: PydanticObjectId
    record_id: str
    resident_id: str
    allocation_id: str
    checked_in_at: datetime = Field(default_factory=utcnow)
    keys_issued: list[str] = Field(default_factory=list)
    room_condition_ack: bool = False
    belongings_notes: str | None = None
    exception_reason: str | None = None
    actor_id: PydanticObjectId | None = None

    class Settings:
        name = "hostel_resident_checkin_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("record_id", ASCENDING)], unique=True, name="unique_checkin_record"),
        ]


class HostelResidentCheckoutRecord(Document):
    tenant_id: PydanticObjectId
    record_id: str
    resident_id: str
    allocation_id: str
    checkout_type: str = "planned"
    checked_out_at: datetime = Field(default_factory=utcnow)
    keys_returned: bool = True
    room_condition_notes: str | None = None
    clearance_status: dict[str, Any] = Field(default_factory=dict)
    exception_reason: str | None = None
    actor_id: PydanticObjectId | None = None

    class Settings:
        name = "hostel_resident_checkout_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("record_id", ASCENDING)], unique=True, name="unique_checkout_record"),
        ]


class HostelResidentTransferHistory(Document):
    tenant_id: PydanticObjectId
    resident_id: str
    from_allocation_id: str
    to_allocation_id: str | None = None
    transfer_date: datetime = Field(default_factory=utcnow)
    reason: str | None = None
    actor_id: PydanticObjectId | None = None

    class Settings:
        name = "hostel_resident_transfer_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("resident_id", ASCENDING), ("transfer_date", DESCENDING)], name="resident_xfer_hist"),
        ]