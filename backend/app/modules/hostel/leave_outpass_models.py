"""Hostel leave, outpass and gate movement collections."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HostelRequestKind(str, Enum):
    LEAVE = "leave"
    OUTPASS = "outpass"


class HostelLeaveOutpassStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED_FOR_CORRECTION = "returned_for_correction"
    DEPARTURE_RECORDED = "departure_recorded"
    CURRENTLY_OUTSIDE = "currently_outside"
    RETURNED = "returned"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    CLOSED = "closed"


class HostelOutpassType(str, Enum):
    DAY = "day"
    SHORT = "short"
    OVERNIGHT = "overnight"
    WEEKEND = "weekend"
    EMERGENCY = "emergency"
    SPECIAL = "special"


class HostelLeaveType(Document):
    tenant_id: PydanticObjectId
    type_code: str
    label: str
    requires_document: bool = False
    max_duration_hours: int | None = None
    policy: dict[str, Any] = Field(default_factory=dict)
    active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_leave_types"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("type_code", ASCENDING)], unique=True, name="unique_leave_type"),
        ]


class HostelLeaveRequest(Document):
    tenant_id: PydanticObjectId
    request_id: str
    student_user_id: PydanticObjectId
    resident_id: str | None = None
    leave_type_code: str
    reason: str = Field(max_length=2000)
    destination: str | None = None
    departure_at: datetime
    expected_return_at: datetime
    emergency_contact_ref: str | None = None
    document_ref: str | None = None
    status: HostelLeaveOutpassStatus = HostelLeaveOutpassStatus.SUBMITTED
    approver_id: PydanticObjectId | None = None
    rejection_reason: str | None = None
    parent_approval_required: bool = False
    parent_approved: bool | None = None
    actual_return_at: datetime | None = None
    departure_recorded_at: datetime | None = None
    gate_staff_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_leave_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_leave_request"),
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)], name="leave_by_student"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("expected_return_at", ASCENDING)], name="leave_by_return"),
        ]


class HostelOutpassRequest(Document):
    """Outpass (legacy-compatible collection with extended fields)."""

    tenant_id: PydanticObjectId
    request_id: str
    student_user_id: PydanticObjectId
    resident_id: str | None = None
    outpass_type: HostelOutpassType = HostelOutpassType.DAY
    from_at: datetime
    to_at: datetime
    reason: str = Field(max_length=1000)
    destination: str | None = None
    status: HostelLeaveOutpassStatus = HostelLeaveOutpassStatus.PENDING_APPROVAL
    approver_id: PydanticObjectId | None = None
    rejection_reason: str | None = None
    departure_recorded_at: datetime | None = None
    actual_return_at: datetime | None = None
    gate_staff_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_outpass_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_outpass"),
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)], name="outpass_by_student"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("to_at", ASCENDING)], name="outpass_by_to"),
        ]


class HostelLeaveApprovalHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    request_kind: HostelRequestKind
    request_id: str
    decision: str
    actor_id: PydanticObjectId | None = None
    comment: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_leave_approval_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_leave_approval_hist"),
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING), ("created_at", DESCENDING)], name="approval_hist_by_req"),
        ]


class HostelGateMovement(Document):
    tenant_id: PydanticObjectId
    movement_id: str
    request_kind: HostelRequestKind
    request_id: str
    student_user_id: PydanticObjectId
    movement_type: str
    recorded_at: datetime = Field(default_factory=utcnow)
    gate_staff_id: PydanticObjectId | None = None
    note: str | None = None

    class Settings:
        name = "hostel_outpass_gate_movements"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("movement_id", ASCENDING)], unique=True, name="unique_gate_movement"),
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING), ("recorded_at", DESCENDING)], name="gate_by_request"),
        ]


class HostelResidentMovementHistory(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    resident_id: str | None = None
    event_type: str
    request_id: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_resident_movement_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("created_at", DESCENDING)], name="resident_movement_hist"),
        ]