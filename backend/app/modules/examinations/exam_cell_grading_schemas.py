"""Grading policy and result calculation schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.examinations.exam_cell_assessment_enums import ExamMarkRoundingMode
from app.modules.examinations.exam_cell_grading_enums import (
    ExamGradeSystem,
    ExamGradingPolicyStatus,
    ExamSubjectResultOutcome,
    ExamSubjectResultStatus,
)
from app.modules.examinations.exam_cell_grading_models import (
    ExamCgpaCalculation,
    ExamGpaCalculation,
    ExamGradeBoundary,
    ExamGradingPolicy,
    ExamGradingPolicyVersion,
    ExamSemesterResult,
    ExamStudentSubjectResult,
)


class ExamGradeBoundaryInput(BaseModel):
    min_percent: float = Field(ge=0, le=100)
    max_percent: float = Field(ge=0, le=100)
    grade_letter: str = Field(min_length=1, max_length=8)
    grade_point: float = Field(ge=0)
    is_passing: bool = True
    component_scope: str = "overall"
    sort_order: int = Field(default=1, ge=1)


class ExamGradingPolicyCreate(BaseModel):
    policy_code: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=1, max_length=160)
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
    arrear_rules: dict = Field(default_factory=dict)
    supplementary_rules: dict = Field(default_factory=dict)
    effective_from: date | None = None
    boundaries: list[ExamGradeBoundaryInput] = Field(min_length=1)

    @field_validator("policy_code", "programme_code")
    @classmethod
    def upper_trim(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class ExamGradingPolicyRead(BaseModel):
    id: str
    policy_id: str
    policy_code: str
    title: str
    programme_code: str | None
    status: ExamGradingPolicyStatus
    version: int
    passing_min_percent: float
    min_grade_point_to_pass: float
    mark_rounding: ExamMarkRoundingMode
    decimal_precision: int

    @classmethod
    def from_doc(cls, doc: ExamGradingPolicy) -> "ExamGradingPolicyRead":
        return cls(
            id=str(doc.id),
            policy_id=doc.policy_id,
            policy_code=doc.policy_code,
            title=doc.title,
            programme_code=doc.programme_code,
            status=doc.status,
            version=doc.version,
            passing_min_percent=doc.passing_min_percent,
            min_grade_point_to_pass=doc.min_grade_point_to_pass,
            mark_rounding=doc.mark_rounding,
            decimal_precision=doc.decimal_precision,
        )


class ExamGradeBoundaryRead(BaseModel):
    boundary_id: str
    policy_id: str
    min_percent: float
    max_percent: float
    grade_letter: str
    grade_point: float
    is_passing: bool

    @classmethod
    def from_doc(cls, doc: ExamGradeBoundary) -> "ExamGradeBoundaryRead":
        return cls(
            boundary_id=doc.boundary_id,
            policy_id=doc.policy_id,
            min_percent=doc.min_percent,
            max_percent=doc.max_percent,
            grade_letter=doc.grade_letter,
            grade_point=doc.grade_point,
            is_passing=doc.is_passing,
        )


class ExamGradingPolicyActivate(BaseModel):
    change_summary: str | None = Field(default=None, max_length=500)
    effective_from: date | None = None


class ExamProvisionalCalculateRequest(BaseModel):
    exam_session_id: str
    policy_id: str | None = None
    programme_code: str | None = None
    recalculate: bool = False

    @field_validator("programme_code")
    @classmethod
    def normalize(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class ExamStudentSubjectResultRead(BaseModel):
    result_id: str
    exam_session_id: str
    student_user_id: str
    course_code: str
    policy_id: str
    policy_version: int
    percentage: float | None
    grade_letter: str | None
    grade_point: float | None
    credit_units: float
    credits_earned: float
    outcome: ExamSubjectResultOutcome
    status: ExamSubjectResultStatus
    calculated_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamStudentSubjectResult) -> "ExamStudentSubjectResultRead":
        return cls(
            result_id=doc.result_id,
            exam_session_id=str(doc.exam_session_id),
            student_user_id=str(doc.student_user_id),
            course_code=doc.course_code,
            policy_id=doc.policy_id,
            policy_version=doc.policy_version,
            percentage=doc.percentage,
            grade_letter=doc.grade_letter,
            grade_point=doc.grade_point,
            credit_units=doc.credit_units,
            credits_earned=doc.credits_earned,
            outcome=doc.outcome,
            status=doc.status,
            calculated_at=doc.calculated_at,
        )


class ExamSemesterResultRead(BaseModel):
    semester_result_id: str
    exam_session_id: str
    student_user_id: str
    credits_registered: float
    credits_earned: float
    gpa: float | None
    cgpa: float | None
    status: ExamSubjectResultStatus

    @classmethod
    def from_doc(cls, doc: ExamSemesterResult) -> "ExamSemesterResultRead":
        return cls(
            semester_result_id=doc.semester_result_id,
            exam_session_id=str(doc.exam_session_id),
            student_user_id=str(doc.student_user_id),
            credits_registered=doc.credits_registered,
            credits_earned=doc.credits_earned,
            gpa=doc.gpa,
            cgpa=doc.cgpa,
            status=doc.status,
        )


class ExamGpaCalculationRead(BaseModel):
    calculation_id: str
    gpa: float
    credits_attempted: float
    credits_earned: float
    policy_id: str
    policy_version: int

    @classmethod
    def from_doc(cls, doc: ExamGpaCalculation) -> "ExamGpaCalculationRead":
        return cls(
            calculation_id=doc.calculation_id,
            gpa=doc.gpa,
            credits_attempted=doc.credits_attempted,
            credits_earned=doc.credits_earned,
            policy_id=doc.policy_id,
            policy_version=doc.policy_version,
        )


class ExamCgpaCalculationRead(BaseModel):
    calculation_id: str
    cgpa: float
    credits_attempted: float
    credits_earned: float

    @classmethod
    def from_doc(cls, doc: ExamCgpaCalculation) -> "ExamCgpaCalculationRead":
        return cls(
            calculation_id=doc.calculation_id,
            cgpa=doc.cgpa,
            credits_attempted=doc.credits_attempted,
            credits_earned=doc.credits_earned,
        )


class ExamProvisionalCalculateSummary(BaseModel):
    subjects_computed: int
    students_computed: int
    missing_marks: int
    invalid_records: int
    policy_id: str
    policy_version: int


class ExamGradingPolicyVersionRead(BaseModel):
    policy_id: str
    version_number: int
    effective_from: date | None
    change_summary: str | None

    @classmethod
    def from_doc(cls, doc: ExamGradingPolicyVersion) -> "ExamGradingPolicyVersionRead":
        return cls(
            policy_id=doc.policy_id,
            version_number=doc.version_number,
            effective_from=doc.effective_from,
            change_summary=doc.change_summary,
        )