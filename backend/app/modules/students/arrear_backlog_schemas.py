"""Arrear and supplementary examination API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ArrearSubjectRead(BaseModel):
    course_code: str
    course_name: str | None = None
    backlog_status: str
    last_attempt_season_id: str | None = None
    last_outcome: str | None = None
    attempt_count: int = 0


class ExamAttemptHistoryRead(BaseModel):
    course_code: str
    season_id: str
    attempt_number: int
    outcome: str
    is_supplementary: bool
    recorded_at: datetime


class ArrearEligibilityRead(BaseModel):
    supplementary_season_id: str
    eligible: bool
    arrear_course_codes: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)


class SupplementaryScheduleRead(BaseModel):
    supplementary_season_id: str
    title: str
    registration_open_at: datetime
    registration_close_at: datetime
    parent_season_id: str | None = None


class SupplementaryFeeRead(BaseModel):
    fee_required: bool
    fee_amount: float
    fee_code: str
    payment_status: str | None = None
    fee_verified: bool = False


class SupplementaryRegistrationInput(BaseModel):
    supplementary_season_id: str
    course_code: str

    model_config = {"extra": "forbid"}


class SupplementaryRegistrationRead(BaseModel):
    registration_id: str
    supplementary_season_id: str
    course_code: str
    attempt_number: int
    status: str
    fee_verified: bool
    submitted_at: datetime | None = None


class BacklogSummaryRead(BaseModel):
    pending_count: int
    cleared_count: int
    registered_count: int
    subjects: list[ArrearSubjectRead] = Field(default_factory=list)
    progression_restrictions: list[str] = Field(default_factory=list)


class SupplementaryResultRead(BaseModel):
    season_id: str
    course_code: str
    pass_fail: str | None = None
    total_obtained: float | None = None
    total_max: float | None = None
    published_at: datetime | None = None
