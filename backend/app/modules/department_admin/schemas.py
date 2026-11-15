"""Department Admin API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.identity_models import DepartmentStatus
from app.modules.department_admin.models import DepartmentProfileChangeStatus


class DepartmentDashboardFilters(BaseModel):
    anchor_date: date | None = None
    date_range: DashboardDateRange = DashboardDateRange.WEEK
    academic_year_label: str | None = None
    semester_label: str | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    section_code: str | None = None


class HeadOfDepartmentSummary(BaseModel):
    user_id: str | None = None
    full_name: str | None = None
    email: str | None = None


class DepartmentOverviewRead(BaseModel):
    department_id: str
    institution_department_id: str
    department_code: str
    department_name: str
    college_name: str
    status: DepartmentStatus
    head_of_department: HeadOfDepartmentSummary | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    programme_count: int = 0
    batch_count: int = 0
    section_count: int = 0
    total_active_students: int = 0
    total_active_faculty: int = 0


class DepartmentStudentStatsRead(BaseModel):
    total_enrolled: int
    active_students: int
    inactive_students: int
    by_programme: list[dict[str, Any]]
    by_batch: list[dict[str, Any]]
    by_section: list[dict[str, Any]]
    new_admissions_count: int | None = None
    follow_up_count: int = 0


class DepartmentFacultyStatsRead(BaseModel):
    total_faculty: int
    active_faculty: int
    on_approved_leave: int
    by_designation: list[dict[str, Any]]
    unassigned_teaching_count: int
    workload_summary_available: bool


class DepartmentAcademicSummaryRead(BaseModel):
    active_programmes: int
    programme_codes: list[str]
    current_academic_year: str | None
    current_semester: str | None
    subjects_offered_count: int | None = None
    curriculum_coverage: float | None = None
    curriculum_coverage_note: str | None = None


class DepartmentAttendanceOverviewRead(BaseModel):
    sessions_submitted: int
    pending_submissions: int
    correction_requests_open: int
    missing_submission_count: int


class DepartmentTimetableOverviewRead(BaseModel):
    today_sessions: list[dict[str, Any]]
    upcoming_sessions: list[dict[str, Any]]
    scheduling_conflicts: int | None = None


class DepartmentExaminationOverviewRead(BaseModel):
    scheduled_examinations: int
    pending_marks_evaluations: int
    upcoming_assessments: int


class DepartmentAlertRead(BaseModel):
    category: str
    title: str
    reference_id: str
    api_reference: str
    severity: str
    occurred_at: datetime


class DepartmentActivityRead(BaseModel):
    activity_type: str
    summary: str
    user_id: str
    occurred_at: datetime


class DepartmentDashboardBundleRead(BaseModel):
    overview: DepartmentOverviewRead
    students: DepartmentStudentStatsRead
    faculty: DepartmentFacultyStatsRead
    academics: DepartmentAcademicSummaryRead
    attendance: DepartmentAttendanceOverviewRead
    timetable: DepartmentTimetableOverviewRead
    examinations: DepartmentExaminationOverviewRead
    alerts: list[DepartmentAlertRead]
    upcoming_events: list[dict[str, Any]]


class DepartmentProfileDetailsRead(BaseModel):
    institution_department_id: str
    department_code: str
    department_name: str
    status: DepartmentStatus
    description: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    office_location: str | None = None
    website_url: str | None = None
    programme_codes: list[str] = Field(default_factory=list)
    head_of_department: HeadOfDepartmentSummary | None = None
    revision: int = 1
    updated_at: datetime | None = None


class DepartmentProfileDetailsUpdate(BaseModel):
    description: str | None = Field(default=None, max_length=2000)
    contact_email: str | None = Field(default=None, max_length=254)
    contact_phone: str | None = Field(default=None, max_length=32)
    office_location: str | None = Field(default=None, max_length=500)
    website_url: str | None = Field(default=None, max_length=500)


class DepartmentProfileChangeRequestCreate(BaseModel):
    field_name: str = Field(min_length=2, max_length=64)
    proposed_value: str = Field(min_length=1, max_length=500)
    idempotency_key: str | None = Field(default=None, max_length=64)


class DepartmentProfileChangeRequestRead(BaseModel):
    request_id: str
    field_name: str
    previous_value: str | None
    proposed_value: str
    status: DepartmentProfileChangeStatus
    requested_by: str
    decided_by: str | None = None
    decided_at: datetime | None = None
    rejection_reason: str | None = None
    created_at: datetime


class DepartmentSettingRead(BaseModel):
    key: str
    value: Any
    category: str
    revision: int
    updated_at: datetime


class DepartmentSettingUpdate(BaseModel):
    value: Any


class DepartmentAcademicConfigVisibilityRead(BaseModel):
    academic_years: list[dict[str, Any]]
    attendance_policy_available: bool
    examination_policies_note: str
    grading_config_note: str
    timetable_rules_note: str


SENSITIVE_PROFILE_FIELDS = frozenset({"name", "department_code", "status", "head_user_id"})


def normalize_profile_field(field_name: str) -> str:
    return field_name.strip().lower()