"""Central LMS collections."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.lms.enums import LmsAssignmentStatus, MaterialPublishState, SubmissionStatus


class LearningMaterial(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    course_id: str
    course_code: str
    section: str | None = None
    subject_id: str | None = None
    unit_no: int | None = Field(default=None, ge=1)
    material_type: str = Field(default="document", max_length=32)
    title: str = Field(max_length=200)
    file_id: str
    storage_key: str
    file_name: str
    mime_type: str
    size_bytes: int = Field(ge=1)
    publish_state: MaterialPublishState = MaterialPublishState.DRAFT
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "learning_materials"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("course_code", ASCENDING), ("publish_state", ASCENDING)],
                name="materials_by_course",
            ),
            IndexModel([("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING)], name="materials_by_faculty"),
        ]


class AssignmentRule(Document):
    tenant_id: PydanticObjectId
    allowed_extensions: list[str] = Field(default_factory=lambda: [".pdf", ".docx"])
    max_file_size_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    late_submission_allowed: bool = True
    late_penalty_percent: float = Field(default=0, ge=0, le=100)
    resubmission_allowed: bool = False
    max_resubmissions: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "assignment_rules"
        indexes = [IndexModel([("tenant_id", ASCENDING)], name="rules_by_tenant")]


class CourseAssignment(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    course_id: str
    course_code: str
    section: str
    subject_id: str | None = None
    title: str = Field(max_length=200)
    instructions: str = Field(max_length=8000)
    max_marks: float = Field(ge=0)
    deadline_at: datetime
    rule_id: PydanticObjectId
    status: LmsAssignmentStatus = LmsAssignmentStatus.DRAFT
    academic_year_label: str
    semester_label: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "course_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("course_code", ASCENDING), ("section", ASCENDING), ("status", ASCENDING)],
                name="lms_assignments_by_section",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("deadline_at", ASCENDING)],
                name="lms_assignments_by_faculty",
            ),
        ]


class AssignmentSubmission(Document):
    tenant_id: PydanticObjectId
    assignment_id: PydanticObjectId
    student_user_id: PydanticObjectId
    status: SubmissionStatus = SubmissionStatus.SUBMITTED
    submitted_at: datetime | None = None
    storage_key: str | None = None
    file_name: str | None = None
    attempt_no: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "assignment_submissions"
        indexes = [
            IndexModel(
                [("assignment_id", ASCENDING), ("student_user_id", ASCENDING), ("attempt_no", ASCENDING)],
                unique=True,
                name="unique_submission_attempt",
            ),
        ]


class AssignmentEvaluation(Document):
    tenant_id: PydanticObjectId
    submission_id: PydanticObjectId
    evaluator_id: PydanticObjectId
    marks_awarded: float = Field(ge=0)
    evaluated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "assignment_evaluations"
        indexes = [
            IndexModel([("submission_id", ASCENDING)], unique=True, name="unique_evaluation_per_submission"),
        ]


class AssignmentFeedback(Document):
    tenant_id: PydanticObjectId
    submission_id: PydanticObjectId
    feedback: str = Field(max_length=4000)
    author_id: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "assignment_feedback"
        indexes = [
            IndexModel([("submission_id", ASCENDING)], unique=True, name="unique_feedback_per_submission"),
        ]


class AssignmentResubmissionHistory(Document):
    tenant_id: PydanticObjectId
    assignment_id: PydanticObjectId
    student_user_id: PydanticObjectId
    from_attempt: int
    to_attempt: int
    reason: str | None = None
    authorized_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "assignment_resubmission_history"
        indexes = [
            IndexModel(
                [("assignment_id", ASCENDING), ("student_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="resubmission_history",
            ),
        ]
