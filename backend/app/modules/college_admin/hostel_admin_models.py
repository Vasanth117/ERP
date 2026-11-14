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
    MAINTENANCE = "maintenance"
    BLOCKED = "blocked"


class HostelAllocationStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"


class HostelBuilding(Document):
    tenant_id: PydanticObjectId
    building_code: str
    name: str = Field(max_length=200)
    campus_id: PydanticObjectId | None = None
    is_active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_buildings"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("building_code", ASCENDING)], unique=True, name="unique_hostel_building"),
        ]


class HostelBlock(Document):
    tenant_id: PydanticObjectId
    building_code: str
    block_code: str
    name: str = Field(max_length=200)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_blocks"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("building_code", ASCENDING), ("block_code", ASCENDING)], unique=True, name="unique_hostel_block"),
        ]


class HostelRoom(Document):
    tenant_id: PydanticObjectId
    building_code: str
    block_code: str
    room_code: str
    capacity: int = Field(ge=1, default=1)
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
    bed_id: str
    building_code: str
    block_code: str
    room_code: str
    bed_label: str
    status: HostelAllocationStatus = HostelAllocationStatus.PENDING
    authoritative_allocation_id: str | None = None
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_allocations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("allocation_id", ASCENDING)], unique=True, name="unique_hostel_admin_allocation"),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_active_student_allocation",
                partialFilterExpression={"status": {"$in": ["pending", "active"]}},
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("bed_id", ASCENDING)],
                unique=True,
                name="unique_active_bed_allocation",
                partialFilterExpression={"status": {"$in": ["pending", "active"]}},
            ),
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


class HostelMessPlan(Document):
    tenant_id: PydanticObjectId
    plan_code: str
    title: str
    monthly_amount: float = Field(ge=0)
    finance_reference: str | None = None
    published: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_mess_plans"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("plan_code", ASCENDING)], unique=True, name="unique_mess_plan"),
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


class HostelOutpassRequest(Document):
    tenant_id: PydanticObjectId
    request_id: str
    student_user_id: PydanticObjectId
    from_at: datetime
    to_at: datetime
    reason: str = Field(max_length=1000)
    status: str = "pending"
    approver_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_outpass_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_outpass"),
        ]


class HostelMaintenanceRequest(Document):
    tenant_id: PydanticObjectId
    request_id: str
    building_code: str
    room_code: str
    description: str
    status: str = "open"
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_maintenance_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_hostel_maintenance"),
        ]


class HostelIncident(Document):
    tenant_id: PydanticObjectId
    incident_id: str
    building_code: str | None = None
    description: str
    severity: str = "low"
    status: str = "open"
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_incidents"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("incident_id", ASCENDING)], unique=True, name="unique_hostel_incident"),
        ]


class HostelRule(Document):
    tenant_id: PydanticObjectId
    rule_code: str
    title: str
    body: str
    version: int = 1
    published: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_rules"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("rule_code", ASCENDING)], unique=True, name="unique_hostel_rule"),
        ]


class HostelWaitingListEntry(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    application_id: str
    position: int = Field(ge=1)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_waiting_list"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("application_id", ASCENDING)], unique=True, name="unique_waiting_entry"),
        ]