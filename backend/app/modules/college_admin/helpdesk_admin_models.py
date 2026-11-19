"""Institution helpdesk and support collections."""

from datetime import datetime
from enum import Enum

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class SupportTicketStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_INFORMATION = "waiting_for_information"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class SupportPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RequesterAudience(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    EMPLOYEE = "employee"
    PARENT = "parent"
    INSTITUTION = "institution"


class InstitutionSupportCategory(Document):
    tenant_id: PydanticObjectId
    category_code: str
    title: str
    module_key: str
    issue_type: str
    active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_support_categories"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("category_code", ASCENDING)], unique=True, name="unique_support_category"),
        ]


class InstitutionSupportSlaPolicy(Document):
    tenant_id: PydanticObjectId
    policy_id: str = "default"
    first_response_hours: int = Field(default=24, ge=1)
    resolution_hours: int = Field(default=72, ge=1)
    priority_multipliers: dict[str, float] = Field(default_factory=lambda: {"urgent": 0.25, "high": 0.5, "normal": 1.0, "low": 1.5})
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_support_sla_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("policy_id", ASCENDING)], unique=True, name="unique_sla_policy"),
        ]


class InstitutionSupportTicket(Document):
    tenant_id: PydanticObjectId
    ticket_id: str
    ticket_number: str
    title: str = Field(max_length=200)
    description: str = Field(max_length=8000)
    category_code: str
    module_key: str
    issue_type: str
    priority: SupportPriority = SupportPriority.NORMAL
    requester_user_id: PydanticObjectId
    requester_audience: RequesterAudience = RequesterAudience.INSTITUTION
    assigned_user_id: PydanticObjectId | None = None
    assigned_team: str | None = None
    status: SupportTicketStatus = SupportTicketStatus.OPEN
    first_response_due_at: datetime | None = None
    resolution_due_at: datetime | None = None
    resolved_at: datetime | None = None
    resolved_by: PydanticObjectId | None = None
    resolution_detail: str | None = Field(default=None, max_length=4000)
    reopen_count: int = 0
    idempotency_key: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_support_tickets"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("ticket_id", ASCENDING)], unique=True, name="unique_support_ticket"),
            IndexModel([("tenant_id", ASCENDING), ("ticket_number", ASCENDING)], unique=True, name="unique_ticket_number"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING), ("updated_at", DESCENDING)], name="tickets_by_status"),
            IndexModel([("tenant_id", ASCENDING), ("requester_user_id", ASCENDING), ("created_at", DESCENDING)], name="tickets_by_requester"),
            IndexModel([("tenant_id", ASCENDING), ("assigned_user_id", ASCENDING), ("status", ASCENDING)], name="tickets_by_assignee"),
        ]


class InstitutionSupportAssignment(Document):
    tenant_id: PydanticObjectId
    assignment_id: str
    ticket_id: str
    assignee_user_id: PydanticObjectId | None = None
    assigned_team: str | None = None
    assigned_by: PydanticObjectId
    active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_support_assignments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("assignment_id", ASCENDING)], unique=True, name="unique_support_assignment"),
            IndexModel([("tenant_id", ASCENDING), ("ticket_id", ASCENDING), ("active", ASCENDING)], name="assignments_by_ticket"),
        ]


class InstitutionSupportComment(Document):
    tenant_id: PydanticObjectId
    comment_id: str
    ticket_id: str
    author_id: PydanticObjectId
    body: str = Field(max_length=4000)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_support_comments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("ticket_id", ASCENDING), ("created_at", ASCENDING)], name="comments_by_ticket"),
        ]


class InstitutionSupportInternalNote(Document):
    tenant_id: PydanticObjectId
    note_id: str
    ticket_id: str
    author_id: PydanticObjectId
    body: str = Field(max_length=4000)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_support_internal_notes"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("ticket_id", ASCENDING), ("created_at", DESCENDING)], name="internal_notes_by_ticket"),
        ]


class InstitutionSupportAttachment(Document):
    tenant_id: PydanticObjectId
    attachment_id: str
    ticket_id: str
    file_name: str
    mime_type: str
    storage_key: str
    size_bytes: int = Field(ge=1)
    uploaded_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_support_attachments"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("attachment_id", ASCENDING)], unique=True, name="unique_support_attachment"),
        ]


class InstitutionSupportEscalation(Document):
    tenant_id: PydanticObjectId
    escalation_id: str
    ticket_id: str
    reason: str
    target_team: str
    escalated_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_support_escalations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("ticket_id", ASCENDING), ("created_at", DESCENDING)], name="escalations_by_ticket"),
        ]


class InstitutionSupportHistory(Document):
    tenant_id: PydanticObjectId
    ticket_id: str
    change_type: str
    actor_id: PydanticObjectId | None = None
    summary: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_support_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("ticket_id", ASCENDING), ("created_at", DESCENDING)], name="support_history"),
        ]


class InstitutionSupportFeedback(Document):
    tenant_id: PydanticObjectId
    ticket_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
    submitted_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_support_feedback"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("ticket_id", ASCENDING)], unique=True, name="unique_support_feedback"),
        ]