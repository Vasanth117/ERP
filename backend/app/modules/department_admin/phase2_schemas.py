"""Department Admin phase 2 request/response schemas."""

from datetime import date, datetime
from typing import Any

from typing import Literal

from pydantic import BaseModel, Field

from app.modules.college_admin.academic_config_models import ConfigPublicationStatus
from app.modules.department_admin.models import DepartmentRequestStatus
from app.modules.faculty.enums import AssignmentRole, AssignmentStatus
from app.modules.faculty.models import QualificationRecord


class FacultyDirectoryFilters(BaseModel):
    designation: str | None = None
    employment_status: str | None = None
    programme_code: str | None = None
    subject_code: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    search: str | None = Field(default=None, max_length=120)


class FacultyDirectoryItem(BaseModel):
    faculty_user_id: str
    full_name: str
    email: str
    employee_id: str | None = None
    faculty_code: str | None = None
    designation: str | None = None
    employment_status: str | None = None
    department_id: str | None = None
    specialization: str | None = None
    assigned_subjects: list[str] = Field(default_factory=list)
    assigned_sections: list[str] = Field(default_factory=list)
    workload_total_hours: float | None = None


class FacultyProfileDetailRead(BaseModel):
    faculty_user_id: str
    full_name: str
    email: str
    employee_id: str | None = None
    faculty_code: str | None = None
    designation: str | None = None
    department_id: str | None = None
    qualifications: list[QualificationRecord] = Field(default_factory=list)
    specialization: str | None = None
    contact_phone: str | None = None
    office_location: str | None = None
    bio: str | None = None
    assignments: list[dict[str, Any]] = Field(default_factory=list)
    workload: dict[str, Any] | None = None
    approved_leave_count: int = 0


class FacultyAvailabilityRead(BaseModel):
    faculty_user_id: str
    has_timetable_data: bool
    scheduled_sessions_today: int
    on_approved_leave: bool
    availability_note: str


class FacultyWorkloadRead(BaseModel):
    faculty_user_id: str
    academic_year_label: str
    semester_label: str
    lecture_hours: float = 0
    lab_hours: float = 0
    tutorial_hours: float = 0
    total_hours: float = 0
    credit_units: float = 0
    active_course_count: int = 0
    institutional_max_hours: float | None = None
    exceeds_limit: bool | None = None


class TeachingAssignmentCreate(BaseModel):
    faculty_user_id: str
    academic_year_label: str = Field(min_length=2, max_length=32)
    semester_label: str = Field(min_length=2, max_length=32)
    course_code: str = Field(min_length=2, max_length=32)
    course_name: str = Field(min_length=2, max_length=200)
    course_id: str | None = None
    subject_code: str | None = None
    subject_name: str | None = None
    section: str = Field(min_length=1, max_length=16)
    assignment_role: AssignmentRole = AssignmentRole.PRIMARY
    idempotency_key: str | None = Field(default=None, max_length=64)


class TeachingAssignmentUpdate(BaseModel):
    status: AssignmentStatus | None = None
    section: str | None = Field(default=None, max_length=16)
    change_note: str | None = Field(default=None, max_length=500)


class TeachingAssignmentRead(BaseModel):
    assignment_id: str
    faculty_user_id: str
    academic_year_label: str
    semester_label: str
    course_code: str
    course_name: str
    section: str
    assignment_role: AssignmentRole
    status: AssignmentStatus
    updated_at: datetime


class UnassignedSubjectItem(BaseModel):
    course_code: str
    course_name: str
    academic_year_label: str | None
    semester_label: str | None


class SubstituteRequestCreate(BaseModel):
    original_faculty_user_id: str
    substitute_faculty_user_id: str | None = None
    course_code: str
    section: str
    academic_year_label: str
    semester_label: str
    session_date: date | None = None
    reason: str = Field(min_length=3, max_length=1000)
    idempotency_key: str | None = Field(default=None, max_length=64)


class SubstituteRequestRead(BaseModel):
    request_id: str
    original_faculty_user_id: str
    substitute_faculty_user_id: str | None
    course_code: str
    section: str
    academic_year_label: str
    semester_label: str
    session_date: date | None
    reason: str
    status: DepartmentRequestStatus
    created_at: datetime


class FacultyAssignmentRequestCreate(BaseModel):
    faculty_user_id: str
    request_type: Literal["assign", "transfer"]
    target_department_id: str | None = None
    note: str | None = Field(default=None, max_length=1000)
    idempotency_key: str | None = Field(default=None, max_length=64)


class ProgrammeRead(BaseModel):
    programme_id: str
    programme_code: str
    name: str
    department_id: str | None
    duration_semesters: int
    status: ConfigPublicationStatus
    is_active: bool


class ProgrammeCreate(BaseModel):
    programme_code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=2, max_length=200)
    duration_semesters: int = Field(default=8, ge=1, le=20)
    credits_required: float = Field(default=160, ge=0)


class ProgrammeUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    duration_semesters: int | None = Field(default=None, ge=1, le=20)
    credits_required: float | None = Field(default=None, ge=0)


class CurriculumRead(BaseModel):
    curriculum_id: str
    course_id: str
    academic_year_label: str
    semester_label: str
    version: str
    approved: bool
    locked: bool


class SubjectRead(BaseModel):
    subject_id: str
    subject_code: str
    name: str
    course_code: str | None = None


class CourseOfferingRead(BaseModel):
    offering_id: str
    section_id: str
    course_code: str
    section_code: str
    batch_label: str | None
    academic_year_label: str
    semester_label: str


class CourseOfferingRequestCreate(BaseModel):
    programme_code: str
    course_id: str
    course_code: str
    section_code: str
    batch_label: str | None = None
    academic_year_label: str
    semester_label: str
    faculty_user_id: str | None = None
    idempotency_key: str | None = Field(default=None, max_length=64)


class CurriculumCoverageItem(BaseModel):
    course_code: str
    section: str
    faculty_user_id: str
    percent_complete: float
    coverage_available: bool = True


class AcademicProgressionSummary(BaseModel):
    batch_label: str | None
    student_count: int
    probation_or_suspended_count: int
    note: str | None = None