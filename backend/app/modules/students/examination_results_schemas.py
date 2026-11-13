"""Examination results API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class SemesterResultSummaryRead(BaseModel):
    season_id: str
    academic_year_label: str
    semester_label: str
    overall_pass: bool | None = None
    gpa: float | None = None
    published_at: datetime | None = None
    status: str


class SubjectWiseMarksRead(BaseModel):
    season_id: str
    course_code: str
    course_name: str | None = None
    attempt_number: int
    is_arrear: bool
    theory_obtained: float | None = None
    theory_max: float | None = None
    practical_obtained: float | None = None
    practical_max: float | None = None
    internal_obtained: float | None = None
    internal_max: float | None = None
    external_obtained: float | None = None
    external_max: float | None = None
    total_obtained: float | None = None
    total_max: float | None = None
    pass_fail: str | None = None
    grade_letter: str | None = None
    published_at: datetime | None = None


class ResultAttemptHistoryRead(BaseModel):
    season_id: str
    course_code: str
    attempt_number: int
    pass_fail: str | None = None
    total_obtained: float | None = None
    total_max: float | None = None
    published_at: datetime | None = None


class ArrearResultRead(BaseModel):
    season_id: str
    course_code: str
    course_name: str | None = None
    attempt_number: int
    pass_fail: str | None = None
    total_obtained: float | None = None
    total_max: float | None = None
    published_at: datetime | None = None


class ResultPublicationStatusRead(BaseModel):
    season_id: str
    status: str
    published_at: datetime | None = None
    message: str | None = None


class ResultNotificationRead(BaseModel):
    id: str
    kind: str
    season_id: str | None = None
    title: str
    body: str
    created_at: datetime
    read_at: datetime | None = None
