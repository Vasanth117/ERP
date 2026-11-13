"""Student portal API schemas."""

from datetime import date, datetime, time
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.modules.students.enums import (
    AcademicStanding,
    DashboardDateRange,
    ProgressionStatus,
    StudentAcademicRequestStatus,
    StudentAcademicRequestType,
    StudentActivityType,
    StudentEnrollmentStatus,
    StudentNotificationCategory,
)
from app.modules.students.models import (
    EmergencyContact,
    ProfileDocumentRef,
    StudentAcademicRecord,
    StudentAcademicRequest,
    StudentActivityLog,
    StudentEnrollment,
    StudentEnrollmentHistory,
    StudentProfile,
)


class StudentProfileSummary(BaseModel):
    user_id: str
    full_name: str
    email: str
    student_id: str | None = None
    roll_number: str | None = None
    admission_number: str | None = None
    admission_date: date | None = None
    department_id: str | None = None
    department_name: str | None = None
    programme_code: str | None = None
    programme_name: str | None = None
    batch_label: str | None = None
    section_code: str | None = None


class AcademicTermInfo(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None


class EnrolledCourseSummary(BaseModel):
    course_code: str
    course_name: str | None = None
    section_code: str
    status: str = "active"


class TimetableSlotSummary(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time
    course_code: str
    course_name: str
    section: str
    room: str | None = None


class AttendanceCourseSummary(BaseModel):
    course_code: str
    section: str
    percentage: float | None = None
    sessions_held: int = 0
    min_required: float = 75.0


class AttendanceSummaryRead(BaseModel):
    status: str
    overall_percentage: float | None = None
    min_required: float | None = None
    courses: list[AttendanceCourseSummary] = Field(default_factory=list)


class PendingTaskSummary(BaseModel):
    task_type: str
    title: str
    due_at: datetime | None = None
    reference_id: str | None = None


class DeadlineSummary(BaseModel):
    title: str
    due_at: datetime
    category: str


class NotificationSummary(BaseModel):
    id: str
    title: str
    body: str
    category: StudentNotificationCategory = StudentNotificationCategory.ACADEMIC
    created_at: datetime


class FeeSummaryRead(BaseModel):
    status: str
    outstanding_amount: float | None = None
    currency: str = "INR"
    due_date: date | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class ResultSummary(BaseModel):
    assessment_id: str
    component_id: str
    marks_obtained: float
    max_marks: float
    published_at: datetime


class QuickAction(BaseModel):
    code: str
    label: str
    href: str | None = None
    enabled: bool = True


class StudentDashboardRead(BaseModel):
    profile: StudentProfileSummary
    academic_term: AcademicTermInfo
    enrolled_courses: list[EnrolledCourseSummary]
    attendance: AttendanceSummaryRead
    timetable_today: list[TimetableSlotSummary]
    upcoming_examinations: list[PendingTaskSummary]
    pending_assignments: list[PendingTaskSummary]
    published_results: list[ResultSummary]
    fees: FeeSummaryRead
    notifications: list[NotificationSummary]
    pending_requests: list[PendingTaskSummary]
    deadlines: list[DeadlineSummary]
    quick_actions: list[QuickAction] = Field(default_factory=list)
    preferences: dict[str, Any] = Field(default_factory=dict)


class StudentDashboardStats(BaseModel):
    enrolled_course_count: int
    pending_assignment_count: int
    pending_request_count: int
    attendance_overall_percentage: float | None = None
    unread_notification_count: int = 0


class StudentProfileRead(BaseModel):
    user_id: str
    full_name: str
    email: str
    student_id: str | None = None
    roll_number: str | None = None
    admission_number: str | None = None
    admission_date: date | None = None
    department_id: str | None = None
    department_name: str | None = None
    programme_code: str | None = None
    programme_name: str | None = None
    batch_label: str | None = None
    section_code: str | None = None
    contact_phone: str | None = None
    alternate_email: EmailStr | None = None
    permanent_address: str | None = None
    current_address: str | None = None
    emergency_contacts: list[EmergencyContact] = Field(default_factory=list)
    bio: str | None = None
    profile_photo_ref: str | None = None
    document_refs: list[ProfileDocumentRef] = Field(default_factory=list)
    updated_at: datetime

    @classmethod
    def from_parts(
        cls,
        profile: StudentProfile,
        *,
        full_name: str,
        email: str,
        department_name: str | None,
    ) -> "StudentProfileRead":
        return cls(
            user_id=str(profile.user_id),
            full_name=full_name,
            email=email,
            student_id=profile.student_id,
            roll_number=profile.roll_number,
            admission_number=profile.admission_number,
            admission_date=profile.admission_date,
            department_id=str(profile.department_id) if profile.department_id else None,
            department_name=department_name,
            programme_code=profile.programme_code,
            programme_name=profile.programme_name,
            batch_label=profile.batch_label,
            section_code=profile.section_code,
            contact_phone=profile.contact_phone,
            alternate_email=profile.alternate_email,  # type: ignore[arg-type]
            permanent_address=profile.permanent_address,
            current_address=profile.current_address,
            emergency_contacts=profile.emergency_contacts,
            bio=profile.bio,
            profile_photo_ref=profile.profile_photo_ref,
            document_refs=profile.document_refs,
            updated_at=profile.updated_at,
        )


class StudentProfileUpdate(BaseModel):
    contact_phone: str | None = Field(default=None, max_length=32)
    alternate_email: EmailStr | None = None
    permanent_address: str | None = Field(default=None, max_length=1000)
    current_address: str | None = Field(default=None, max_length=1000)
    emergency_contacts: list[EmergencyContact] | None = None
    bio: str | None = Field(default=None, max_length=2000)
    profile_photo_ref: str | None = Field(default=None, max_length=120)

    model_config = {"extra": "forbid"}


class AdmissionInfoRead(BaseModel):
    student_id: str | None = None
    roll_number: str | None = None
    admission_number: str | None = None
    admission_date: date | None = None
    programme_code: str | None = None
    programme_name: str | None = None
    department_name: str | None = None
    batch_label: str | None = None
    section_code: str | None = None


class EnrollmentStatusRead(BaseModel):
    academic_year_label: str
    semester_label: str
    enrollment_status: StudentEnrollmentStatus
    academic_standing: AcademicStanding
    progression_status: ProgressionStatus


class DepartmentProgrammeRead(BaseModel):
    department_id: str | None = None
    department_name: str | None = None
    programme_code: str | None = None
    programme_name: str | None = None
    batch_label: str | None = None
    section_code: str | None = None


class EnrollmentLineRead(BaseModel):
    course_code: str
    course_name: str
    section_code: str
    status: StudentEnrollmentStatus
    academic_year_label: str
    semester_label: str


class EnrollmentHistoryRead(BaseModel):
    id: str
    academic_year_label: str
    semester_label: str
    programme_code: str | None = None
    section_code: str | None = None
    courses: list[dict[str, str]]
    final_standing: AcademicStanding
    credits_earned: float
    cgpa: float | None = None
    closed_at: datetime


class AcademicEligibilityRead(BaseModel):
    promotion_eligible: bool | None = None
    eligibility_summary: dict[str, Any] = Field(default_factory=dict)
    credits_registered: float = 0
    credits_earned: float = 0
    cgpa: float | None = None


class AcademicDetailsRead(BaseModel):
    admission: AdmissionInfoRead
    enrollment_status: EnrollmentStatusRead
    department_programme: DepartmentProgrammeRead
    current_enrollments: list[EnrollmentLineRead]
    academic_record: AcademicEligibilityRead | None = None


class EnrollmentRequestCreate(BaseModel):
    request_type: StudentAcademicRequestType
    title: str = Field(max_length=200)
    description: str = Field(min_length=10, max_length=4000)
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class EnrollmentRequestRead(BaseModel):
    id: str
    request_type: StudentAcademicRequestType
    title: str
    description: str
    status: StudentAcademicRequestStatus
    academic_year_label: str
    semester_label: str
    reviewer_note: str | None = None
    submitted_at: datetime
    resolved_at: datetime | None = None


class StudentActivityRead(BaseModel):
    id: str
    activity_type: StudentActivityType
    title: str
    description: str | None = None
    created_at: datetime

    @classmethod
    def from_document(cls, row: StudentActivityLog) -> "StudentActivityRead":
        return cls(
            id=str(row.id),
            activity_type=row.activity_type,
            title=row.title,
            description=row.description,
            created_at=row.created_at,
        )


def enrollment_line_from_doc(row: StudentEnrollment) -> EnrollmentLineRead:
    return EnrollmentLineRead(
        course_code=row.course_code,
        course_name=row.course_name,
        section_code=row.section_code,
        status=row.status,
        academic_year_label=row.academic_year_label,
        semester_label=row.semester_label,
    )


def enrollment_history_from_doc(row: StudentEnrollmentHistory) -> EnrollmentHistoryRead:
    return EnrollmentHistoryRead(
        id=str(row.id),
        academic_year_label=row.academic_year_label,
        semester_label=row.semester_label,
        programme_code=row.programme_code,
        section_code=row.section_code,
        courses=row.courses,
        final_standing=row.final_standing,
        credits_earned=row.credits_earned,
        cgpa=row.cgpa,
        closed_at=row.closed_at,
    )


def request_from_doc(row: StudentAcademicRequest) -> EnrollmentRequestRead:
    return EnrollmentRequestRead(
        id=str(row.id),
        request_type=row.request_type,
        title=row.title,
        description=row.description,
        status=row.status,
        academic_year_label=row.academic_year_label,
        semester_label=row.semester_label,
        reviewer_note=row.reviewer_note,
        submitted_at=row.submitted_at,
        resolved_at=row.resolved_at,
    )


def enrollment_status_from_record(
    record: StudentAcademicRecord | None,
    *,
    year: str,
    semester: str,
) -> EnrollmentStatusRead:
    if record is None:
        return EnrollmentStatusRead(
            academic_year_label=year,
            semester_label=semester,
            enrollment_status=StudentEnrollmentStatus.PROVISIONAL,
            academic_standing=AcademicStanding.UNKNOWN,
            progression_status=ProgressionStatus.PENDING,
        )
    return EnrollmentStatusRead(
        academic_year_label=record.academic_year_label,
        semester_label=record.semester_label,
        enrollment_status=record.enrollment_status,
        academic_standing=record.academic_standing,
        progression_status=record.progression_status,
    )
