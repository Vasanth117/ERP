"""College admin hostel administration collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HostelBedStatus(str, Enum):
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    BLOCKED = "blocked"


class HostelAllocationStatus(str, Enum):
    REQUESTED = "requested"
    PENDING = "pending"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    TRANSFERRED = "transferred"
    CHECKED_OUT = "checked_out"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


HOSTEL_BED_HOLDING_ALLOCATION_STATUSES = frozenset(
    {
        HostelAllocationStatus.REQUESTED.value,
        HostelAllocationStatus.PENDING.value,
        HostelAllocationStatus.PENDING_APPROVAL.value,
        HostelAllocationStatus.APPROVED.value,
        HostelAllocationStatus.CONFIRMED.value,
        HostelAllocationStatus.ACTIVE.value,
    }
)


class HostelBuilding(Document):
    tenant_id: PydanticObjectId
    hostel_code: str | None = None
    building_code: str
    name: str = Field(max_length=200)
    building_type: str | None = Field(default=None, max_length=64)
    campus_id: PydanticObjectId | None = None
    facilities: list[str] = Field(default_factory=list)
    responsible_staff_user_id: PydanticObjectId | None = None
    operating_status: str = "active"
    is_active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_buildings"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("building_code", ASCENDING)], unique=True, name="unique_hostel_building"),
            IndexModel([("tenant_id", ASCENDING), ("hostel_code", ASCENDING), ("is_active", ASCENDING)], name="buildings_by_hostel"),
        ]


class HostelBlock(Document):
    tenant_id: PydanticObjectId
    hostel_code: str | None = None
    building_code: str
    block_code: str
    name: str = Field(max_length=200)
    is_active: bool = True
    responsible_staff_user_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_blocks"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("building_code", ASCENDING), ("block_code", ASCENDING)], unique=True, name="unique_hostel_block"),
        ]


class HostelRoom(Document):
    tenant_id: PydanticObjectId
    hostel_code: str | None = None
    building_code: str
    block_code: str
    floor_id: str | None = None
    floor_label: str | None = None
    room_code: str
    room_type: str | None = Field(default=None, max_length=32)
    capacity: int = Field(ge=1, default=1)
    bed_capacity: int = Field(ge=1, default=1)
    facilities: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=2000)
    operational_status: str = "active"
    maintenance_status: str = "available"
    gender_policy: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_rooms"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("building_code", ASCENDING), ("block_code", ASCENDING), ("room_code", ASCENDING)],
                unique=True,
                name="unique_hostel_room",
            ),
        ]


class HostelBed(Document):
    tenant_id: PydanticObjectId
    hostel_code: str | None = None
    bed_id: str
    building_code: str
    block_code: str
    room_code: str
    bed_label: str
    status: HostelBedStatus = HostelBedStatus.AVAILABLE
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_beds"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("bed_id", ASCENDING)], unique=True, name="unique_hostel_bed"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="hostel_beds_by_status"),
        ]


class HostelAllocation(Document):
    """Active allocation; authoritative student view syncs to `hostel_room_allocations`."""

    tenant_id: PydanticObjectId
    allocation_id: str
    student_user_id: PydanticObjectId
    application_id: str | None = None
    hostel_code: str | None = None
    bed_id: str
    building_code: str
    block_code: str
    room_code: str
    floor_id: str | None = None
    bed_label: str
    status: HostelAllocationStatus = HostelAllocationStatus.PENDING
    allocation_reason: str | None = Field(default=None, max_length=2000)
    start_date: date | None = None
    expected_end_date: date | None = None
    previous_allocation_id: str | None = None
    authoritative_allocation_id: str | None = None
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    approver_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_allocations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("allocation_id", ASCENDING)], unique=True, name="unique_hostel_admin_allocation"),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_hostel_admin_active_student_allocation",
                partialFilterExpression={
                    "status": {
                        "$in": [
                            "requested",
                            "pending",
                            "pending_approval",
                            "approved",
                            "confirmed",
                            "active",
                        ]
                    }
                },
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("bed_id", ASCENDING)],
                unique=True,
                name="unique_active_bed_allocation",
                partialFilterExpression={
                    "status": {
                        "$in": [
                            "requested",
                            "pending",
                            "pending_approval",
                            "approved",
                            "confirmed",
                            "active",
                        ]
                    }
                },
            ),
            IndexModel([("tenant_id", ASCENDING), ("application_id", ASCENDING)], name="allocation_by_application"),
            IndexModel([("tenant_id", ASCENDING), ("hostel_code", ASCENDING), ("status", ASCENDING)], name="allocations_by_hostel"),
        ]


class HostelResidentHistory(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    allocation_id: str
    event_type: str
    note: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_resident_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("created_at", DESCENDING)], name="resident_history"),
        ]


class HostelVisitorLog(Document):
    tenant_id: PydanticObjectId
    visit_id: str
    resident_user_id: PydanticObjectId
    visitor_name: str
    purpose: str | None = None
    check_in_at: datetime = Field(default_factory=utcnow)
    check_out_at: datetime | None = None
    actor_id: PydanticObjectId | None = None

    class Settings:
        name = "hostel_visitor_logs"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("visit_id", ASCENDING)], unique=True, name="unique_visitor_log"),
        ]


class HostelWaitingListEntry(Document):
    tenant_id: PydanticObjectId
    list_id: str
    student_user_id: PydanticObjectId
    application_id: str
    hostel_code: str | None = None
    room_type: str | None = None
    position: int = Field(ge=1)
    priority_score: int = Field(default=0)
    priority_override_reason: str | None = Field(default=None, max_length=500)
    status: str = "active"
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_waiting_list"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("application_id", ASCENDING)], unique=True, name="unique_waiting_entry"),
            IndexModel(
                [("tenant_id", ASCENDING), ("list_id", ASCENDING), ("position", ASCENDING)],
                name="waiting_by_list_position",
            ),
        ]


# Re-export portal-owned documents (single Beanie model per collection).
from app.modules.hostel.leave_outpass_models import HostelOutpassRequest  # noqa: E402,F401
from app.modules.hostel.maintenance_models import HostelMaintenanceRequest  # noqa: E402,F401
from app.modules.hostel.mess_models import HostelMessPlan  # noqa: E402,F401
from app.modules.hostel.rules_incident_models import HostelIncident, HostelRule  # noqa: E402,F401