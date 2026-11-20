"""Institution calendar holidays and working-week configuration."""

from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, IndexModel

from app.common.time import utcnow


class InstitutionHoliday(Document):
    tenant_id: PydanticObjectId
    academic_year_id: PydanticObjectId
    holiday_id: str = Field(max_length=64)
    title: str = Field(max_length=200)
    start_date: date
    end_date: date | None = None
    holiday_type: str = Field(max_length=32)
    applies_to: str = Field(max_length=32)
    sort_order: int = 0
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "institution_holidays"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("holiday_id", ASCENDING)],
                unique=True,
                name="unique_institution_holiday",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("academic_year_id", ASCENDING), ("start_date", ASCENDING)],
                name="holidays_by_year",
            ),
        ]