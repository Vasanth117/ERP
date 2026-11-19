"""Examination cell — assessment configuration collections."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_assessment_enums import (
    ExamAssessmentConfigStatus,
    ExamAssessmentComponentKind,
    ExamMarkRoundingMode,
)


class ExamAssessmentConfig(Document):
    tenant_id: PydanticObjectId
    config_id: str
    config_code: str
    title: str
    programme_code: str | None = None
    semester_label: str
    academic_year_label: str
    course_code: str | None = None
    subject_code: str | None = None
    effective_from: date | None = None
    effective_to: date | None = None
    version: int = 1
    status: ExamAssessmentConfigStatus = ExamAssessmentConfigStatus.DRAFT
    passing_marks_percent: float = Field(default=40.0, ge=0, le=100)
    minimum_eligibility_percent: float = Field(default=40.0, ge=0, le=100)
    attendance_eligibility_percent: float | None = Field(default=None, ge=0, le=100)
    mark_rounding: ExamMarkRoundingMode = ExamMarkRoundingMode.NEAREST
    decimal_precision: int = Field(default=0, ge=0, le=2)
    theory_rules: dict[str, Any] = Field(default_factory=dict)
    practical_rules: dict[str, Any] = Field(default_factory=dict)
    internal_calculation_rules: dict[str, Any] = Field(default_factory=dict)
    created_by: PydanticObjectId | None = None
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_assessment_configs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("config_code", ASCENDING)],
                unique=True,
                name="unique_exam_assessment_config_code",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("config_id", ASCENDING)],
                unique=True,
                name="unique_exam_assessment_config_id",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("programme_code", ASCENDING),
                    ("semester_label", ASCENDING),
                    ("course_code", ASCENDING),
                ],
                name="exam_assessment_config_scope",
            ),
        ]


class ExamAssessmentComponent(Document):
    tenant_id: PydanticObjectId
    config_id: str
    component_id: str
    code: str
    name: str
    assessment_type: ExamAssessmentComponentKind
    max_marks: float = Field(ge=0)
    weight_percent: float = Field(default=0, ge=0, le=100)
    passing_marks: float | None = Field(default=None, ge=0)
    contributes_to_final: bool = True
    sort_order: int = Field(default=1, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_assessment_components"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("config_id", ASCENDING), ("component_id", ASCENDING)],
                unique=True,
                name="unique_exam_assessment_component",
            ),
        ]


class ExamAssessmentPolicyVersion(Document):
    tenant_id: PydanticObjectId
    config_id: str
    version_number: int = Field(ge=1)
    snapshot: dict[str, Any] = Field(default_factory=dict)
    change_summary: str | None = Field(default=None, max_length=500)
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_assessment_policy_versions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("config_id", ASCENDING), ("version_number", DESCENDING)],
                name="exam_assessment_policy_versions",
            ),
        ]