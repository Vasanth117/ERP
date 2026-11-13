"""Examination registration and hall ticket API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.students.examination_registration_enums import (
    ExamRegistrationSubjectType,
    StudentExamRegistrationStatus,
)


class EligibleExaminationRead(BaseModel):
    season_id: str
    title: str
    academic_year_label: str
    semester_label: str
    registration_open_at: datetime | None = None
    registration_close_at: datetime | None = None
    registration_open: bool = False
    eligible: bool = False


class ExaminationRegistrationScheduleRead(BaseModel):
    season_id: str
    registration_open_at: datetime
    registration_close_at: datetime
    cancellation_deadline: datetime | None = None
    fee_required: bool
    fee_amount: float
    fee_code: str
    allow_arrear_registration: bool


class ExaminationRegistrationEligibilityRead(BaseModel):
    season_id: str
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    fee_payment_status: str | None = None
    fee_verified: bool = False
    registration_window_open: bool = False


class EligibleExamSubjectRead(BaseModel):
    course_code: str
    course_name: str | None = None
    subject_type: ExamRegistrationSubjectType
    paper_code: str | None = None
    already_registered: bool = False


class ExamRegistrationSubjectInput(BaseModel):
    course_code: str
    subject_type: ExamRegistrationSubjectType = ExamRegistrationSubjectType.SEMESTER
    paper_code: str | None = None

    model_config = {"extra": "forbid"}


class ExamRegistrationSubmitInput(BaseModel):
    season_id: str
    subjects: list[ExamRegistrationSubjectInput] = Field(min_length=1)

    model_config = {"extra": "forbid"}


class ExamRegistrationRead(BaseModel):
    registration_id: str
    season_id: str
    status: StudentExamRegistrationStatus
    fee_verified: bool
    subjects: list[EligibleExamSubjectRead] = Field(default_factory=list)
    submitted_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime


class ExamRegistrationHistoryRead(BaseModel):
    registration_id: str
    season_id: str
    action: str
    note: str | None = None
    created_at: datetime


class HallTicketAvailabilityRead(BaseModel):
    season_id: str
    available: bool
    ticket_number: str | None = None
    status: str | None = None
    published_at: datetime | None = None


class HallTicketDetailsRead(BaseModel):
    season_id: str
    ticket_number: str
    roll_number: str | None = None
    student_name: str | None = None
    centre_code: str | None = None
    centre_name: str | None = None
    examination_sessions: list[dict] = Field(default_factory=list)
    instructions: str | None = None
    published_at: datetime | None = None


class HallTicketDownloadRead(BaseModel):
    season_id: str
    ticket_number: str
    content_type: str = "application/pdf"
    download_token: str
    expires_at: datetime
