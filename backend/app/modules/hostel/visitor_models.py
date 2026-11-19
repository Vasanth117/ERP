"""Hostel visitor management collections."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HostelVisitorStatus(str, Enum):
    EXPECTED = "expected"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    ENTRY_RECORDED = "entry_recorded"
    INSIDE = "currently_inside"
    EXITED = "exited"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"
    FLAGGED = "flagged"


class HostelVisitorProfile(Document):
    tenant_id: PydanticObjectId
    profile_id: str
    visitor_name: str
    mobile_number: str | None = None
    id_type: str | None = None
    id_reference: str | None = None
    photo_ref: str | None = None
    blacklisted: bool = False
    blacklist_reason: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_visitor_profiles"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("profile_id", ASCENDING)], unique=True, name="unique_visitor_profile"),
            IndexModel([("tenant_id", ASCENDING), ("mobile_number", ASCENDING)], name="visitor_profile_mobile"),
        ]


class HostelVisitorEntry(Document):
    tenant_id: PydanticObjectId
    visit_id: str
    resident_user_id: PydanticObjectId
    hostel_code: str | None = None
    visitor_name: str
    mobile_number: str | None = None
    id_type: str | None = None
    id_reference: str | None = None
    photo_ref: str | None = None
    visitor_address: str | None = None
    organization: str | None = None
    purpose: str = Field(max_length=1000)
    relationship_to_resident: str | None = None
    accompanying_count: int = Field(default=0, ge=0)
    expected_arrival: datetime | None = None
    expected_departure: datetime | None = None
    vehicle_info: str | None = None
    remarks: str | None = None
    visitor_profile_id: str | None = None
    status: HostelVisitorStatus = HostelVisitorStatus.EXPECTED
    approval_required: bool = False
    actual_entry_at: datetime | None = None
    actual_exit_at: datetime | None = None
    pass_reference: str | None = None
    denied_reason: str | None = None
    actor_id: PydanticObjectId | None = None
    approver_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_visitor_entries"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("visit_id", ASCENDING)], unique=True, name="unique_visitor_entry"),
            IndexModel([("tenant_id", ASCENDING), ("resident_user_id", ASCENDING), ("created_at", DESCENDING)], name="visits_by_resident"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="visits_by_status"),
            IndexModel([("tenant_id", ASCENDING), ("hostel_code", ASCENDING), ("actual_entry_at", DESCENDING)], name="visits_by_hostel"),
        ]


class HostelVisitorApproval(Document):
    tenant_id: PydanticObjectId
    approval_id: str
    visit_id: str
    approver_role: str
    decision: str
    remarks: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_visitor_approvals"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("approval_id", ASCENDING)], unique=True, name="unique_visitor_approval"),
        ]


class HostelVisitorRestriction(Document):
    tenant_id: PydanticObjectId
    hostel_code: str | None = None
    visiting_hours: dict[str, Any] = Field(default_factory=dict)
    max_visitors_per_resident: int | None = None
    allowed_weekdays: list[int] = Field(default_factory=list)
    restricted_visitor_types: list[str] = Field(default_factory=list)
    policy_notes: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_visitor_restrictions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("hostel_code", ASCENDING)], unique=True, name="unique_visitor_restriction_scope"),
        ]


class HostelVisitorActivityHistory(Document):
    tenant_id: PydanticObjectId
    visit_id: str
    event_type: str
    note: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_visitor_activity_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("visit_id", ASCENDING), ("created_at", DESCENDING)], name="visitor_activity"),
        ]