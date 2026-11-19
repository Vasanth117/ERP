"""HR recruitment API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, EmailStr

from app.modules.hr.enums import (
    HrApplicationPipelineStage,
    HrEmploymentOfferStatus,
    HrInterviewStatus,
    HrJobOpeningStatus,
    HrJobRequisitionStatus,
)
from app.modules.hr.recruitment_models import (
    HrCandidate,
    HrEmploymentOffer,
    HrInterviewFeedback,
    HrInterviewSession,
    HrJobApplication,
    HrJobOpening,
    HrJobRequisition,
)


class JobRequisitionCreate(BaseModel):
    requisition_code: str = Field(min_length=1, max_length=64)
    job_title: str = Field(min_length=1, max_length=200)
    requested_by_user_id: str | None = None
    department_id: str
    campus_id: str | None = None
    positions_required: int = Field(ge=1, default=1)
    employment_type: str = Field(min_length=1, max_length=64)
    work_location_id: str | None = None
    job_description: str = Field(min_length=1, max_length=12000)
    qualifications: str = ""
    skills: list[str] = Field(default_factory=list)
    experience_requirements: str = ""
    salary_range: dict[str, Any] | None = None
    reason_for_hiring: str = Field(min_length=1, max_length=2000)
    expected_joining_date: date | None = None
    hiring_priority: str = "normal"


class JobRequisitionRead(BaseModel):
    id: str
    requisition_code: str
    job_title: str
    department_id: str
    campus_id: str | None
    positions_required: int
    employment_type: str
    status: HrJobRequisitionStatus
    requested_by: str
    created_at: datetime

    @classmethod
    def from_document(cls, doc: HrJobRequisition) -> "JobRequisitionRead":
        return cls(
            id=str(doc.id),
            requisition_code=doc.requisition_code,
            job_title=doc.job_title,
            department_id=str(doc.department_id),
            campus_id=str(doc.campus_id) if doc.campus_id else None,
            positions_required=doc.positions_required,
            employment_type=doc.employment_type,
            status=doc.status,
            requested_by=str(doc.requested_by),
            created_at=doc.created_at,
        )


class RequisitionDecision(BaseModel):
    decision: str = Field(pattern="^(approve|reject|return|hr_approve)$")
    note: str | None = Field(default=None, max_length=2000)
    approved_position_ref: str | None = None


class JobOpeningCreate(BaseModel):
    opening_code: str = Field(min_length=1, max_length=64)
    requisition_id: str
    application_deadline: datetime | None = None
    vacancies: int | None = Field(default=None, ge=1)
    selection_criteria: str = ""
    interview_stages: list[str] = Field(default_factory=list)


class JobOpeningUpdate(BaseModel):
    job_description: str | None = None
    qualifications: str | None = None
    selection_criteria: str | None = None
    interview_stages: list[str] | None = None
    application_deadline: datetime | None = None
    vacancies: int | None = Field(default=None, ge=1)


class JobOpeningRead(BaseModel):
    id: str
    opening_code: str
    requisition_id: str
    job_title: str
    department_id: str
    status: HrJobOpeningStatus
    vacancies: int
    filled_count: int
    application_deadline: datetime | None
    published_at: datetime | None

    @classmethod
    def from_document(cls, doc: HrJobOpening) -> "JobOpeningRead":
        return cls(
            id=str(doc.id),
            opening_code=doc.opening_code,
            requisition_id=str(doc.requisition_id),
            job_title=doc.job_title,
            department_id=str(doc.department_id),
            status=doc.status,
            vacancies=doc.vacancies,
            filled_count=doc.filled_count,
            application_deadline=doc.application_deadline,
            published_at=doc.published_at,
        )


class CandidateUpsert(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = None
    address: str | None = None
    qualifications: list[dict[str, Any]] = Field(default_factory=list)
    work_experience: list[dict[str, Any]] = Field(default_factory=list)
    previous_employment: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    resume_file_ref: str | None = None
    supporting_document_refs: list[str] = Field(default_factory=list)


class CandidateRead(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str | None
    converted_employee_user_id: str | None

    @classmethod
    def from_document(cls, doc: HrCandidate) -> "CandidateRead":
        return cls(
            id=str(doc.id),
            full_name=doc.full_name,
            email=doc.email,
            phone=doc.phone,
            converted_employee_user_id=str(doc.converted_employee_user_id) if doc.converted_employee_user_id else None,
        )


class ApplicationCreate(BaseModel):
    job_opening_id: str
    candidate_id: str
    application_source: str = "portal"
    document_refs: list[str] = Field(default_factory=list)


class ApplicationStageTransition(BaseModel):
    target_stage: HrApplicationPipelineStage
    reason: str | None = Field(default=None, max_length=2000)


class ApplicationReviewNoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=4000)
    visible_to_candidate: bool = False


class ApplicationAssignRecruiter(BaseModel):
    recruiter_user_id: str


class ApplicationRead(BaseModel):
    id: str
    application_code: str
    job_opening_id: str
    candidate_id: str
    stage: HrApplicationPipelineStage
    assigned_recruiter_id: str | None
    applied_at: datetime

    @classmethod
    def from_document(cls, doc: HrJobApplication) -> "ApplicationRead":
        return cls(
            id=str(doc.id),
            application_code=doc.application_code,
            job_opening_id=str(doc.job_opening_id),
            candidate_id=str(doc.candidate_id),
            stage=doc.stage,
            assigned_recruiter_id=str(doc.assigned_recruiter_id) if doc.assigned_recruiter_id else None,
            applied_at=doc.applied_at,
        )


class InterviewSchedule(BaseModel):
    application_id: str
    scheduled_at: datetime
    mode: str = Field(min_length=1, max_length=32)
    location_or_meeting: str = Field(min_length=1, max_length=1000)
    panel_member_ids: list[str] = Field(default_factory=list)
    interviewer_ids: list[str] = Field(default_factory=list)


class InterviewReschedule(BaseModel):
    scheduled_at: datetime
    reason: str = Field(min_length=1, max_length=2000)


class InterviewFeedbackSubmit(BaseModel):
    criteria_scores: dict[str, float] = Field(default_factory=dict)
    comments: str = ""
    recommendation: str = "neutral"


class InterviewRead(BaseModel):
    id: str
    interview_code: str
    application_id: str
    scheduled_at: datetime
    status: HrInterviewStatus

    @classmethod
    def from_document(cls, doc: HrInterviewSession) -> "InterviewRead":
        return cls(
            id=str(doc.id),
            interview_code=doc.interview_code,
            application_id=str(doc.application_id),
            scheduled_at=doc.scheduled_at,
            status=doc.status,
        )


class OfferCreate(BaseModel):
    application_id: str
    designation: str
    department_id: str
    employment_type: str
    salary_details: dict[str, Any] = Field(default_factory=dict)
    expected_joining_date: date | None = None
    offer_valid_until: date | None = None


class OfferDecision(BaseModel):
    decision: str = Field(pattern="^(submit_approval|approve|issue|accept|decline|withdraw|remind)$")
    note: str | None = None


class OfferRead(BaseModel):
    id: str
    offer_code: str
    application_id: str
    candidate_id: str
    status: HrEmploymentOfferStatus

    @classmethod
    def from_document(cls, doc: HrEmploymentOffer) -> "OfferRead":
        return cls(
            id=str(doc.id),
            offer_code=doc.offer_code,
            application_id=str(doc.application_id),
            candidate_id=str(doc.candidate_id),
            status=doc.status,
        )


class RecruitmentDashboardStats(BaseModel):
    total_job_openings: int = 0
    active_job_openings: int = 0
    draft_job_openings: int = 0
    draft_requisitions: int = 0
    active_requisitions: int = 0
    applications_received: int = 0
    new_applications: int = 0
    under_review: int = 0
    shortlisted: int = 0
    in_assessment: int = 0
    interviews_scheduled: int = 0
    awaiting_feedback: int = 0
    selected: int = 0
    rejected: int = 0
    withdrawn: int = 0
    offers_pending_approval: int = 0
    offers_issued: int = 0
    offers_accepted: int = 0
    offers_declined: int = 0
    positions_filled: int = 0


class RecruitmentDashboardFilters(BaseModel):
    department_id: str | None = None
    job_opening_id: str | None = None
    requisition_id: str | None = None
    job_title: str | None = None
    campus_id: str | None = None
    application_stage: HrApplicationPipelineStage | None = None
    period_from: date | None = None
    period_to: date | None = None


class JobRequisitionDetailRead(JobRequisitionRead):
    job_description: str
    qualifications: str
    skills: list[str]
    experience_requirements: str
    reason_for_hiring: str
    hiring_priority: str
    hr_review_note: str | None = None
    management_decision_note: str | None = None
    recruitment_progress: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_document(cls, doc: HrJobRequisition, *, recruitment_progress: dict) -> "JobRequisitionDetailRead":
        base = JobRequisitionRead.from_document(doc)
        return cls(
            **base.model_dump(),
            job_description=doc.job_description,
            qualifications=doc.qualifications,
            skills=doc.skills,
            experience_requirements=doc.experience_requirements,
            reason_for_hiring=doc.reason_for_hiring,
            hiring_priority=doc.hiring_priority,
            hr_review_note=doc.hr_review_note,
            management_decision_note=doc.management_decision_note,
            recruitment_progress=recruitment_progress,
        )


class CandidateDetailRead(CandidateRead):
    address: str | None = None
    qualifications: list[dict[str, Any]] = Field(default_factory=list)
    work_experience: list[dict[str, Any]] = Field(default_factory=list)
    previous_employment: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    resume_file_ref: str | None = None
    supporting_document_refs: list[str] = Field(default_factory=list)

    @classmethod
    def from_document(cls, doc: HrCandidate) -> "CandidateDetailRead":
        base = CandidateRead.from_document(doc)
        refs = doc.metadata.get("supporting_document_refs") if isinstance(doc.metadata, dict) else []
        return cls(
            **base.model_dump(),
            address=doc.address,
            qualifications=doc.qualifications,
            work_experience=doc.work_experience,
            previous_employment=doc.previous_employment,
            skills=doc.skills,
            resume_file_ref=doc.resume_file_ref,
            supporting_document_refs=list(refs or []),
        )


class ApplicationHistoryItem(BaseModel):
    from_stage: str | None
    to_stage: str
    reason: str | None
    actor_id: str | None
    created_at: datetime

    @classmethod
    def from_document(cls, doc) -> "ApplicationHistoryItem":
        return cls(
            from_stage=doc.from_stage,
            to_stage=doc.to_stage,
            reason=doc.reason,
            actor_id=str(doc.actor_id) if doc.actor_id else None,
            created_at=doc.created_at,
        )


class ApplicationWorkspaceRead(BaseModel):
    application: ApplicationRead
    candidate: CandidateDetailRead
    opening: JobOpeningRead
    internal_notes: list[str]
    stage_history: list[ApplicationHistoryItem]
    requirement_fit_percent: float


class ApplicationRequestInfo(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class InterviewDetailRead(BaseModel):
    id: str
    interview_code: str
    application_id: str
    scheduled_at: datetime
    status: HrInterviewStatus
    mode: str
    location_or_meeting: str
    candidate: CandidateRead | CandidateDetailRead | None = None
    feedback_count: int = 0

    @classmethod
    def from_session(cls, session: HrInterviewSession, *, candidate, feedback_count: int) -> "InterviewDetailRead":
        return cls(
            id=str(session.id),
            interview_code=session.interview_code,
            application_id=str(session.application_id),
            scheduled_at=session.scheduled_at,
            status=session.status,
            mode=session.mode,
            location_or_meeting=session.location_or_meeting,
            candidate=candidate,
            feedback_count=feedback_count,
        )


class ConsolidatedEvaluationRead(BaseModel):
    application_id: str
    feedback_count: int
    averaged_scores: dict[str, float]
    recommendations: list[str]
    suggested_decision: str


class OfferRevise(BaseModel):
    designation: str | None = None
    salary_details: dict[str, Any] | None = None
    expected_joining_date: date | None = None
    offer_valid_until: date | None = None


class PipelineConfigRead(BaseModel):
    stages: list[str]
    application_channels: list[str]
    evaluation_criteria: list[str]
    updated_at: datetime


class PipelineConfigUpdate(BaseModel):
    stages: list[str] = Field(min_length=1)
    application_channels: list[str] | None = None
    evaluation_criteria: list[str] | None = None


class ChannelApplicationCreate(BaseModel):
    job_opening_id: str
    candidate: CandidateUpsert
    application_source: str = "portal"
    document_refs: list[str] = Field(default_factory=list)


class CandidateComparisonItem(BaseModel):
    application_id: str
    application_code: str
    candidate_id: str
    candidate_name: str
    stage: HrApplicationPipelineStage
    requirement_fit_percent: float


class ApplicationRecruitmentHistory(BaseModel):
    stage_history: list[ApplicationHistoryItem]
    recruiter_assignments: list[dict[str, Any]]
    interviews: list[dict[str, Any]]
    interview_feedback: list[dict[str, Any]]
    offers: list[dict[str, Any]]


class RecruitmentReportRead(BaseModel):
    department_application_counts: dict[str, int]
    opening_performance: list[dict[str, Any]]
    time_to_fill: list[dict[str, Any]]
    recruitment_sources: dict[str, int]