"""Department Admin phase 7 — requests hub and resources."""

from datetime import datetime, date
from enum import Enum

from pydantic import BaseModel, Field, field_validator

from app.modules.department_admin.models import DepartmentRequestStatus, DepartmentResourceIssueStatus, DepartmentResourceType


class UnifiedRequestStatus(str, Enum):
    PENDING = "pending"
    AWAITING_INFORMATION = "awaiting_information"
    FORWARDED = "forwarded"
    ESCALATED = "escalated"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class RequestFilters(BaseModel):
    category: str | None = None
    status: UnifiedRequestStatus | None = None
    requester_user_id: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None

    @field_validator("date_to")
    @classmethod
    def range_ok(cls, date_to: datetime | None, info) -> datetime | None:
        start = info.data.get("date_from")
        if start and date_to and start > date_to:
            raise ValueError("date_from must be on or before date_to")
        return date_to


class UnifiedRequestListItem(BaseModel):
    request_id: str
    category: str
    status: UnifiedRequestStatus
    requester_user_id: str
    title: str
    reason: str | None
    submitted_at: datetime
    due_date: datetime | None = None
    subject_ref: dict = Field(default_factory=dict)


class RequestSummaryRead(BaseModel):
    total: int
    pending: int
    awaiting_review: int
    approved: int
    rejected: int
    forwarded_or_escalated: int
    overdue: int
    by_category: dict[str, int]


class RequestDetailRead(BaseModel):
    request_id: str
    category: str
    status: UnifiedRequestStatus
    requester_user_id: str
    title: str
    reason: str | None
    submitted_at: datetime
    due_date: datetime | None = None
    assigned_reviewer_user_id: str | None = None
    escalation_level: int = 0
    subject_ref: dict = Field(default_factory=dict)
    canonical: dict = Field(default_factory=dict)
    coordination_flags: dict = Field(default_factory=dict)


class RequestDecisionBody(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)
    idempotency_key: str | None = Field(default=None, max_length=128)


class RequestRejectBody(RequestDecisionBody):
    rejection_reason: str = Field(min_length=2, max_length=500)


class RequestForwardBody(RequestDecisionBody):
    forward_target: str = Field(description="college_admin|hr|examination_cell")
    due_date: datetime | None = None


class RequestEscalateBody(RequestDecisionBody):
    due_date: datetime | None = None


class RequestHistoryRecordRead(BaseModel):
    action: str
    actor_user_id: str
    comment: str | None
    forward_target: str | None = None
    previous_state: str | None = None
    new_state: str | None = None
    created_at: datetime


class RequestHistoryRead(BaseModel):
    request_id: str
    canonical_history: list[dict] = Field(default_factory=list)
    coordination_history: list[RequestHistoryRecordRead] = Field(default_factory=list)


class ResourceDirectoryItemRead(BaseModel):
    resource_id: str
    name: str
    resource_type: str
    location: str | None = None
    capacity: int | None = None
    operational_status: str = "active"
    ownership: str = "college"
    source: str
    metadata: dict = Field(default_factory=dict)


class ResourceAvailabilityQuery(BaseModel):
    resource_type: str | None = None
    resource_ref: str | None = None
    day: date | None = None


class ResourceAvailabilityRead(BaseModel):
    resource_id: str
    available: bool
    conflicts: list[dict[str, str]] = Field(default_factory=list)
    note: str | None = None


class ResourceRequestCreate(BaseModel):
    resource_type: DepartmentResourceType
    resource_ref: str = Field(min_length=1, max_length=128)
    resource_name: str | None = Field(default=None, max_length=200)
    quantity: int = Field(default=1, ge=1, le=500)
    needed_from: datetime
    needed_until: datetime
    urgency: str = Field(default="normal", max_length=16)
    reason: str = Field(min_length=2, max_length=2000)
    idempotency_key: str | None = Field(default=None, max_length=128)

    @field_validator("needed_until")
    @classmethod
    def window_ok(cls, ends: datetime, info) -> datetime:
        start = info.data.get("needed_from")
        if start and ends <= start:
            raise ValueError("needed_until must be after needed_from")
        return ends


class ResourceRequestRead(BaseModel):
    request_id: str
    resource_type: str
    resource_ref: str
    resource_name: str | None
    quantity: int
    needed_from: datetime
    needed_until: datetime
    urgency: str
    reason: str
    status: DepartmentRequestStatus
    requested_by: str
    created_at: datetime


class ResourceIssueCreate(BaseModel):
    resource_type: DepartmentResourceType
    resource_ref: str = Field(min_length=1, max_length=128)
    issue_type: str = Field(min_length=2, max_length=64)
    description: str = Field(min_length=2, max_length=2000)
    idempotency_key: str | None = Field(default=None, max_length=128)


class ResourceIssueRead(BaseModel):
    issue_id: str
    resource_type: str
    resource_ref: str
    issue_type: str
    description: str
    status: DepartmentResourceIssueStatus
    reported_by: str
    created_at: datetime


class ResourceUtilizationRead(BaseModel):
    classrooms_listed: int
    laboratories_listed: int
    equipment_listed: int
    pending_resource_requests: int
    open_resource_issues: int
    timetable_booking_hints: int
    advisory: str