"""Examination cell dashboard schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType


class ExamDashboardFilters(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None
    exam_session_id: str | None = None
    session_code: str | None = None
    department_code: str | None = None
    course_code: str | None = None
    examination_status: ExamSessionStatus | None = None
    examination_type: ExamSessionType | None = None


class ExamSessionCountSummary(BaseModel):
    total: int
    upcoming: int
    ongoing: int
    completed: int


class ExamRegistrationSummary(BaseModel):
    total_registered_candidates: int
    pending_registrations: int
    pending_eligibility_checks: int


class ExamHallTicketSummary(BaseModel):
    generated: int
    pending: int


class ExamMarksSummary(BaseModel):
    assessments_total: int
    marks_batches_pending_submission: int
    marks_batches_pending_approval: int
    marks_entry_completed: int


class ExamResultsSummary(BaseModel):
    awaiting_review: int
    awaiting_publication: int


class ExamSupplementaryRevaluationSummary(BaseModel):
    revaluation_windows_open: int
    supplementary_seasons: int
    pending_review_fee_payments: int


class ExamIncidentSummary(BaseModel):
    open_coordination_issues: int
    malpractice_related_issues: int


class ExamTimetableItem(BaseModel):
    session_code: str
    course_code: str
    scheduled_start: datetime
    centre_code: str | None = None
    room: str | None = None
    season_id: str | None = None


class ExamActivityItem(BaseModel):
    event_id: str
    action: str
    summary: str
    exam_session_id: str | None = None
    actor_id: str | None = None
    created_at: datetime


class ExamSessionStatRow(BaseModel):
    session_code: str
    session_id: str
    name: str
    status: ExamSessionStatus
    registered_candidates: int
    pending_eligibility: int
    hall_tickets_published: int


class ExamDepartmentStatRow(BaseModel):
    department_code: str
    exam_sessions: int
    registered_candidates: int
    pending_registrations: int


class ExamDashboardOverview(BaseModel):
    filters: ExamDashboardFilters
    sessions: ExamSessionCountSummary
    registration: ExamRegistrationSummary
    hall_tickets: ExamHallTicketSummary
    marks: ExamMarksSummary
    results: ExamResultsSummary
    supplementary_revaluation: ExamSupplementaryRevaluationSummary
    incidents: ExamIncidentSummary
    upcoming_timetable: list[ExamTimetableItem] = Field(default_factory=list)
    recent_activities: list[ExamActivityItem] = Field(default_factory=list)
    session_statistics: list[ExamSessionStatRow] = Field(default_factory=list)
    department_statistics: list[ExamDepartmentStatRow] = Field(default_factory=list)