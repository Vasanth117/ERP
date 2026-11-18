"""Department Admin phase 4 — timetable and attendance oversight."""

from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.modules.department_admin.models import DepartmentRequestStatus, DepartmentTimetableStatus


class TimetablePlanCreate(BaseModel):
    academic_year_label: str = Field(min_length=2, max_length=32)
    semester_label: str = Field(min_length=1, max_length=32)
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    title: str = Field(min_length=2, max_length=200)


class TimetablePlanUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    programme_code: str | None = None
    batch_label: str | None = None


class TimetablePlanRead(BaseModel):
    timetable_id: str
    academic_year_label: str
    semester_label: str
    programme_code: str | None
    batch_label: str | None
    title: str
    status: DepartmentTimetableStatus
    revision: int
    published_version: int
    slot_count: int = 0
    created_at: datetime
    updated_at: datetime


class TimetableSlotCreate(BaseModel):
    faculty_user_id: str
    section: str = Field(min_length=1, max_length=16)
    course_code: str = Field(min_length=2, max_length=32)
    course_name: str = Field(min_length=2, max_length=200)
    course_id: str | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    session_type: str = "lecture"
    room: str | None = Field(default=None, max_length=64)
    room_id: str | None = None
    laboratory: str | None = Field(default=None, max_length=64)


class TimetableSlotUpdate(BaseModel):
    faculty_user_id: str | None = None
    section: str | None = None
    course_code: str | None = None
    course_name: str | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    start_time: time | None = None
    end_time: time | None = None
    session_type: str | None = None
    room: str | None = None
    laboratory: str | None = None
    revision: int | None = None


class TimetableSlotRead(BaseModel):
    slot_id: str
    plan_id: str
    faculty_user_id: str
    section: str
    course_code: str
    course_name: str
    day_of_week: int
    start_time: time
    end_time: time
    session_type: str
    room: str | None
    laboratory: str | None
    revision: int


class TimetableConflictRead(BaseModel):
    conflict_type: str
    message: str
    details: dict = Field(default_factory=dict)


class TimetableValidationResult(BaseModel):
    valid: bool
    conflicts: list[TimetableConflictRead]


class TimetablePublishBody(BaseModel):
    idempotency_key: str | None = Field(default=None, max_length=64)


class TimetableChangeCreate(BaseModel):
    slot_id: str | None = None
    change_type: str = Field(min_length=2, max_length=32)
    reason: str = Field(min_length=3, max_length=2000)
    new_values: dict = Field(default_factory=dict)


class TimetableChangeRead(BaseModel):
    request_id: str
    plan_id: str
    change_type: str
    status: DepartmentRequestStatus
    reason: str
    created_at: datetime


class AttendanceOverviewRead(BaseModel):
    sessions_submitted: int
    pending_submissions: int
    correction_requests_open: int
    missing_submission_count: int
    policy_min_percentage: float | None
    threshold_source: str


class AttendanceClassSummary(BaseModel):
    course_code: str
    section: str
    sessions_scheduled: int
    sessions_submitted: int
    sessions_missing: int


class AttendanceSubjectSummary(BaseModel):
    course_code: str
    sections: list[str]
    submitted_count: int
    missing_count: int


class AttendanceStudentSummary(BaseModel):
    student_user_id: str
    roll_number: str | None
    percentage: float
    threshold: float
    below_threshold: bool
    sessions_counted: int


class AttendanceFacultySubmissionRead(BaseModel):
    faculty_user_id: str
    full_name: str | None
    submitted_sessions: int
    pending_sessions: int
    late_submissions: int


class AttendanceMissingSessionRead(BaseModel):
    faculty_user_id: str
    course_code: str | None
    section: str | None
    session_date: date
    status: str


class AttendanceShortageRead(BaseModel):
    student_user_id: str
    course_code: str
    section: str
    percentage: float
    threshold: float
    attended_weight: float
    eligible_sessions: int


class AttendanceDiscrepancyRead(BaseModel):
    discrepancy_id: str
    discrepancy_type: str
    summary: str
    session_id: str | None
    status: str
    detected_at: datetime


class AttendanceCorrectionRead(BaseModel):
    request_id: str
    faculty_user_id: str
    session_id: str
    student_user_id: str | None
    status: str
    reason: str
    created_at: datetime


class AttendanceCorrectionReview(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    reviewer_note: str | None = Field(default=None, max_length=500)


class AttendanceOverviewFilters(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None