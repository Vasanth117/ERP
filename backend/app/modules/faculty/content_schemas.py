"""Phase 2 course and timetable API schemas."""

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, Field

from app.modules.academics.curriculum_models import SyllabusUnit, TeachingMaterialRef
from app.modules.academics.enums import SessionType
from app.modules.faculty.enums import SessionUpdateRequestType


class AssignedCourseListItem(BaseModel):
    assignment_id: str
    course_id: str | None
    course_code: str
    course_name: str
    section: str
    academic_year_label: str
    semester_label: str


class AssignedSubjectItem(BaseModel):
    subject_id: str
    subject_code: str
    name: str
    description: str | None = None


class CourseDetailRead(BaseModel):
    course_id: str
    course_code: str
    name: str
    description: str | None
    credit_units: float
    academic_year_label: str | None
    semester_label: str | None


class SyllabusRead(BaseModel):
    course_id: str
    subject_id: str | None
    academic_year_label: str
    semester_label: str
    units: list[SyllabusUnit]
    objectives: list[str]
    teaching_materials: list[TeachingMaterialRef]
    locked: bool


class LearningOutcomesRead(BaseModel):
    course_id: str
    academic_year_label: str
    semester_label: str
    outcomes: list[str]
    locked: bool


class EnrolledStudentRead(BaseModel):
    roll_number: str
    display_name: str
    student_user_id: str


class SectionBatchRead(BaseModel):
    section_id: str
    section_code: str
    batch_label: str | None


class TeachingProgressRead(BaseModel):
    unit_no: int | None
    notes: str
    percent_complete: float | None
    recorded_at: datetime


class CourseCoverageRead(BaseModel):
    course_id: str
    course_code: str
    section: str
    subject_id: str | None
    academic_year_label: str
    semester_label: str
    units_completed: list[int]
    percent_complete: float
    progress_log: list[TeachingProgressRead]
    updated_at: datetime


class CourseCoverageUpdate(BaseModel):
    units_completed: list[int] | None = None
    percent_complete: float | None = Field(default=None, ge=0, le=100)
    progress_note: str | None = Field(default=None, max_length=2000)
    unit_no: int | None = Field(default=None, ge=1)

    model_config = {"extra": "forbid"}


class TimetableSlotRead(BaseModel):
    id: str
    day_of_week: int
    start_time: time
    end_time: time
    course_code: str
    course_name: str
    section: str
    session_type: SessionType
    room: str | None
    laboratory: str | None
    status: str


class TimetableDayRead(BaseModel):
    anchor_date: date
    slots: list[TimetableSlotRead]
    conflicts: list[str]


class TimetableWeekRead(BaseModel):
    anchor_date: date
    days: list[TimetableDayRead]
    conflicts: list[str]


class ClassSessionRead(BaseModel):
    id: str
    course_code: str
    section: str
    session_type: SessionType
    scheduled_start: datetime
    scheduled_end: datetime
    room: str | None
    laboratory: str | None
    status: str
    topic: str | None


class ClassroomSummary(BaseModel):
    room: str | None
    laboratory: str | None
    session_count: int


class CalendarEventRead(BaseModel):
    id: str
    title: str
    description: str | None
    event_at: datetime
    event_type: str


class ExaminationScheduleRead(BaseModel):
    id: str
    title: str
    course_code: str
    section: str | None
    exam_type: str
    scheduled_at: datetime
    room: str | None


class TimetableChangeRead(BaseModel):
    id: str
    change_type: str
    summary: str
    effective_at: datetime
    related_session_id: str | None


class TimetableNotificationRead(BaseModel):
    id: str
    title: str
    body: str
    created_at: datetime
    read_at: datetime | None


class SessionUpdateRequestCreate(BaseModel):
    request_type: SessionUpdateRequestType
    reason: str | None = Field(default=None, max_length=500)
    topic: str | None = Field(default=None, max_length=500)
    proposed_start: datetime | None = None
    proposed_end: datetime | None = None

    model_config = {"extra": "forbid"}


class SessionUpdateRequestRead(BaseModel):
    id: str
    class_session_id: str
    request_type: SessionUpdateRequestType
    status: str
    payload: dict[str, Any]
    reason: str | None
    created_at: datetime
