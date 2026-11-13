"""Arrear, supplementary examination authority."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class SupplementaryExaminationSeason(Document):
    tenant_id: PydanticObjectId
    supplementary_season_id: str
    parent_season_id: str | None = None
    title: str
    academic_year_label: str
    semester_label: str
    registration_open_at: datetime
    registration_close_at: datetime
    fee_required: bool = True
    fee_amount: float = Field(default=0, ge=0)
    fee_code: str = "supplementary_exam_fee"
    published: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "supplementary_examination_seasons"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("supplementary_season_id", ASCENDING)],
                unique=True,
                name="unique_supplementary_season",
            ),
        ]


class ExaminationAttemptRecord(Document):
    """Official attempt log (examination cell)."""

    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    course_code: str
    season_id: str
    attempt_number: int = Field(ge=1)
    is_supplementary: bool = False
    outcome: str
    published: bool = True
    published_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_attempt_records"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("course_code", ASCENDING),
                    ("season_id", ASCENDING),
                    ("attempt_number", ASCENDING),
                ],
                unique=True,
                name="unique_exam_attempt",
            ),
        ]


class ArrearEligibilityRecord(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    supplementary_season_id: str
    eligible: bool = False
    arrear_course_codes: list[str] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    published: bool = False
    published_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "arrear_eligibility_records"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("supplementary_season_id", ASCENDING),
                ],
                unique=True,
                name="unique_arrear_eligibility",
            ),
        ]
