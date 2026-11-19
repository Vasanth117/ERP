"""Examination cell — eligibility and registration schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.examinations.exam_cell_registration_enums import (
    ExamRegistrationStatus,
    ExamRegistrationSubjectType,
)


class ExamEligibilitySubjectRead(BaseModel):
    course_code: str
    subject_type: ExamRegistrationSubjectType
    eligible: bool
    reasons: list[str] = Field(default_factory=list)


class ExamEligibilityRead(BaseModel):
    eligibility_id: str
    exam_session_id: str
    season_id: str | None
    student_user_id: str
    overall_eligible: bool
    summary_reasons: list[str]
    subjects: list[ExamEligibilitySubjectRead]
    evaluated_at: datetime
    published: bool


class ExamEligibilityEvaluateRequest(BaseModel):
    student_user_id: str
    exam_session_id: str
    publish: bool = False


class ExamRegistrationSubjectInput(BaseModel):
    course_code: str = Field(min_length=2, max_length=32)
    subject_code: str | None = Field(default=None, max_length=32)
    paper_code: str | None = Field(default=None, max_length=32)
    subject_type: ExamRegistrationSubjectType = ExamRegistrationSubjectType.SEMESTER

    @field_validator("course_code")
    @classmethod
    def normalize(cls, value: str) -> str:
        return value.strip().upper()


class ExamRegistrationCreate(BaseModel):
    exam_session_id: str
    student_user_id: str | None = None
    subjects: list[ExamRegistrationSubjectInput] = Field(min_length=1)
    confirm: bool = False


class ExamBulkRegistrationCreate(BaseModel):
    exam_session_id: str
    student_user_ids: list[str] = Field(min_length=1, max_length=200)
    subjects: list[ExamRegistrationSubjectInput] = Field(min_length=1)
    confirm: bool = True


class ExamRegistrationSubjectRead(BaseModel):
    course_code: str
    subject_code: str | None
    paper_code: str | None
    subject_type: ExamRegistrationSubjectType


class ExamRegistrationRead(BaseModel):
    registration_id: str
    exam_session_id: str
    season_id: str | None
    student_user_id: str
    status: ExamRegistrationStatus
    fee_verified: bool
    subjects: list[ExamRegistrationSubjectRead]
    submitted_at: datetime | None
    confirmed_at: datetime | None
    cancelled_at: datetime | None
    created_at: datetime


class ExamRegistrationCorrection(BaseModel):
    subjects: list[ExamRegistrationSubjectInput] | None = None
    note: str | None = Field(default=None, max_length=500)


class ExamRegistrationSummaryRead(BaseModel):
    exam_session_id: str
    total_registrations: int
    confirmed: int
    submitted: int
    cancelled: int
    pending_fee: int


class ExamRegistrationHistoryRead(BaseModel):
    registration_id: str
    action: str
    actor_id: str | None
    note: str | None
    created_at: datetime