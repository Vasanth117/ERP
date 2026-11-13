"""Student timetable preferences, calendar references, and attendance portal models."""

from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.attendance.enums import AttendanceMarkStatus
from app.modules.students.student_schedule_enums import (
    AttendanceNotificationType,
    DiscrepancyRequestStatus,
)


class StudentTimetableView(Document):
    """Per-student timetable UI preferences (not a copy of institutional timetable)."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    default_course_filter: str | None = None
    hide_cancelled: bool = False
    show_laboratory_only: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_timetable_views"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_student_timetable_view",
            ),
        ]


class AcademicCalendarReference(Document):
    """Institutional holidays and student-visible calendar overlays."""

    tenant_id: PydanticObjectId
    academic_year_label: str
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    event_at: datetime
    event_type: str = Field(default="general", description="holiday, deadline, exam_period, etc.")
    audience: str = "students"
    department_id: PydanticObjectId | None = None
    programme_code: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "academic_calendar_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("academic_year_label", ASCENDING), ("event_at", ASCENDING)],
                name="calendar_ref_by_year",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("event_type", ASCENDING), ("event_at", ASCENDING)],
                name="calendar_ref_by_type",
            ),
        ]


class StudentAttendanceDiscrepancyRequest(Document):
    """Student-submitted attendance correction requests (read-only on official marks)."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    session_id: PydanticObjectId
    course_code: str
    section: str
    session_date: date
    recorded_status: AttendanceMarkStatus | None = None
    claimed_status: AttendanceMarkStatus
    reason: str = Field(min_length=10, max_length=2000)
    status: DiscrepancyRequestStatus = DiscrepancyRequestStatus.PENDING
    reviewer_note: str | None = Field(default=None, max_length=2000)
    submitted_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None

    class Settings:
        name = "student_attendance_discrepancy_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("status", ASCENDING)],
                name="discrepancy_by_student_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("submitted_at", DESCENDING)],
                name="discrepancy_by_student_time",
            ),
        ]


class AttendanceNotificationRecord(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    notification_type: AttendanceNotificationType
    title: str
    body: str
    course_code: str | None = None
    related_change_id: PydanticObjectId | None = None
    read_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "attendance_notification_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="attendance_notifications_by_user",
            ),
        ]
