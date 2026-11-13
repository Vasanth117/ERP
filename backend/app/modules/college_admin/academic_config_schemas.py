"""Academic configuration API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.college_admin.academic_config_models import (
    AcademicCalendar,
    AcademicProgramme,
    AcademicRegulation,
    AcademicTerm,
    AcademicYear,
    ConfigPublicationStatus,
)


class AcademicYearCreate(BaseModel):
    year_code: str = Field(min_length=4, max_length=32)
    label: str = Field(min_length=4, max_length=64)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class AcademicYearUpdate(BaseModel):
    label: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None


class AcademicYearRead(BaseModel):
    year_id: str
    year_code: str
    label: str
    start_date: date | None
    end_date: date | None
    is_current: bool
    status: ConfigPublicationStatus
    version: int

    @classmethod
    def from_document(cls, doc: AcademicYear) -> "AcademicYearRead":
        return cls(
            year_id=str(doc.id),
            year_code=doc.year_code,
            label=doc.label,
            start_date=doc.start_date,
            end_date=doc.end_date,
            is_current=doc.is_current,
            status=doc.status,
            version=doc.version,
        )


class AcademicTermCreate(BaseModel):
    academic_year_id: str
    term_code: str = Field(min_length=2, max_length=32)
    label: str = Field(min_length=2, max_length=64)
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class AcademicTermRead(BaseModel):
    term_id: str
    academic_year_id: str
    term_code: str
    label: str
    start_date: date | None
    end_date: date | None
    is_current: bool
    status: ConfigPublicationStatus

    @classmethod
    def from_document(cls, doc: AcademicTerm) -> "AcademicTermRead":
        return cls(
            term_id=str(doc.id),
            academic_year_id=str(doc.academic_year_id),
            term_code=doc.term_code,
            label=doc.label,
            start_date=doc.start_date,
            end_date=doc.end_date,
            is_current=doc.is_current,
            status=doc.status,
        )


class AcademicCalendarCreate(BaseModel):
    academic_year_id: str
    academic_term_id: str | None = None
    title: str = Field(max_length=200)
    events: list[dict[str, Any]] = Field(default_factory=list)


class AcademicCalendarRead(BaseModel):
    calendar_id: str
    title: str
    academic_year_id: str
    academic_term_id: str | None
    status: ConfigPublicationStatus
    events_count: int
    version: int

    @classmethod
    def from_document(cls, doc: AcademicCalendar) -> "AcademicCalendarRead":
        return cls(
            calendar_id=str(doc.id),
            title=doc.title,
            academic_year_id=str(doc.academic_year_id),
            academic_term_id=str(doc.academic_term_id) if doc.academic_term_id else None,
            status=doc.status,
            events_count=len(doc.events),
            version=doc.version,
        )


class ProgrammeCreate(BaseModel):
    programme_code: str
    name: str
    department_id: str | None = None
    duration_semesters: int = 8
    credits_required: float = 160


class ProgrammeRead(BaseModel):
    programme_id: str
    programme_code: str
    name: str
    department_id: str | None
    duration_semesters: int
    credits_required: float
    is_active: bool
    status: ConfigPublicationStatus

    @classmethod
    def from_document(cls, doc: AcademicProgramme) -> "ProgrammeRead":
        return cls(
            programme_id=str(doc.id),
            programme_code=doc.programme_code,
            name=doc.name,
            department_id=str(doc.department_id) if doc.department_id else None,
            duration_semesters=doc.duration_semesters,
            credits_required=doc.credits_required,
            is_active=doc.is_active,
            status=doc.status,
        )


class RegulationUpsert(BaseModel):
    scope_key: str = Field(pattern=r"^(grading|attendance|progression|examination|registration)$")
    rules: dict[str, Any] = Field(default_factory=dict)
    effective_from: date | None = None


class RegulationRead(BaseModel):
    regulation_id: str
    scope_key: str
    rules: dict[str, Any]
    status: ConfigPublicationStatus
    version: int

    @classmethod
    def from_document(cls, doc: AcademicRegulation) -> "RegulationRead":
        return cls(
            regulation_id=str(doc.id),
            scope_key=doc.scope_key,
            rules=doc.rules,
            status=doc.status,
            version=doc.version,
        )


class CourseAdminCreate(BaseModel):
    course_code: str
    name: str
    credit_units: float = 0
    department_id: str | None = None


class CourseAdminRead(BaseModel):
    course_id: str
    course_code: str
    name: str
    credit_units: float
    is_active: bool


class SectionCreate(BaseModel):
    course_id: str
    course_code: str
    section_code: str
    batch_label: str | None = None
    academic_year_label: str
    semester_label: str


class ConfigHistoryRead(BaseModel):
    scope: str
    resource_id: str
    version_number: int
    published_at: datetime
