"""Parent portal phase 2 API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.students.student_schedule_schemas import (
    AttendanceMarkRead,
    AttendanceSemesterSummaryRead,
    AttendanceShortageRead,
    SubjectAttendanceDetailRead,
)


class ParentInstitutionContactRead(BaseModel):
    institution_name: str | None = None
    primary_email: str | None = None
    primary_phone: str | None = None
    website: str | None = None


class ParentStudentProfileRead(BaseModel):
    student_user_id: str
    full_name: str
    student_id: str | None = None
    roll_number: str | None = None
    admission_number: str | None = None
    admission_date: date | None = None
    profile_photo_ref: str | None = None
    programme_code: str | None = None
    programme_name: str | None = None
    department_id: str | None = None
    department_name: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    enrollment_status: str | None = None
    campus_name: str | None = None
    institution_contact: ParentInstitutionContactRead | None = None


class ParentEnrolledCourseRead(BaseModel):
    course_code: str
    course_name: str
    section_code: str
    credit_units: float | None = None
    academic_year_label: str
    semester_label: str


class ParentAcademicProgressRead(BaseModel):
    academic_standing: str | None = None
    progression_status: str | None = None
    cgpa: float | None = None
    credits_registered: float | None = None
    credits_earned: float | None = None
    published_only: bool = True
    notices: list[str] = Field(default_factory=list)


class ParentAcademicOverviewRead(BaseModel):
    profile: ParentStudentProfileRead
    enrolled_courses: list[ParentEnrolledCourseRead] = Field(default_factory=list)
    progress: ParentAcademicProgressRead | None = None


class ParentAcademicHistoryTermRead(BaseModel):
    academic_year_label: str
    semester_label: str
    enrollment_status: str | None = None
    credits_registered: float | None = None
    credits_earned: float | None = None
    cgpa: float | None = None
    summary: dict[str, Any] = Field(default_factory=dict)


class ParentAcademicEnquiryCreate(BaseModel):
    category: str
    description: str = Field(min_length=10, max_length=4000)
    requested_fields: dict[str, Any] = Field(default_factory=dict)


class ParentAcademicEnquiryRead(BaseModel):
    enquiry_id: str
    category: str
    description: str
    status: str
    response_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ParentAttendanceDashboardRead(BaseModel):
    summary: AttendanceSemesterSummaryRead
    present_marks: int = 0
    absent_marks: int = 0
    excused_marks: int = 0
    working_sessions: int = 0
    alerts_pending: int = 0


class ParentAttendanceAlertRead(BaseModel):
    alert_id: str
    severity: str
    title: str
    body: str
    course_code: str | None = None
    percentage: float | None = None
    min_required: float | None = None
    acknowledged: bool
    created_at: datetime
    updated_at: datetime


class ParentAttendanceEnquiryCreate(BaseModel):
    category: str
    course_code: str | None = None
    section: str | None = None
    attendance_date: date | None = None
    period_label: str | None = None
    description: str = Field(min_length=10, max_length=4000)
    supporting_info: dict[str, Any] = Field(default_factory=dict)


class ParentAttendanceEnquiryRead(BaseModel):
    enquiry_id: str
    category: str
    course_code: str | None = None
    section: str | None = None
    attendance_date: date | None = None
    status: str
    response_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ParentEnquiryReview(BaseModel):
    status: str | None = None
    response_notes: str = Field(min_length=3, max_length=4000)
    assigned_team: str | None = None