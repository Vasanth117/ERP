"""Examination administration API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.college_admin.examination_admin_models import ExaminationConfiguration, ExaminationType
from app.modules.examinations.enums import MarksBatchStatus


class ExaminationConfigUpsert(BaseModel):
    season_id: str
    title: str
    academic_year_label: str
    semester_label: str
    examination_type: ExaminationType = ExaminationType.SEMESTER
    component_definitions: list[dict[str, Any]] = Field(default_factory=list)
    regulations: dict[str, Any] = Field(default_factory=dict)


class ExaminationConfigRead(BaseModel):
    configuration_id: str
    season_id: str
    title: str
    examination_type: ExaminationType
    published: bool
    version: int

    @classmethod
    def from_document(cls, doc: ExaminationConfiguration) -> "ExaminationConfigRead":
        return cls(
            configuration_id=str(doc.id),
            season_id=doc.season_id,
            title=doc.title,
            examination_type=doc.examination_type,
            published=doc.published,
            version=doc.version,
        )


class ExaminationSeasonCreate(BaseModel):
    season_id: str
    title: str
    academic_year_label: str
    semester_label: str
    starts_at: datetime
    ends_at: datetime


class ExaminationSessionCreate(BaseModel):
    season_id: str
    session_code: str
    course_code: str
    course_name: str | None = None
    section: str | None = None
    scheduled_start: datetime
    scheduled_end: datetime | None = None
    centre_code: str | None = None
    room: str | None = None


class RegistrationWindowUpsert(BaseModel):
    season_id: str
    registration_open_at: datetime
    registration_close_at: datetime
    fee_amount: float = 0
    fee_code: str = "exam_fee"


class EligibilityUpsert(BaseModel):
    student_user_id: str
    season_id: str
    eligible: bool
    reasons: list[str] = Field(default_factory=list)


class HallTicketGenerate(BaseModel):
    student_user_id: str
    season_id: str
    roll_number: str | None = None
    student_name: str | None = None
    centre_code: str | None = None


class MarksBatchDecision(BaseModel):
    batch_id: str
    decision: MarksBatchStatus
    note: str | None = None


class ResultPublishRequest(BaseModel):
    student_user_id: str
    season_id: str
    academic_year_label: str
    semester_label: str


class ReviewWindowUpsert(BaseModel):
    season_id: str
    review_type: str = "revaluation"
    application_open_at: datetime
    application_close_at: datetime
    fee_amount: float = 0
    fee_code: str = "reval_fee"
