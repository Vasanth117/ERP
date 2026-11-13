"""Exam review request API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ReviewEligibleSubjectRead(BaseModel):
    season_id: str
    course_code: str
    eligible_for_revaluation: bool = True
    eligible_for_rechecking: bool = True
    eligible_for_correction: bool = False
    review_window_open: bool = False


class ReviewFeeDetailsRead(BaseModel):
    review_type: str
    season_id: str
    fee_required: bool
    fee_amount: float
    fee_code: str
    payment_status: str | None = None
    fee_verified: bool = False
    application_close_at: datetime | None = None


class ReviewRequestSubmitInput(BaseModel):
    season_id: str
    course_code: str
    component_id: str | None = None
    reason: str = Field(min_length=10, max_length=2000)

    model_config = {"extra": "forbid"}


class ReviewRequestRead(BaseModel):
    request_id: str
    request_type: str
    season_id: str
    course_code: str
    component_id: str | None = None
    status: str
    reason: str
    fee_verified: bool = False
    revised_mark_published: bool = False
    created_at: datetime
    updated_at: datetime


class ReviewRequestHistoryRead(BaseModel):
    request_id: str
    request_type: str
    action: str
    note: str | None = None
    created_at: datetime


class RevisedMarkRead(BaseModel):
    season_id: str
    course_code: str
    component_id: str | None = None
    marks_obtained: float | None = None
    max_marks: float | None = None
    published_at: datetime | None = None
