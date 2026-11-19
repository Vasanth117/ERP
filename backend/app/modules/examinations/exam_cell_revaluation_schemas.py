"""Revaluation and supplementary schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.examinations.exam_cell_revaluation_enums import (
    ExamRevaluationApplicationStatus,
    ExamRevaluationApplicationType,
    ExamSupplementaryRegistrationStatus,
)
from app.modules.examinations.exam_cell_revaluation_models import ExamRevaluationApplication, ExamSupplementaryRegistration


class ExamRevaluationApply(BaseModel):
    application_type: ExamRevaluationApplicationType
    student_user_id: str
    exam_session_id: str
    course_code: str
    season_id: str | None = None
    payment_request_id: str | None = None

    @field_validator("course_code")
    @classmethod
    def upper(cls, v: str) -> str:
        return v.strip().upper()


class ExamRevaluationAssignEvaluator(BaseModel):
    evaluator_user_id: str


class ExamRevaluationRecordEvaluation(BaseModel):
    revised_marks: float = Field(ge=0)
    revised_max_marks: float = Field(gt=0)
    findings: str | None = Field(default=None, max_length=4000)


class ExamRevaluationApprovalDecision(BaseModel):
    approved: bool
    comment: str | None = Field(default=None, max_length=2000)


class ExamRevaluationApplicationRead(BaseModel):
    application_id: str
    application_type: ExamRevaluationApplicationType
    student_user_id: str
    exam_session_id: str
    course_code: str
    status: ExamRevaluationApplicationStatus
    fee_verified: bool
    original_marks: float | None
    original_grade: str | None

    @classmethod
    def from_doc(cls, doc: ExamRevaluationApplication) -> "ExamRevaluationApplicationRead":
        return cls(
            application_id=doc.application_id,
            application_type=doc.application_type,
            student_user_id=str(doc.student_user_id),
            exam_session_id=str(doc.exam_session_id),
            course_code=doc.course_code,
            status=doc.status,
            fee_verified=doc.fee_verified,
            original_marks=doc.original_marks,
            original_grade=doc.original_grade,
        )


class ExamSupplementaryRegister(BaseModel):
    student_user_id: str
    exam_session_id: str | None = None
    supplementary_season_id: str | None = None
    course_codes: list[str] = Field(min_length=1)
    payment_request_id: str | None = None

    @field_validator("course_codes")
    @classmethod
    def upper_codes(cls, values: list[str]) -> list[str]:
        return [v.strip().upper() for v in values]


class ExamSupplementaryEligibilityRead(BaseModel):
    student_user_id: str
    eligible_courses: list[str]
    restrictions: list[str]


class ExamSupplementaryRegistrationRead(BaseModel):
    registration_id: str
    student_user_id: str
    course_codes: list[str]
    status: ExamSupplementaryRegistrationStatus
    fee_verified: bool

    @classmethod
    def from_doc(cls, doc: ExamSupplementaryRegistration) -> "ExamSupplementaryRegistrationRead":
        return cls(
            registration_id=doc.registration_id,
            student_user_id=str(doc.student_user_id),
            course_codes=list(doc.course_codes),
            status=doc.status,
            fee_verified=doc.fee_verified,
        )