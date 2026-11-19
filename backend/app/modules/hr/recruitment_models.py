"""HR recruitment domain documents."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hr.enums import (
    HrApplicationPipelineStage,
    HrEmploymentOfferStatus,
    HrInterviewStatus,
    HrJobOpeningStatus,
    HrJobRequisitionStatus,
)


DEFAULT_EVALUATION_CRITERIA = (
    "technical_knowledge",
    "subject_expertise",
    "communication",
    "experience",
    "qualifications",
    "teaching_demonstration",
    "practical_assessment",
    "overall_suitability",
)

DEFAULT_APPLICATION_CHANNELS = ("portal", "referral", "campus_drive", "walk_in", "agency")


class HrRecruitmentPipelineConfig(Document):
    tenant_id: PydanticObjectId
    stages: list[str] = Field(default_factory=list)
    application_channels: list[str] = Field(default_factory=lambda: list(DEFAULT_APPLICATION_CHANNELS))
    evaluation_criteria: list[str] = Field(default_factory=lambda: list(DEFAULT_EVALUATION_CRITERIA))
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_recruitment_pipeline_config"
        indexes = [IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_hr_pipeline_config")]


class HrJobRequisition(Document):
    tenant_id: PydanticObjectId
    requisition_code: str = Field(max_length=64)
    job_title: str = Field(max_length=200)
    department_id: PydanticObjectId
    campus_id: PydanticObjectId | None = None
    positions_required: int = Field(ge=1, default=1)
    employment_type: str = Field(max_length=64)
    work_location_id: PydanticObjectId | None = None
    job_description: str = Field(max_length=12000)
    qualifications: str = Field(max_length=4000, default="")
    skills: list[str] = Field(default_factory=list)
    experience_requirements: str = Field(max_length=2000, default="")
    salary_range: dict[str, Any] | None = None
    reason_for_hiring: str = Field(max_length=2000)
    expected_joining_date: date | None = None
    hiring_priority: str = Field(max_length=32, default="normal")
    requested_by: PydanticObjectId
    status: HrJobRequisitionStatus = HrJobRequisitionStatus.DRAFT
    hr_review_note: str | None = Field(default=None, max_length=2000)
    management_decision_note: str | None = Field(default=None, max_length=2000)
    approved_position_ref: str | None = Field(default=None, max_length=128)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_job_requisitions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("requisition_code", ASCENDING)],
                unique=True,
                name="unique_hr_requisition_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="hr_requisitions_by_status"),
        ]


class HrJobOpening(Document):
    tenant_id: PydanticObjectId
    opening_code: str = Field(max_length=64)
    requisition_id: PydanticObjectId
    job_title: str = Field(max_length=200)
    department_id: PydanticObjectId
    campus_id: PydanticObjectId | None = None
    vacancies: int = Field(ge=1, default=1)
    filled_count: int = Field(ge=0, default=0)
    application_deadline: datetime | None = None
    job_description: str = Field(max_length=12000)
    qualifications: str = Field(max_length=4000, default="")
    selection_criteria: str = Field(max_length=4000, default="")
    interview_stages: list[str] = Field(default_factory=list)
    status: HrJobOpeningStatus = HrJobOpeningStatus.DRAFT
    published_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_job_openings"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("opening_code", ASCENDING)],
                unique=True,
                name="unique_hr_opening_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("requisition_id", ASCENDING)], name="hr_openings_by_requisition"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="hr_openings_by_status"),
        ]


class HrCandidate(Document):
    tenant_id: PydanticObjectId
    full_name: str = Field(max_length=200)
    email: str = Field(max_length=254)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = Field(default=None, max_length=1000)
    qualifications: list[dict[str, Any]] = Field(default_factory=list)
    work_experience: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    previous_employment: list[dict[str, Any]] = Field(default_factory=list)
    resume_file_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    converted_employee_user_id: PydanticObjectId | None = None
    email_normalized: str = Field(max_length=254)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_candidates"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("email_normalized", ASCENDING)],
                unique=True,
                name="unique_hr_candidate_email",
            ),
        ]


class HrJobApplication(Document):
    tenant_id: PydanticObjectId
    application_code: str = Field(max_length=64)
    job_opening_id: PydanticObjectId
    candidate_id: PydanticObjectId
    requisition_id: PydanticObjectId
    department_id: PydanticObjectId
    campus_id: PydanticObjectId | None = None
    application_source: str = Field(max_length=64, default="portal")
    stage: HrApplicationPipelineStage = HrApplicationPipelineStage.APPLICATION_SUBMITTED
    assigned_recruiter_id: PydanticObjectId | None = None
    document_refs: list[str] = Field(default_factory=list)
    applied_at: datetime = Field(default_factory=utcnow)
    actor_id: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_job_applications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("application_code", ASCENDING)],
                unique=True,
                name="unique_hr_application_code",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("job_opening_id", ASCENDING), ("candidate_id", ASCENDING)],
                unique=True,
                name="unique_application_per_opening_candidate",
            ),
            IndexModel([("tenant_id", ASCENDING), ("stage", ASCENDING)], name="hr_applications_by_stage"),
        ]


class HrApplicationStageHistory(Document):
    tenant_id: PydanticObjectId
    application_id: PydanticObjectId
    from_stage: str | None = None
    to_stage: str
    reason: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_application_stage_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("application_id", ASCENDING), ("created_at", DESCENDING)],
                name="hr_app_stage_history",
            ),
        ]


class HrApplicationReviewNote(Document):
    tenant_id: PydanticObjectId
    application_id: PydanticObjectId
    author_id: PydanticObjectId
    note: str = Field(max_length=4000)
    visible_to_candidate: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_application_review_notes"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("application_id", ASCENDING)], name="hr_app_review_notes"),
        ]


class HrInterviewSession(Document):
    tenant_id: PydanticObjectId
    application_id: PydanticObjectId
    interview_code: str = Field(max_length=64)
    scheduled_at: datetime
    mode: str = Field(max_length=32)
    location_or_meeting: str = Field(max_length=1000)
    panel_member_ids: list[PydanticObjectId] = Field(default_factory=list)
    interviewer_ids: list[PydanticObjectId] = Field(default_factory=list)
    status: HrInterviewStatus = HrInterviewStatus.SCHEDULED
    reschedule_reason: str | None = Field(default=None, max_length=2000)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_interview_sessions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("interview_code", ASCENDING)],
                unique=True,
                name="unique_hr_interview_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("application_id", ASCENDING)], name="hr_interviews_by_app"),
        ]


class HrInterviewFeedback(Document):
    tenant_id: PydanticObjectId
    interview_id: PydanticObjectId
    application_id: PydanticObjectId
    interviewer_id: PydanticObjectId
    criteria_scores: dict[str, float] = Field(default_factory=dict)
    comments: str = Field(max_length=4000, default="")
    recommendation: str = Field(max_length=64, default="neutral")
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_interview_feedback"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("interview_id", ASCENDING), ("interviewer_id", ASCENDING)],
                unique=True,
                name="unique_interviewer_feedback",
            ),
        ]


class HrRecruiterAssignmentHistory(Document):
    tenant_id: PydanticObjectId
    application_id: PydanticObjectId
    recruiter_user_id: PydanticObjectId
    assigned_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_recruiter_assignment_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("application_id", ASCENDING), ("created_at", DESCENDING)],
                name="hr_recruiter_assignments",
            ),
        ]


class HrEmploymentOffer(Document):
    tenant_id: PydanticObjectId
    offer_code: str = Field(max_length=64)
    application_id: PydanticObjectId
    candidate_id: PydanticObjectId
    job_opening_id: PydanticObjectId
    designation: str = Field(max_length=200)
    department_id: PydanticObjectId
    employment_type: str = Field(max_length=64)
    salary_details: dict[str, Any] = Field(default_factory=dict)
    expected_joining_date: date | None = None
    offer_valid_until: date | None = None
    status: HrEmploymentOfferStatus = HrEmploymentOfferStatus.DRAFT
    approval_note: str | None = Field(default=None, max_length=2000)
    approved_by: PydanticObjectId | None = None
    approved_at: datetime | None = None
    issued_at: datetime | None = None
    decided_at: datetime | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hr_employment_offers"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("offer_code", ASCENDING)],
                unique=True,
                name="unique_hr_offer_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("application_id", ASCENDING)], name="hr_offers_by_app"),
        ]