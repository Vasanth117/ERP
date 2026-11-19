"""Examination cell — grading policies and calculated results."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_assessment_enums import ExamMarkRoundingMode
from app.modules.examinations.exam_cell_grading_enums import (
    ExamGradeSystem,
    ExamGradingPolicyStatus,
    ExamSubjectResultOutcome,
    ExamSubjectResultStatus,
)


class ExamGradingPolicy(Document):
    tenant_id: PydanticObjectId
    policy_id: str
    policy_code: str
    title: str
    programme_code: str | None = None
    batch_label: str | None = None
    academic_year_label: str | None = None
    grade_system: ExamGradeSystem = ExamGradeSystem.LETTER
    passing_min_percent: float = Field(default=40.0, ge=0, le=100)
    min_grade_point_to_pass: float = Field(default=4.0, ge=0)
    theory_min_percent: float | None = Field(default=None, ge=0, le=100)
    practical_min_percent: float | None = Field(default=None, ge=0, le=100)
    mark_rounding: ExamMarkRoundingMode = ExamMarkRoundingMode.NEAREST
    decimal_precision: int = Field(default=2, ge=0, le=2)
    arrear_rules: dict[str, Any] = Field(default_factory=dict)
    supplementary_rules: dict[str, Any] = Field(default_factory=dict)
    version: int = Field(default=1, ge=1)
    status: ExamGradingPolicyStatus = ExamGradingPolicyStatus.DRAFT
    effective_from: date | None = None
    effective_to: date | None = None
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_grading_policies"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_id", ASCENDING)],
                unique=True,
                name="unique_exam_grading_policy_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_code", ASCENDING)],
                unique=True,
                name="unique_exam_grading_policy_code",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("programme_code", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("status", ASCENDING),
                ],
                name="exam_grading_policy_scope",
            ),
        ]


class ExamGradeBoundary(Document):
    tenant_id: PydanticObjectId
    boundary_id: str
    policy_id: str
    min_percent: float = Field(ge=0, le=100)
    max_percent: float = Field(ge=0, le=100)
    grade_letter: str
    grade_point: float = Field(ge=0)
    is_passing: bool = True
    component_scope: str = "overall"
    sort_order: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_grade_boundaries"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("boundary_id", ASCENDING)],
                unique=True,
                name="unique_exam_grade_boundary_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_id", ASCENDING), ("sort_order", ASCENDING)],
                name="exam_grade_boundaries_by_policy",
            ),
        ]


class ExamGradingPolicyVersion(Document):
    tenant_id: PydanticObjectId
    policy_id: str
    version_number: int = Field(ge=1)
    snapshot: dict[str, Any] = Field(default_factory=dict)
    boundaries_snapshot: list[dict[str, Any]] = Field(default_factory=list)
    effective_from: date | None = None
    change_summary: str | None = Field(default=None, max_length=500)
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_grading_policy_versions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_id", ASCENDING), ("version_number", DESCENDING)],
                unique=True,
                name="unique_exam_grading_policy_version",
            ),
        ]


class ExamStudentSubjectResult(Document):
    tenant_id: PydanticObjectId
    result_id: str
    exam_session_id: PydanticObjectId
    student_user_id: PydanticObjectId
    course_code: str
    policy_id: str
    policy_version: int
    marks_obtained: float | None = None
    max_marks: float | None = None
    percentage: float | None = None
    grade_letter: str | None = None
    grade_point: float | None = None
    credit_units: float = Field(default=0, ge=0)
    credits_earned: float = Field(default=0, ge=0)
    outcome: ExamSubjectResultOutcome = ExamSubjectResultOutcome.INCOMPLETE
    status: ExamSubjectResultStatus = ExamSubjectResultStatus.PROVISIONAL
    calculation_inputs: dict[str, Any] = Field(default_factory=dict)
    calculated_at: datetime = Field(default_factory=utcnow)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_student_subject_results"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("result_id", ASCENDING)],
                unique=True,
                name="unique_exam_student_subject_result",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("exam_session_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("course_code", ASCENDING),
                ],
                unique=True,
                name="unique_subject_result_per_student",
            ),
        ]


class ExamSemesterResult(Document):
    tenant_id: PydanticObjectId
    semester_result_id: str
    exam_session_id: PydanticObjectId
    student_user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    programme_code: str | None = None
    credits_registered: float = Field(default=0, ge=0)
    credits_earned: float = Field(default=0, ge=0)
    gpa: float | None = None
    gpa_calculation_id: str | None = None
    cgpa: float | None = None
    cgpa_calculation_id: str | None = None
    overall_outcome: ExamSubjectResultOutcome | None = None
    status: ExamSubjectResultStatus = ExamSubjectResultStatus.PROVISIONAL
    calculated_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_semester_results"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("semester_result_id", ASCENDING)],
                unique=True,
                name="unique_exam_semester_result",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_semester_result_per_student",
            ),
        ]


class ExamGpaCalculation(Document):
    tenant_id: PydanticObjectId
    calculation_id: str
    exam_session_id: PydanticObjectId
    student_user_id: PydanticObjectId
    policy_id: str
    policy_version: int
    credits_attempted: float = Field(default=0, ge=0)
    credits_earned: float = Field(default=0, ge=0)
    quality_points: float = Field(default=0, ge=0)
    gpa: float = Field(default=0, ge=0)
    calculation_inputs: dict[str, Any] = Field(default_factory=dict)
    calculated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_gpa_calculations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("calculation_id", ASCENDING)],
                unique=True,
                name="unique_exam_gpa_calculation",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("student_user_id", ASCENDING)],
                name="exam_gpa_by_student_session",
            ),
        ]


class ExamCgpaCalculation(Document):
    tenant_id: PydanticObjectId
    calculation_id: str
    student_user_id: PydanticObjectId
    policy_id: str
    policy_version: int
    credits_attempted: float = Field(default=0, ge=0)
    credits_earned: float = Field(default=0, ge=0)
    quality_points: float = Field(default=0, ge=0)
    cgpa: float = Field(default=0, ge=0)
    calculation_inputs: dict[str, Any] = Field(default_factory=dict)
    calculated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_cgpa_calculations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("calculation_id", ASCENDING)],
                unique=True,
                name="unique_exam_cgpa_calculation",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("calculated_at", DESCENDING)],
                name="exam_cgpa_timeline",
            ),
        ]