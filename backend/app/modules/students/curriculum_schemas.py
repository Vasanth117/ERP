"""Student curriculum and course registration API schemas."""

from datetime import datetime, time
from typing import Any

from pydantic import BaseModel, Field

from app.modules.academics.curriculum_models import SyllabusUnit, TeachingMaterialRef
from app.modules.students.registration_enums import (
    CourseRegistrationStatus,
    CourseRegistrationType,
    RegistrationRequestStatus,
)


class EnrolledCourseItemRead(BaseModel):
    course_id: str
    course_code: str
    name: str
    section_code: str | None = None
    credit_units: float
    academic_year_label: str
    semester_label: str
    source: str


class SubjectItemRead(BaseModel):
    subject_id: str
    subject_code: str
    name: str
    description: str | None = None
    credit_units: float = 0
    sequence_order: int = 1


class CurriculumRead(BaseModel):
    programme_code: str
    academic_year_label: str
    semester_label: str
    version: str | None = None
    summary: str | None = None
    academic_regulations: list[str] = Field(default_factory=list)
    locked: bool = True


class SyllabusRevisionRead(BaseModel):
    version: str
    effective_at: datetime
    summary: str | None = None


class SyllabusDetailRead(BaseModel):
    course_id: str
    subject_id: str | None = None
    academic_year_label: str
    semester_label: str
    units: list[SyllabusUnit]
    objectives: list[str]
    teaching_materials: list[TeachingMaterialRef]
    revision_history: list[SyllabusRevisionRead]
    locked: bool = True


class LearningOutcomesDetailRead(BaseModel):
    course_id: str
    academic_year_label: str
    semester_label: str
    outcomes: list[str]
    locked: bool = True


class PrerequisiteRead(BaseModel):
    course_id: str
    course_code: str
    prerequisite_course_ids: list[str]
    corequisite_course_ids: list[str]
    min_cgpa: float | None = None
    notes: str | None = None


class FacultyInfoRead(BaseModel):
    faculty_user_id: str
    display_name: str
    section: str
    subject_code: str | None = None


class CourseInfoRead(BaseModel):
    course_id: str
    course_code: str
    name: str
    description: str | None = None
    credit_units: float
    faculty: list[FacultyInfoRead] = Field(default_factory=list)


class SemesterSubjectsRead(BaseModel):
    academic_year_label: str
    semester_label: str
    subjects: list[SubjectItemRead]


class AvailableCourseRead(BaseModel):
    course_id: str
    course_code: str
    name: str
    credit_units: float
    registration_type: CourseRegistrationType
    is_open_for_registration: bool
    prerequisites_met: bool | None = None
    max_capacity: int | None = None


class ElectiveGroupRead(BaseModel):
    id: str
    group_code: str
    title: str
    description: str | None = None
    min_selections: int
    max_selections: int
    min_credits: float
    max_credits: float


class ElectiveOptionRead(BaseModel):
    course_id: str
    course_code: str
    course_name: str
    credit_units: float
    seats_available: int | None = None
    eligible: bool = True


class RegistrationEligibilityRead(BaseModel):
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    min_credits: float | None = None
    max_credits: float | None = None
    registration_open_at: datetime | None = None
    registration_close_at: datetime | None = None
    modification_deadline: datetime | None = None
    window_open: bool = False


class RegistrationSelectionInput(BaseModel):
    course_id: str
    course_code: str
    section_code: str | None = None
    registration_type: CourseRegistrationType = CourseRegistrationType.ELECTIVE
    elective_group_id: str | None = None

    model_config = {"extra": "forbid"}


class RegistrationValidationRead(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    total_credits: float = 0
    timetable_conflicts: list[str] = Field(default_factory=list)


class RegistrationSubmitRead(BaseModel):
    request_id: str
    status: RegistrationRequestStatus
    selections: list[RegistrationSelectionInput]
    submitted_at: datetime | None = None


class CourseRegistrationRead(BaseModel):
    id: str
    course_id: str
    course_code: str
    section_code: str | None = None
    registration_type: CourseRegistrationType
    credit_units: float
    status: CourseRegistrationStatus
    academic_year_label: str
    semester_label: str


class RegistrationRequestRead(BaseModel):
    id: str
    status: RegistrationRequestStatus
    academic_year_label: str
    semester_label: str
    selections: list[RegistrationSelectionInput]
    reviewer_note: str | None = None
    submitted_at: datetime | None = None
    resolved_at: datetime | None = None


class RegistrationHistoryRead(BaseModel):
    id: str
    course_code: str
    action: str
    previous_status: str | None = None
    new_status: str | None = None
    occurred_at: datetime


class TimetableSlotCheck(BaseModel):
    course_code: str
    day_of_week: int
    start_time: time
    end_time: time
