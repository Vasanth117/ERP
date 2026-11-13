"""Faculty attendance API schemas."""

from datetime import date, datetime

from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.modules.attendance.enums import AttendanceMarkStatus, AttendanceSessionStatus


class AssignedClassRead(BaseModel):
    course_code: str
    course_name: str
    section: str
    course_id: str | None
    subject_id: str | None = None


class AttendanceSessionCreate(BaseModel):
    course_code: str
    section: str
    session_date: date
    subject_id: str | None = None
    class_session_id: str | None = None

    model_config = {"extra": "forbid"}


class AttendanceSessionRead(BaseModel):
    id: str
    course_code: str
    section: str
    session_date: date
    status: AttendanceSessionStatus
    subject_id: str | None
    submitted_at: datetime | None


class AttendanceMarkInput(BaseModel):
    student_user_id: str
    status: AttendanceMarkStatus
    remarks: str | None = Field(default=None, max_length=256)


class AttendanceSubmitPayload(BaseModel):
    marks: list[AttendanceMarkInput] = Field(min_length=1)

    model_config = {"extra": "forbid"}


class AttendanceRecordRead(BaseModel):
    student_user_id: str
    status: AttendanceMarkStatus
    remarks: str | None


class StudentAttendanceSummary(BaseModel):
    student_user_id: str
    total_sessions: int
    percentage: float
    below_threshold: bool


class SubjectAttendanceSummary(BaseModel):
    subject_id: str | None
    course_code: str
    section: str
    average_percentage: float


class AttendanceShortageStudent(BaseModel):
    student_user_id: str
    percentage: float
    min_required: float


class AttendanceCorrectionCreate(BaseModel):
    session_id: str
    student_user_id: str | None = None
    requested_status: AttendanceMarkStatus | None = None
    reason: str = Field(min_length=10, max_length=1000)

    model_config = {"extra": "forbid"}


class AttendanceCorrectionRead(BaseModel):
    id: str
    session_id: str
    status: str
    reason: str
    created_at: datetime
    resolved_at: datetime | None


class AttendanceReportRead(BaseModel):
    course_code: str
    section: str
    policy_min_percentage: float
    student_summaries: list[StudentAttendanceSummary]
    shortages: list[AttendanceShortageStudent]
    generated_at: datetime
