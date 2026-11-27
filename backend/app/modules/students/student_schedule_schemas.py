"""Student timetable and attendance API schemas."""

from datetime import date, datetime, time
from typing import Literal

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


class TimetableOverviewKpisRead(BaseModel):
    classes_today: int
    classes_this_week: int
    next_exam_label: str | None = None
    next_exam_hint: str | None = None
    changes_count: int
    changes_new_count: int
    changes_hint: str | None = None


class TimetableOverviewTodayRowRead(BaseModel):
    id: str
    start_time: time
    end_time: time
    subject_label: str
    session_type_label: str
    room_label: str
    faculty_label: str


class TimetableOverviewHighlightRead(BaseModel):
    id: str
    kind: Literal["change", "holiday", "calendar"]
    title: str
    subtitle: str | None = None
    badge_label: str
    badge_tone: str


class TimetableOverviewPageRead(BaseModel):
    page_title: str = "Timetable Dashboard"
    anchor_date: date
    iso_week_number: int
    academic_year_label: str
    semester_label: str
    kpis: TimetableOverviewKpisRead
    today_rows: list[TimetableOverviewTodayRowRead]
    today_sessions_footer: str
    highlights: list[TimetableOverviewHighlightRead] = Field(default_factory=list)


class TimetableCourseFilterOptionRead(BaseModel):
    value: str
    label: str


class TimetableDailySessionRowRead(BaseModel):
    slot_id: str
    start_time: time
    end_time: time
    course_code: str
    subject_label: str
    session_type_label: str
    room_label: str
    faculty_label: str
    status_label: str
    status_tone: str


class TimetableSessionDetailFieldRead(BaseModel):
    label: str
    value: str


class TimetableSessionDetailRead(BaseModel):
    slot_id: str
    panel_title: str = "Class session details"
    headline: str
    subheadline: str | None = None
    fields: list[TimetableSessionDetailFieldRead] = Field(default_factory=list)


class TimetableDailyPageRead(BaseModel):
    page_title: str = "Daily timetable"
    page_subtitle: str
    anchor_date: date
    prev_date: date
    next_date: date
    academic_year_label: str
    semester_label: str
    course_filter_options: list[TimetableCourseFilterOptionRead]
    selected_course_code: str | None = None
    timeline_rows: list[TimetableDailySessionRowRead]
    timeline_footer: str
    session_detail: TimetableSessionDetailRead | None = None


class TimetableWeeklyDayColumnRead(BaseModel):
    anchor_date: date
    day_label: str
    short_label: str
    session_count: int
    slots: list[TimetableDailySessionRowRead]


class TimetableWeeklyPageRead(BaseModel):
    page_title: str = "Weekly timetable"
    page_subtitle: str
    anchor_date: date
    academic_year_label: str
    semester_label: str
    course_filter_options: list[TimetableCourseFilterOptionRead]
    selected_course_code: str | None = None
    days: list[TimetableWeeklyDayColumnRead]
    week_footer: str


class TimetableMonthlyDayCellRead(BaseModel):
    anchor_date: date
    in_month: bool
    day_number: int | None = None
    session_count: int
    is_today: bool = False


class TimetableMonthlyPageRead(BaseModel):
    page_title: str = "Monthly timetable"
    page_subtitle: str
    anchor_date: date
    academic_year_label: str
    semester_label: str
    weekday_labels: list[str]
    weeks: list[list[TimetableMonthlyDayCellRead]]
    month_footer: str


class TimetableLaboratoryPageRead(BaseModel):
    page_title: str = "Laboratory timetable"
    page_subtitle: str
    anchor_date: date
    prev_date: date
    next_date: date
    academic_year_label: str
    semester_label: str
    course_filter_options: list[TimetableCourseFilterOptionRead]
    selected_course_code: str | None = None
    timeline_rows: list[TimetableDailySessionRowRead]
    timeline_footer: str
    session_detail: TimetableSessionDetailRead | None = None
