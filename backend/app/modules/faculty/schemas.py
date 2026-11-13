"""Faculty API schemas."""

from datetime import date, datetime, time
from typing import Any

from beanie import PydanticObjectId
from pydantic import BaseModel, Field

from app.modules.faculty.enums import (
    AssignmentRole,
    AssignmentStatus,
    DashboardDateRange,
    FacultyActivityType,
    FacultyNotificationCategory,
)
from app.modules.faculty.models import (
    FacultyActivityLog,
    FacultyAssignment,
    FacultyNotification,
    FacultyProfile,
    FacultyWorkload,
    ProfileDocumentRef,
    QualificationRecord,
)


class FacultyProfileSummary(BaseModel):
    user_id: str
    full_name: str
    email: str
    employee_id: str | None = None
    faculty_code: str | None = None
    designation: str | None = None
    department_id: str | None = None
    department_name: str | None = None
    specialization: str | None = None


class AcademicTermInfo(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None


class CourseAssignmentSummary(BaseModel):
    course_code: str
    course_name: str
    subject_code: str | None = None
    subject_name: str | None = None
    section: str
    assignment_role: AssignmentRole


class TimetableSlotSummary(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time
    course_code: str
    course_name: str
    section: str
    room: str | None = None


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
    category: FacultyNotificationCategory
    created_at: datetime
    read_at: datetime | None = None


class WorkloadSummary(BaseModel):
    academic_year_label: str
    semester_label: str
    lecture_hours: float
    lab_hours: float
    tutorial_hours: float
    total_hours: float
    credit_units: float
    active_course_count: int


class QuickAction(BaseModel):
    code: str
    label: str
    href: str | None = None
    enabled: bool = True


class FacultyDashboardRead(BaseModel):
    profile: FacultyProfileSummary
    academic_term: AcademicTermInfo
    assigned_courses: list[CourseAssignmentSummary]
    timetable_today: list[TimetableSlotSummary]
    timetable_week: list[TimetableSlotSummary]
    pending_attendance: list[PendingTaskSummary]
    upcoming_assessments: list[PendingTaskSummary]
    pending_evaluations: list[PendingTaskSummary]
    upcoming_deadlines: list[DeadlineSummary]
    notifications: list[NotificationSummary]
    workload: WorkloadSummary | None = None
    recent_activities: list["FacultyActivityRead"]
    upcoming_events: list[PendingTaskSummary]
    quick_actions: list[QuickAction]
    date_filter: DashboardDateRange
    anchor_date: date


class FacultyDashboardStats(BaseModel):
    pending_task_count: int
    upcoming_assessment_count: int
    pending_evaluation_count: int
    unread_notification_count: int
    classes_today: int


class FacultyProfileRead(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: str
    employee_id: str | None = None
    faculty_code: str | None = None
    designation: str | None = None
    department_id: str | None = None
    department_name: str | None = None
    qualifications: list[QualificationRecord]
    specialization: str | None = None
    contact_phone: str | None = None
    office_location: str | None = None
    bio: str | None = None
    document_refs: list[ProfileDocumentRef]
    employment_snapshot: dict[str, Any]
    updated_at: datetime

    @classmethod
    def from_parts(
        cls,
        profile: FacultyProfile,
        *,
        full_name: str,
        email: str,
        department_name: str | None,
    ) -> "FacultyProfileRead":
        return cls(
            id=str(profile.id),
            user_id=str(profile.user_id),
            full_name=full_name,
            email=email,
            employee_id=profile.employee_id,
            faculty_code=profile.faculty_code,
            designation=profile.designation,
            department_id=str(profile.department_id) if profile.department_id else None,
            department_name=department_name,
            qualifications=profile.qualifications,
            specialization=profile.specialization,
            contact_phone=profile.contact_phone,
            office_location=profile.office_location,
            bio=profile.bio,
            document_refs=profile.document_refs,
            employment_snapshot=profile.employment_snapshot,
            updated_at=profile.updated_at,
        )


class FacultyProfileUpdate(BaseModel):
    contact_phone: str | None = Field(default=None, max_length=32)
    office_location: str | None = Field(default=None, max_length=128)
    bio: str | None = Field(default=None, max_length=4000)
    document_refs: list[ProfileDocumentRef] | None = None

    model_config = {"extra": "forbid"}


class TeachingResponsibilityRead(BaseModel):
    id: str
    academic_year_label: str
    semester_label: str
    course_code: str
    course_name: str
    subject_code: str | None = None
    subject_name: str | None = None
    section: str
    assignment_role: AssignmentRole
    status: AssignmentStatus
    effective_from: datetime | None = None
    effective_to: datetime | None = None
    allocation_locked: bool
    updated_at: datetime

    @classmethod
    def from_document(cls, document: FacultyAssignment) -> "TeachingResponsibilityRead":
        return cls(
            id=str(document.id),
            academic_year_label=document.academic_year_label,
            semester_label=document.semester_label,
            course_code=document.course_code,
            course_name=document.course_name,
            subject_code=document.subject_code,
            subject_name=document.subject_name,
            section=document.section,
            assignment_role=document.assignment_role,
            status=document.status,
            effective_from=document.effective_from,
            effective_to=document.effective_to,
            allocation_locked=document.allocation_locked,
            updated_at=document.updated_at,
        )


class FacultyActivityRead(BaseModel):
    id: str
    activity_type: FacultyActivityType
    title: str
    description: str | None = None
    occurred_at: datetime
    source_module: str
    metadata: dict[str, Any]

    @classmethod
    def from_document(cls, document: FacultyActivityLog) -> "FacultyActivityRead":
        return cls(
            id=str(document.id),
            activity_type=document.activity_type,
            title=document.title,
            description=document.description,
            occurred_at=document.occurred_at,
            source_module=document.source_module,
            metadata=document.metadata,
        )


class FacultyNotificationRead(BaseModel):
    id: str
    title: str
    body: str
    category: FacultyNotificationCategory
    created_at: datetime
    read_at: datetime | None = None

    @classmethod
    def from_document(cls, document: FacultyNotification) -> "FacultyNotificationRead":
        return cls(
            id=str(document.id),
            title=document.title,
            body=document.body,
            category=document.category,
            created_at=document.created_at,
            read_at=document.read_at,
        )


FacultyDashboardRead.model_rebuild()


class WorkloadDetailRead(BaseModel):
    workload: WorkloadSummary | None
    assignments: list[TeachingResponsibilityRead]

    @staticmethod
    def workload_from_document(document: FacultyWorkload) -> WorkloadSummary:
        return WorkloadSummary(
            academic_year_label=document.academic_year_label,
            semester_label=document.semester_label,
            lecture_hours=document.lecture_hours,
            lab_hours=document.lab_hours,
            tutorial_hours=document.tutorial_hours,
            total_hours=document.total_hours,
            credit_units=document.credit_units,
            active_course_count=document.active_course_count,
        )
