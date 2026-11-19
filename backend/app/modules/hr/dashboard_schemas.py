"""HR dashboard response schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrDashboardDateRange


class HrDashboardFilters(BaseModel):
    department_id: str | None = None
    campus_id: str | None = None
    anchor_date: date
    date_range: HrDashboardDateRange
    date_from: date
    date_to: date


class CountGroupItem(BaseModel):
    key: str
    label: str | None = None
    count: int = 0


class EmployeeOverviewStats(BaseModel):
    total: int = 0
    active: int = 0
    inactive: int = 0
    probation: int = 0
    awaiting_confirmation: int = 0
    notice_period: int = 0
    resigned: int = 0
    terminated: int = 0
    recently_joined: int = 0
    by_department: list[CountGroupItem] = Field(default_factory=list)
    by_designation: list[CountGroupItem] = Field(default_factory=list)
    by_employment_type: list[CountGroupItem] = Field(default_factory=list)
    by_campus: list[CountGroupItem] = Field(default_factory=list)


class AttendanceOverviewStats(BaseModel):
    present_today: int = 0
    absent_today: int = 0
    on_leave_today: int = 0
    late_today: int = 0
    early_departure_today: int = 0
    missing_today: int = 0
    pending_corrections: int = 0


class LeaveOverviewStats(BaseModel):
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    currently_on_leave: int = 0
    upcoming_approved: int = 0
    by_leave_type: list[CountGroupItem] = Field(default_factory=list)
    by_department: list[CountGroupItem] = Field(default_factory=list)


class RecruitmentOverviewStats(BaseModel):
    active_openings: int = 0
    total_applicants: int = 0
    new_applications: int = 0
    under_review: int = 0
    interviews_scheduled: int = 0
    awaiting_feedback: int = 0
    selected: int = 0
    rejected: int = 0
    awaiting_offer_acceptance: int = 0


class OnboardingOverviewStats(BaseModel):
    in_progress: int = 0
    pending_tasks: int = 0
    overdue_tasks: int = 0
    awaiting_documents: int = 0
    awaiting_verification: int = 0
    completed: int = 0


class PayrollOverviewStats(BaseModel):
    current_period_label: str | None = None
    configuration_count: int = 0
    last_run_status: str | None = None
    employees_in_payroll_scope: int = 0
    incomplete_salary_profiles: int = 0
    pending_approvals: int = 0
    completed_periods: int = 0
    held_or_failed_records: int = 0


class HrAlertItem(BaseModel):
    code: str
    severity: str = "info"
    message: str
    count: int = 0
    employee_user_id: str | None = None


class HrActivityItem(BaseModel):
    activity_id: str
    activity_type: str
    summary: str
    employee_user_id: str | None = None
    department_id: str | None = None
    status_label: str | None = None
    created_at: datetime


class HrDashboardOverview(BaseModel):
    filters: HrDashboardFilters
    employees: EmployeeOverviewStats
    attendance: AttendanceOverviewStats
    leave: LeaveOverviewStats
    recruitment: RecruitmentOverviewStats
    onboarding: OnboardingOverviewStats
    payroll: PayrollOverviewStats
    alerts: list[HrAlertItem] = Field(default_factory=list)
    recent_activities: list[HrActivityItem] = Field(default_factory=list)


class DashboardEmployeeListItem(BaseModel):
    user_id: str
    employee_code: str | None
    full_name: str | None
    department_id: str | None
    designation: str | None
    employment_status: str | None
    detail: dict = Field(default_factory=dict)