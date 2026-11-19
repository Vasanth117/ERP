"""Examination cell — hall ticket schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.examinations.exam_cell_registration_enums import ExamHallTicketStatus


class ExamHallTicketGenerateRequest(BaseModel):
    exam_session_id: str
    student_user_id: str
    publish: bool = False


class ExamHallTicketBulkGenerateRequest(BaseModel):
    exam_session_id: str
    student_user_ids: list[str] = Field(min_length=1, max_length=200)
    publish: bool = False


class ExamHallTicketSubjectRead(BaseModel):
    course_code: str
    subject_code: str | None
    paper_code: str | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    centre_code: str | None
    room_label: str | None
    facility_id: str | None


class ExamHallTicketRead(BaseModel):
    hall_ticket_id: str
    ticket_number: str
    verification_code: str
    exam_session_id: str
    season_id: str | None
    registration_id: str
    student_user_id: str
    institution_name: str | None
    roll_number: str | None
    student_name: str | None
    status: ExamHallTicketStatus
    subjects: list[ExamHallTicketSubjectRead]
    published_at: datetime | None
    has_pdf: bool


class ExamHallTicketVerifyRequest(BaseModel):
    ticket_number: str
    verification_code: str


class ExamHallTicketVerifyResponse(BaseModel):
    valid: bool
    status: ExamHallTicketStatus | None = None
    student_name: str | None = None
    exam_session_id: str | None = None
    message: str | None = None


class ExamHallTicketReissueRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class ExamHallTicketHistoryRead(BaseModel):
    action: str
    actor_id: str | None
    note: str | None
    created_at: datetime