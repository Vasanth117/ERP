"""College admin academic configuration collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class ConfigPublicationStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AcademicCalendarEventEmbed(BaseModel):
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    event_at: datetime
    event_type: str = "general"
    audience: str = "all"


class AcademicYear(Document):
    tenant_id: PydanticObjectId
    year_code: str = Field(min_length=4, max_length=32)
    label: str = Field(min_length=4, max_length=64)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    status: ConfigPublicationStatus = ConfigPublicationStatus.DRAFT
    version: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "academic_years"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("year_code", ASCENDING)],
                unique=True,
                name="unique_academic_year_code",
            ),
            IndexModel([("tenant_id", ASCENDING), ("is_current", ASCENDING)], name="academic_years_current"),
        ]


class AcademicTerm(Document):
    tenant_id: PydanticObjectId
    academic_year_id: PydanticObjectId
    term_code: str = Field(min_length=2, max_length=32)
    label: str = Field(min_length=2, max_length=64)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    status: ConfigPublicationStatus = ConfigPublicationStatus.DRAFT
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "academic_terms"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("academic_year_id", ASCENDING), ("term_code", ASCENDING)],
                unique=True,
                name="unique_academic_term",
            ),
            IndexModel([("tenant_id", ASCENDING), ("is_current", ASCENDING)], name="academic_terms_current"),
        ]


class AcademicCalendar(Document):
    tenant_id: PydanticObjectId
    academic_year_id: PydanticObjectId
    academic_term_id: PydanticObjectId | None = None
    title: str = Field(max_length=200)
    events: list[AcademicCalendarEventEmbed] = Field(default_factory=list)
    status: ConfigPublicationStatus = ConfigPublicationStatus.DRAFT
    published_at: datetime | None = None
    version: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "academic_calendars"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("academic_year_id", ASCENDING)], name="calendars_by_year"),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="calendars_by_status"),
        ]


class AcademicProgramme(Document):
    tenant_id: PydanticObjectId
    programme_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    department_id: PydanticObjectId | None = None
    duration_semesters: int = Field(default=8, ge=1, le=20)
    credits_required: float = Field(default=160, ge=0)
    is_active: bool = True
    status: ConfigPublicationStatus = ConfigPublicationStatus.DRAFT
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "academic_programmes"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("programme_code", ASCENDING)],
                unique=True,
                name="unique_programme_code",
            ),
        ]


class AcademicRegulation(Document):
    tenant_id: PydanticObjectId
    scope_key: str = Field(description="grading|attendance|progression|examination|registration")
    rules: dict[str, Any] = Field(default_factory=dict)
    status: ConfigPublicationStatus = ConfigPublicationStatus.DRAFT
    version: int = 1
    effective_from: date | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "academic_regulations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("scope_key", ASCENDING), ("version", DESCENDING)],
                name="regulations_by_scope",
            ),
        ]


class AcademicConfigurationVersion(Document):
    tenant_id: PydanticObjectId
    scope: str
    resource_id: str
    version_number: int
    snapshot: dict[str, Any] = Field(default_factory=dict)
    published_at: datetime = Field(default_factory=utcnow)
    published_by: PydanticObjectId | None = None

    class Settings:
        name = "academic_configuration_versions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("scope", ASCENDING), ("version_number", DESCENDING)],
                name="academic_config_versions",
            ),
        ]
