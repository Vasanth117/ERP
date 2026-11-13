"""Authoritative academic records read by faculty and other modules.

Academic Management owns writes to these collections; faculty services aggregate
read-only data for dashboards and teaching views.
"""

from datetime import date, datetime, time
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.academics.enums import SessionType, TimetableEntryStatus


class AcademicYearContext(Document):
    """Current academic year and semester per tenant."""

    tenant_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    semester_start: date | None = None
    semester_end: date | None = None
    is_current: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "academic_year_context"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("is_current", ASCENDING)],
                name="academic_context_current_per_tenant",
            ),
        ]


class TimetableEntry(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    day_of_week: int = Field(ge=0, le=6, description="0=Monday")
    start_time: time
    end_time: time
    course_code: str
    course_name: str
    course_id: str | None = None
    section: str
    section_id: str | None = None
    session_type: SessionType = SessionType.LECTURE
    room: str | None = None
    room_id: str | None = None
    laboratory: str | None = None
    status: TimetableEntryStatus = TimetableEntryStatus.ACTIVE
    effective_from: date | None = None
    effective_to: date | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "timetable_entries"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("day_of_week", ASCENDING)],
                name="timetable_by_faculty_day",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("status", ASCENDING)],
                name="timetable_by_faculty_status",
            ),
        ]


class PendingAttendanceSubmission(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    class_label: str
    section: str
    session_date: date
    due_at: datetime
    status: str = "pending"
    course_code: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "pending_attendance_submissions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("status", ASCENDING)],
                name="pending_attendance_by_faculty",
            ),
            IndexModel([("due_at", ASCENDING)], name="pending_attendance_due"),
        ]


class UpcomingAssessment(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    course_code: str
    title: str
    assessment_type: str
    scheduled_at: datetime
    academic_year_label: str
    semester_label: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "upcoming_assessments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("scheduled_at", ASCENDING)],
                name="assessments_by_faculty_schedule",
            ),
        ]


class PendingAssignmentEvaluation(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    assignment_id: str
    title: str
    course_code: str
    submissions_pending: int = Field(ge=0)
    due_at: datetime
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "pending_assignment_evaluations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("due_at", ASCENDING)],
                name="evaluations_by_faculty_due",
            ),
        ]


class AcademicCalendarEvent(Document):
    tenant_id: PydanticObjectId
    title: str
    description: str | None = None
    event_at: datetime
    event_type: str = "general"
    audience: str = "faculty"
    department_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "academic_calendar_events"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("event_at", ASCENDING)],
                name="calendar_events_by_tenant",
            ),
        ]


# Backwards-compatible alias for Phase 1 readers
AcademicEvent = AcademicCalendarEvent


class ClassSession(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    timetable_entry_id: PydanticObjectId | None = None
    course_id: str | None = None
    course_code: str
    section: str
    session_type: SessionType = SessionType.LECTURE
    scheduled_start: datetime
    scheduled_end: datetime
    room: str | None = None
    laboratory: str | None = None
    status: str = "scheduled"
    topic: str | None = None
    original_session_id: PydanticObjectId | None = None
    academic_year_label: str
    semester_label: str
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "class_sessions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("scheduled_start", ASCENDING)],
                name="sessions_by_faculty_start",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("status", ASCENDING)],
                name="sessions_by_faculty_status",
            ),
        ]


class ExaminationSchedule(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId | None = None
    course_code: str
    section: str | None = None
    exam_type: str
    title: str
    scheduled_at: datetime
    scheduled_end: datetime | None = None
    room: str | None = None
    centre_code: str | None = None
    centre_name: str | None = None
    instructions: str | None = None
    examination_session_code: str | None = None
    academic_year_label: str
    semester_label: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_schedules"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("scheduled_at", ASCENDING)],
                name="exams_by_faculty",
            ),
        ]


class TimetableChangeLog(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    change_type: str
    summary: str
    effective_at: datetime
    related_session_id: PydanticObjectId | None = None
    previous_values: dict[str, Any] = Field(default_factory=dict)
    new_values: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "timetable_change_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("effective_at", DESCENDING)],
                name="timetable_changes_by_faculty",
            ),
        ]
