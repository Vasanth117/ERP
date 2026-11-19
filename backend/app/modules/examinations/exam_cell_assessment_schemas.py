"""Examination cell — assessment configuration schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.examinations.exam_cell_assessment_enums import (
    ExamAssessmentComponentKind,
    ExamAssessmentConfigStatus,
    ExamMarkRoundingMode,
)
from app.modules.examinations.exam_cell_assessment_models import ExamAssessmentComponent, ExamAssessmentConfig


class ExamAssessmentComponentInput(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=120)
    assessment_type: ExamAssessmentComponentKind
    max_marks: float = Field(gt=0)
    weight_percent: float = Field(default=0, ge=0, le=100)
    passing_marks: float | None = Field(default=None, ge=0)
    contributes_to_final: bool = True
    sort_order: int = Field(default=1, ge=1)
    metadata: dict = Field(default_factory=dict)

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class ExamAssessmentConfigCreate(BaseModel):
    config_code: str = Field(min_length=2, max_length=32)
    title: str = Field(min_length=2, max_length=200)
    programme_code: str | None = Field(default=None, max_length=32)
    semester_label: str = Field(min_length=1, max_length=32)
    academic_year_label: str = Field(min_length=2, max_length=32)
    course_code: str | None = Field(default=None, max_length=32)
    subject_code: str | None = Field(default=None, max_length=32)
    effective_from: date | None = None
    effective_to: date | None = None
    passing_marks_percent: float = Field(default=40.0, ge=0, le=100)
    minimum_eligibility_percent: float = Field(default=40.0, ge=0, le=100)
    attendance_eligibility_percent: float | None = Field(default=None, ge=0, le=100)
    mark_rounding: ExamMarkRoundingMode = ExamMarkRoundingMode.NEAREST
    decimal_precision: int = Field(default=0, ge=0, le=2)
    theory_rules: dict = Field(default_factory=dict)
    practical_rules: dict = Field(default_factory=dict)
    internal_calculation_rules: dict = Field(default_factory=dict)
    components: list[ExamAssessmentComponentInput] = Field(min_length=1)

    @field_validator("config_code", "course_code", "subject_code", "programme_code")
    @classmethod
    def normalize_optional_codes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped.upper() if stripped else None


class ExamAssessmentConfigUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    effective_from: date | None = None
    effective_to: date | None = None
    passing_marks_percent: float | None = Field(default=None, ge=0, le=100)
    minimum_eligibility_percent: float | None = Field(default=None, ge=0, le=100)
    attendance_eligibility_percent: float | None = Field(default=None, ge=0, le=100)
    mark_rounding: ExamMarkRoundingMode | None = None
    decimal_precision: int | None = Field(default=None, ge=0, le=2)
    theory_rules: dict | None = None
    practical_rules: dict | None = None
    internal_calculation_rules: dict | None = None
    components: list[ExamAssessmentComponentInput] | None = None


class ExamAssessmentComponentRead(BaseModel):
    component_id: str
    code: str
    name: str
    assessment_type: ExamAssessmentComponentKind
    max_marks: float
    weight_percent: float
    passing_marks: float | None
    contributes_to_final: bool
    sort_order: int


class ExamAssessmentConfigRead(BaseModel):
    id: str
    config_id: str
    config_code: str
    title: str
    programme_code: str | None
    semester_label: str
    academic_year_label: str
    course_code: str | None
    subject_code: str | None
    effective_from: date | None
    effective_to: date | None
    version: int
    status: ExamAssessmentConfigStatus
    passing_marks_percent: float
    minimum_eligibility_percent: float
    attendance_eligibility_percent: float | None
    mark_rounding: ExamMarkRoundingMode
    decimal_precision: int
    theory_rules: dict
    practical_rules: dict
    internal_calculation_rules: dict
    components: list[ExamAssessmentComponentRead]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_documents(
        cls,
        config: ExamAssessmentConfig,
        components: list[ExamAssessmentComponent],
    ) -> "ExamAssessmentConfigRead":
        return cls(
            id=str(config.id),
            config_id=config.config_id,
            config_code=config.config_code,
            title=config.title,
            programme_code=config.programme_code,
            semester_label=config.semester_label,
            academic_year_label=config.academic_year_label,
            course_code=config.course_code,
            subject_code=config.subject_code,
            effective_from=config.effective_from,
            effective_to=config.effective_to,
            version=config.version,
            status=config.status,
            passing_marks_percent=config.passing_marks_percent,
            minimum_eligibility_percent=config.minimum_eligibility_percent,
            attendance_eligibility_percent=config.attendance_eligibility_percent,
            mark_rounding=config.mark_rounding,
            decimal_precision=config.decimal_precision,
            theory_rules=dict(config.theory_rules),
            practical_rules=dict(config.practical_rules),
            internal_calculation_rules=dict(config.internal_calculation_rules),
            components=[
                ExamAssessmentComponentRead(
                    component_id=c.component_id,
                    code=c.code,
                    name=c.name,
                    assessment_type=c.assessment_type,
                    max_marks=c.max_marks,
                    weight_percent=c.weight_percent,
                    passing_marks=c.passing_marks,
                    contributes_to_final=c.contributes_to_final,
                    sort_order=c.sort_order,
                )
                for c in sorted(components, key=lambda row: row.sort_order)
            ],
            created_at=config.created_at,
            updated_at=config.updated_at,
        )


class ExamAssessmentPolicyVersionRead(BaseModel):
    config_id: str
    version_number: int
    change_summary: str | None
    created_at: datetime