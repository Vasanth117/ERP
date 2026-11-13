"""Student timetable and attendance API schemas."""

from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.modules.academics.enums import SessionType
from app.modules.attendance.enums import AttendanceMarkStatus
from app.modules.students.student_schedule_enums import AttendanceDataStatus, DiscrepancyRequestStatus


class FacultySlotInfo(BaseModel):
    faculty_user_id: str
    display_name: str
    role: str | None = None


class StudentTimetableSlotRead(BaseModel):
    id: str
    day_of_week: int
    start_time: time
    end_time: time
    course_code: str
    course_name: str
    section: str
    session_type: SessionType
    room: str | None = None
    laboratory: str | None = None
    status: str
    faculty: list[FacultySlotInfo] = Field(default_factory=list)


class StudentTimetableDayRead(BaseModel):
    anchor_date: date
    slots: list[StudentTimetableSlotRead]


class StudentTimetableWeekRead(BaseModel):
    anchor_date: date
    days: list[StudentTimetableDayRead]


class StudentTimetableSemesterRead(BaseModel):
    academic_year_label: str
    semester_label: str
    slots: list[StudentTimetableSlotRead]
    cancelled_slots: list[StudentTimetableSlotRead] = Field(default_factory=list)
    rescheduled_slots: list[StudentTimetableSlotRead] = Field(default_factory=list)


class CalendarEventStudentRead(BaseModel):
    id: str
    title: str
    description: str | None = None
    event_at: datetime
    event_type: str
    source: str = "academic"


class ExaminationScheduleStudentRead(BaseModel):
    id: str
    title: str
    course_code: str
    section: str | None = None
    exam_type: str
    scheduled_at: datetime
    room: str | None = None


class TimetableChangeStudentRead(BaseModel):
    id: str
    change_type: str
    summary: str
    effective_at: datetime
    related_session_id: str | None = None


class TimetableNotificationStudentRead(BaseModel):
    id: str
    title: str
    body: str
    notification_type: str
    created_at: datetime
    read_at: datetime | None = None


class ClassSessionStudentRead(BaseModel):
    id: str
    course_code: str
    section: str
    session_type: SessionType
    scheduled_start: datetime
    scheduled_end: datetime
    room: str | None = None
    laboratory: str | None = None
    status: str
    topic: str | None = None


class AttendanceMarkRead(BaseModel):
    session_id: str
    session_date: date
    course_code: str
    section: str
    status: AttendanceMarkStatus | None = None
    verified: bool = False


class SubjectAttendanceDetailRead(BaseModel):
    course_code: str
    section: str
    subject_id: str | None = None
    percentage: float | None = None
    sessions_held: int = 0
    sessions_recorded: int = 0
    min_required: float
    below_threshold: bool = False
    data_status: AttendanceDataStatus = AttendanceDataStatus.NOT_AVAILABLE


class AttendanceSemesterSummaryRead(BaseModel):
    academic_year_label: str
    semester_label: str
    overall_percentage: float | None = None
    min_required: float
    data_status: AttendanceDataStatus
    subjects: list[SubjectAttendanceDetailRead]
    shortage_warnings: list[str] = Field(default_factory=list)


class AttendanceEligibilityRead(BaseModel):
    eligible: bool
    overall_percentage: float | None = None
    min_required: float
    reasons: list[str] = Field(default_factory=list)
    data_status: AttendanceDataStatus


class AttendanceShortageRead(BaseModel):
    course_code: str
    section: str
    percentage: float | None
    min_required: float
    sessions_remaining_to_clear: int | None = None


class DiscrepancyRequestCreate(BaseModel):
    session_id: str
    claimed_status: AttendanceMarkStatus
    reason: str = Field(min_length=10, max_length=2000)

    model_config = {"extra": "forbid"}


class DiscrepancyRequestRead(BaseModel):
    id: str
    session_id: str
    course_code: str
    section: str
    session_date: date
    recorded_status: AttendanceMarkStatus | None = None
    claimed_status: AttendanceMarkStatus
    reason: str
    status: DiscrepancyRequestStatus
    reviewer_note: str | None = None
    submitted_at: datetime
    resolved_at: datetime | None = None


class AttendanceSummaryExportRead(BaseModel):
    generated_at: datetime
    academic_year_label: str
    semester_label: str
    data_status: AttendanceDataStatus
    csv_content: str
