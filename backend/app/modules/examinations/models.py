"""Central examination and assessment records."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.enums import (
    AssessmentComponentType,
    MarksBatchStatus,
    MarksCorrectionStatus,
    StudentMarkStatus,
)


class GradingPolicy(Document):
    tenant_id: PydanticObjectId
    low_performance_threshold: float = Field(default=40.0, ge=0, le=100)
    pass_percentage: float = Field(default=40.0, ge=0, le=100)
    grade_bands: list[dict[str, Any]] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "grading_policies"
        indexes = [IndexModel([("tenant_id", ASCENDING)], unique=True, name="unique_grading_policy")]


class Assessment(Document):
    tenant_id: PydanticObjectId
    assessment_id: str
    course_id: str
    course_code: str
    title: str
    academic_year_label: str
    semester_label: str
    final_results_published: bool = False
    locked: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "assessments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("assessment_id", ASCENDING)],
                unique=True,
                name="unique_assessment_id",
            ),
        ]


class AssessmentComponent(Document):
    tenant_id: PydanticObjectId
    assessment_id: str
    component_id: str
    code: str
    name: str
    component_type: AssessmentComponentType
    max_marks: float = Field(ge=0)
    weight_percent: float = Field(default=0, ge=0, le=100)
    faculty_may_enter: bool = True
    is_official_final: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "assessment_components"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("assessment_id", ASCENDING), ("component_id", ASCENDING)],
                unique=True,
                name="unique_component",
            ),
        ]


class FacultyAssessmentAssignment(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    assessment_id: str
    course_id: str
    course_code: str
    section: str
    subject_id: str | None = None
    academic_year_label: str
    semester_label: str

    class Settings:
        name = "faculty_assessment_assignments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("assessment_id", ASCENDING)],
                name="faculty_assessment_assignments_lookup",
            ),
        ]


class MarksSubmissionBatch(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    assessment_id: str
    component_id: str
    course_code: str
    section: str
    status: MarksBatchStatus = MarksBatchStatus.DRAFT
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "marks_submission_batches"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("faculty_user_id", ASCENDING),
                    ("component_id", ASCENDING),
                    ("section", ASCENDING),
                ],
                name="batches_by_faculty_component",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("component_id", ASCENDING),
                    ("section", ASCENDING),
                    ("status", ASCENDING),
                ],
                name="batches_by_component_status",
            ),
        ]


class StudentAssessmentMark(Document):
    tenant_id: PydanticObjectId
    batch_id: PydanticObjectId
    assessment_id: str
    component_id: str
    student_user_id: PydanticObjectId
    marks_obtained: float = Field(ge=0)
    max_marks: float = Field(ge=0)
    status: StudentMarkStatus = StudentMarkStatus.DRAFT
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_assessment_marks"
        indexes = [
            IndexModel(
                [
                    ("batch_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                ],
                unique=True,
                name="unique_mark_per_student_batch",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("component_id", ASCENDING)],
                name="marks_by_student_component",
            ),
        ]


class MarksCorrectionRequest(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    batch_id: PydanticObjectId
    student_user_id: PydanticObjectId | None = None
    requested_marks: float | None = Field(default=None, ge=0)
    reason: str = Field(max_length=1000)
    status: MarksCorrectionStatus = MarksCorrectionStatus.PENDING
    created_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None

    class Settings:
        name = "marks_correction_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("status", ASCENDING)],
                name="marks_corrections_by_faculty",
            ),
        ]


class MarksApprovalHistory(Document):
    tenant_id: PydanticObjectId
    batch_id: PydanticObjectId
    action: str
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "marks_approval_history"
        indexes = [
            IndexModel([("batch_id", ASCENDING), ("created_at", DESCENDING)], name="approval_history_by_batch"),
        ]
