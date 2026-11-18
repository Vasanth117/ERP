"""Department Admin phase 10 — helpdesk and placement/research."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.department_admin.models import (
    DepartmentHelpdeskEscalationTarget,
    DepartmentHelpdeskPriority,
    DepartmentHelpdeskStatus,
    DepartmentInternshipStatus,
    DepartmentPlacementActivityStatus,
    DepartmentProjectCoordinationStatus,
    DepartmentProjectReviewStatus,
    DepartmentResearchProjectStatus,
)


class HelpdeskFilters(BaseModel):
    q: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, max_length=64)
    priority: DepartmentHelpdeskPriority | None = None
    status: DepartmentHelpdeskStatus | None = None
    assigned_user_id: str | None = None
    requester_user_id: str | None = None
    overdue_only: bool = False
    escalated_only: bool = False
    date_from: datetime | None = None
    date_to: datetime | None = None

    @field_validator("date_to")
    @classmethod
    def range_ok(cls, date_to: datetime | None, info) -> datetime | None:
        start = info.data.get("date_from")
        if start and date_to and start > date_to:
            raise ValueError("date_from must be on or before date_to")
        return date_to


class HelpdeskTicketCreate(BaseModel):
    title: str = Field(max_length=200)
    description: str = Field(max_length=8000)
    category: str = Field(max_length=64)
    priority: DepartmentHelpdeskPriority = DepartmentHelpdeskPriority.NORMAL
    affected_module: str | None = Field(default=None, max_length=64)
    affected_record_type: str | None = Field(default=None, max_length=64)
    affected_record_id: str | None = Field(default=None, max_length=128)
    requester_user_id: str | None = None
    document_ids: list[str] = Field(default_factory=list)
    preferred_resolution_at: datetime | None = None
    idempotency_key: str | None = Field(default=None, max_length=128)


class HelpdeskTicketUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=8000)
    category: str | None = Field(default=None, max_length=64)
    priority: DepartmentHelpdeskPriority | None = None
    affected_module: str | None = Field(default=None, max_length=64)
    affected_record_type: str | None = Field(default=None, max_length=64)
    affected_record_id: str | None = Field(default=None, max_length=128)
    status: DepartmentHelpdeskStatus | None = None


class HelpdeskAssignBody(BaseModel):
    assigned_user_id: str | None = None
    assigned_team: str | None = Field(default=None, max_length=64)
    reason: str | None = Field(default=None, max_length=500)


class HelpdeskCommentBody(BaseModel):
    body: str = Field(max_length=8000)
    is_internal: bool = False
    attachment_document_ids: list[str] = Field(default_factory=list)


class HelpdeskEscalateBody(BaseModel):
    escalation_target: DepartmentHelpdeskEscalationTarget
    note: str | None = Field(default=None, max_length=1000)


class HelpdeskResolveBody(BaseModel):
    resolution_note: str = Field(max_length=4000)


class HelpdeskReopenBody(BaseModel):
    reason: str = Field(max_length=500)


class HelpdeskTicketRead(BaseModel):
    ticket_id: str
    ticket_number: str
    title: str
    description: str
    category: str
    priority: DepartmentHelpdeskPriority
    affected_module: str | None
    affected_record_type: str | None
    affected_record_id: str | None
    requester_user_id: str
    assigned_user_id: str | None
    assigned_team: str | None
    status: DepartmentHelpdeskStatus
    escalation_target: DepartmentHelpdeskEscalationTarget | None
    document_ids: list[str]
    preferred_resolution_at: datetime | None
    first_response_due_at: datetime | None
    resolution_due_at: datetime | None
    is_overdue: bool
    resolved_at: datetime | None
    resolved_by: str | None
    resolution_note: str | None
    created_by: str
    created_at: datetime
    updated_at: datetime


class HelpdeskCommentRead(BaseModel):
    comment_id: str
    body: str
    is_internal: bool
    author_user_id: str
    attachment_document_ids: list[str]
    created_at: datetime


class HelpdeskHistoryRead(BaseModel):
    event_id: str
    change_type: str
    actor_user_id: str | None
    summary: str | None
    before: dict
    after: dict
    created_at: datetime


class HelpdeskSummaryRead(BaseModel):
    total: int
    open: int
    assigned: int
    in_progress: int
    waiting_for_information: int
    escalated: int
    resolved: int
    closed: int
    overdue: int
    by_category: dict[str, int]
    advisory: str
    generated_at: datetime


class PlacementOverviewRead(BaseModel):
    student_count: int
    placement_activities: int
    scheduled_activities: int
    active_internships: int
    project_records: int
    research_projects: int
    pending_reviews: int
    advisory: str
    generated_at: datetime


class PlacementStudentRead(BaseModel):
    student_user_id: str
    programme_code: str | None
    batch_label: str | None
    section_code: str | None
    placement_follow_ups: int
    internship_count: int
    preparation_note: str


class PlacementActivityCreate(BaseModel):
    title: str = Field(max_length=200)
    activity_type: str = Field(max_length=64)
    description: str | None = Field(default=None, max_length=4000)
    academic_year_label: str | None = Field(default=None, max_length=32)
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    scheduled_at: datetime | None = None
    participant_count: int = Field(default=0, ge=0)
    idempotency_key: str | None = Field(default=None, max_length=128)


class PlacementActivityRead(BaseModel):
    activity_id: str
    title: str
    activity_type: str
    description: str | None
    academic_year_label: str | None
    programme_code: str | None
    batch_label: str | None
    scheduled_at: datetime | None
    status: DepartmentPlacementActivityStatus
    calendar_event_id: str | None
    coordinator_user_id: str
    participant_count: int
    created_at: datetime


class InternshipCreate(BaseModel):
    title: str = Field(max_length=200)
    organization_name: str = Field(max_length=200)
    organization_website: str | None = Field(default=None, max_length=256)
    student_user_id: str
    faculty_coordinator_id: str
    duration_label: str | None = Field(default=None, max_length=64)
    academic_year_label: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=2000)
    document_ids: list[str] = Field(default_factory=list)
    idempotency_key: str | None = Field(default=None, max_length=128)


class InternshipRead(BaseModel):
    internship_id: str
    title: str
    organization_name: str
    organization_website: str | None
    organization_verified: bool
    student_user_id: str
    faculty_coordinator_id: str
    duration_label: str | None
    academic_year_label: str | None
    status: DepartmentInternshipStatus
    document_ids: list[str]
    notes: str | None
    created_at: datetime


class ProjectCoordinationRead(BaseModel):
    project_id: str
    title: str
    project_type: str
    student_user_ids: list[str]
    faculty_guide_id: str
    lms_assignment_id: str | None
    academic_year_label: str | None
    programme_code: str | None
    milestones: list[dict]
    status: DepartmentProjectCoordinationStatus
    submission_status: str | None
    source: str


class ProjectReviewCreate(BaseModel):
    review_type: str = Field(max_length=64)
    milestone_label: str | None = Field(default=None, max_length=128)
    scheduled_at: datetime
    reviewer_faculty_ids: list[str] = Field(default_factory=list)
    feedback_ref: str | None = Field(default=None, max_length=512)


class ProjectReviewRead(BaseModel):
    review_id: str
    project_id: str
    review_type: str
    milestone_label: str | None
    scheduled_at: datetime
    reviewer_faculty_ids: list[str]
    status: DepartmentProjectReviewStatus
    feedback_ref: str | None
    calendar_event_id: str | None


class ResearchOverviewRead(BaseModel):
    active_projects: int
    completed_projects: int
    faculty_leads: int
    student_participants: int
    upcoming_seminars: int
    advisory: str
    generated_at: datetime


class ResearchProjectCreate(BaseModel):
    title: str = Field(max_length=200)
    faculty_lead_id: str
    student_participant_ids: list[str] = Field(default_factory=list)
    academic_year_label: str | None = Field(default=None, max_length=32)
    publication_refs: list[str] = Field(default_factory=list)
    seminar_scheduled_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=4000)
    document_ids: list[str] = Field(default_factory=list)


class ResearchProjectRead(BaseModel):
    project_id: str
    title: str
    faculty_lead_id: str
    student_participant_ids: list[str]
    status: DepartmentResearchProjectStatus
    publication_refs: list[str]
    seminar_scheduled_at: datetime | None
    academic_year_label: str | None
    notes: str | None
    created_at: datetime


class ResearchEventRead(BaseModel):
    event_id: str
    title: str
    category: str
    starts_at: datetime
    ends_at: datetime
    status: str


class PlacementResearchReportRead(BaseModel):
    placement_activities: int
    internships_by_status: dict[str, int]
    projects_by_status: dict[str, int]
    research_by_status: dict[str, int]
    reviews_pending: int
    lms_capstone_assignments: int
    generated_at: datetime
    advisory: str