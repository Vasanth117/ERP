"""Hostel maintenance and complaints collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HostelComplaintStatus(str, Enum):
    NEW = "new"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    AWAITING_PARTS = "awaiting_parts"
    RESOLVED = "resolved"
    REOPENED = "reopened"
    REJECTED = "rejected"
    CLOSED = "closed"


class HostelComplaintPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HostelMaintenanceTaskStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class HostelComplaintCategory(Document):
    tenant_id: PydanticObjectId
    category_code: str
    label: str
    default_priority: HostelComplaintPriority = HostelComplaintPriority.MEDIUM
    active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_complaint_categories"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("category_code", ASCENDING)], unique=True, name="unique_complaint_category"),
        ]


class HostelComplaint(Document):
    tenant_id: PydanticObjectId
    complaint_id: str
    student_user_id: PydanticObjectId | None = None
    resident_id: str | None = None
    hostel_code: str | None = None
    building_code: str
    block_code: str | None = None
    floor_id: str | None = None
    room_code: str
    bed_id: str | None = None
    category_code: str
    subject: str = Field(max_length=300)
    description: str = Field(max_length=4000)
    priority: HostelComplaintPriority = HostelComplaintPriority.MEDIUM
    status: HostelComplaintStatus = HostelComplaintStatus.SUBMITTED
    attachment_refs: list[str] = Field(default_factory=list)
    assigned_to_user_id: PydanticObjectId | None = None
    assigned_department: str | None = None
    supervisor_user_id: PydanticObjectId | None = None
    expected_completion: date | None = None
    resolution_target: datetime | None = None
    resolved_at: datetime | None = None
    reporter_id: PydanticObjectId | None = None
    escalated: bool = False
    escalation_level: int = 0
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_complaints"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("complaint_id", ASCENDING)], unique=True, name="unique_hostel_complaint"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("priority", DESCENDING)], name="complaints_by_status"),
            IndexModel([("tenant_id", ASCENDING), ("room_code", ASCENDING), ("category_code", ASCENDING)], name="complaints_by_room"),
        ]


class HostelComplaintAssignment(Document):
    tenant_id: PydanticObjectId
    assignment_id: str
    complaint_id: str
    assignee_user_id: PydanticObjectId | None = None
    department: str | None = None
    supervisor_user_id: PydanticObjectId | None = None
    work_instructions: str | None = None
    materials_required: list[str] = Field(default_factory=list)
    expected_completion: date | None = None
    reassigned_from: str | None = None
    reason: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_complaint_assignments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("assignment_id", ASCENDING)], unique=True, name="unique_complaint_assignment"),
            IndexModel([("tenant_id", ASCENDING), ("complaint_id", ASCENDING), ("created_at", DESCENDING)], name="assignments_by_complaint"),
        ]


class HostelComplaintHistory(Document):
    tenant_id: PydanticObjectId
    complaint_id: str
    action: str
    from_status: str | None = None
    to_status: str | None = None
    detail: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_complaint_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("complaint_id", ASCENDING), ("created_at", DESCENDING)], name="complaint_history"),
        ]


class HostelMaintenanceTask(Document):
    tenant_id: PydanticObjectId
    task_id: str
    complaint_id: str | None = None
    task_type: str = "corrective"
    title: str
    description: str | None = None
    assignee_user_id: PydanticObjectId | None = None
    status: HostelMaintenanceTaskStatus = HostelMaintenanceTaskStatus.SCHEDULED
    expected_completion: date | None = None
    completed_at: datetime | None = None
    repair_evidence_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_maintenance_tasks"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("task_id", ASCENDING)], unique=True, name="unique_maintenance_task"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="tasks_by_status"),
        ]


class HostelMaintenanceSchedule(Document):
    tenant_id: PydanticObjectId
    schedule_id: str
    schedule_type: str
    hostel_code: str | None = None
    building_code: str | None = None
    title: str
    scheduled_date: date
    assignee_user_id: PydanticObjectId | None = None
    status: HostelMaintenanceTaskStatus = HostelMaintenanceTaskStatus.SCHEDULED
    inspection_remarks: str | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_maintenance_schedules"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("schedule_id", ASCENDING)], unique=True, name="unique_maint_schedule"),
            IndexModel([("tenant_id", ASCENDING), ("scheduled_date", DESCENDING)], name="schedules_by_date"),
        ]


class HostelFacilityUnavailabilityHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    complaint_id: str | None = None
    facility_type: str
    hostel_code: str | None = None
    building_code: str
    block_code: str | None = None
    room_code: str | None = None
    bed_id: str | None = None
    unavailable: bool = True
    reason: str
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_facility_unavailability_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("history_id", ASCENDING)], unique=True, name="unique_facility_unavail"),
            IndexModel([("tenant_id", ASCENDING), ("bed_id", ASCENDING), ("created_at", DESCENDING)], name="unavail_by_bed"),
        ]


class HostelComplaintFeedback(Document):
    tenant_id: PydanticObjectId
    feedback_id: str
    complaint_id: str
    student_user_id: PydanticObjectId
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)
    reopen_requested: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_complaint_feedback"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("feedback_id", ASCENDING)], unique=True, name="unique_complaint_feedback"),
            IndexModel([("tenant_id", ASCENDING), ("complaint_id", ASCENDING)], unique=True, name="one_feedback_per_complaint"),
        ]


class HostelMaintenanceRequest(Document):
    """Legacy maintenance requests (college-admin compatibility)."""

    tenant_id: PydanticObjectId
    request_id: str
    building_code: str
    room_code: str
    description: str
    status: str = "open"
    actor_id: PydanticObjectId | None = None
    complaint_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_maintenance_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_hostel_maintenance"),
        ]