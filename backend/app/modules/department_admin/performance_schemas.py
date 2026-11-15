"""Department Admin phase 5 — academic performance monitoring schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.students.enums import AcademicStanding, ProgressionStatus


class PerformanceFilters(BaseModel):
    academic_year_label: str | None = Field(default=None, max_length=32)
    semester_label: str | None = Field(default=None, max_length=32)
    season_id: str | None = Field(default=None, max_length=64)
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    section_code: str | None = Field(default=None, max_length=16)
    course_code: str | None = Field(default=None, max_length=32)


class PerformanceMeta(BaseModel):
    academic_year_label: str | None = None
    semester_label: str | None = None
    season_id: str | None = None
    calculation_basis: str
    included_student_count: int = 0
    excluded_reason_counts: dict[str, int] = Field(default_factory=dict)


class PerformanceOverviewRead(BaseModel):
    meta: PerformanceMeta
    enrolled_students: int
    students_with_published_results: int
    result_pending_count: int
    result_withheld_count: int
    pass_count: int
    fail_count: int
    pass_percentage: float | None = None
    unknown_outcome_count: int = 0


class ProgrammePerformanceRead(BaseModel):
    programme_code: str
    enrolled_students: int
    pass_count: int
    fail_count: int
    result_pending_count: int
    pass_percentage: float | None = None


class BatchPerformanceRead(BaseModel):
    batch_label: str
    enrolled_students: int
    pass_count: int
    fail_count: int
    pass_percentage: float | None = None


class SubjectPerformanceRead(BaseModel):
    course_code: str
    enrolled_students: int
    results_published: int
    pass_count: int
    fail_count: int
    result_pending_count: int
    pass_percentage: float | None = None


class PassFailSummaryRead(BaseModel):
    meta: PerformanceMeta
    assessed_students: int
    passed_students: int
    failed_students: int
    result_pending_students: int
    result_withheld_students: int
    pass_percentage: float | None = None


class ArrearStudentRead(BaseModel):
    student_user_id: str
    roll_number: str | None = None
    programme_code: str | None = None
    course_code: str
    season_id: str | None = None
    attempt_number: int | None = None
    source_collection: str


class ArrearSummaryRead(BaseModel):
    meta: PerformanceMeta
    arrear_line_count: int
    unique_students: int
    items: list[ArrearStudentRead]


class ProgressionStudentRead(BaseModel):
    student_user_id: str
    roll_number: str | None = None
    programme_code: str | None = None
    academic_year_label: str
    semester_label: str
    progression_status: ProgressionStatus
    academic_standing: AcademicStanding
    credits_registered: float
    credits_earned: float
    cgpa: float | None = None
    promotion_eligible: bool | None = None


class SupportFlagRead(BaseModel):
    reason_code: str
    source_collection: str
    detail: str | None = None


class StudentSupportRead(BaseModel):
    student_user_id: str
    roll_number: str | None = None
    display_name: str | None = None
    programme_code: str | None = None
    flags: list[SupportFlagRead]


class StudentsRequiringSupportRead(BaseModel):
    meta: PerformanceMeta
    enabled_indicators: list[str]
    students: list[StudentSupportRead]


class TrendPeriodRead(BaseModel):
    period_label: str
    data_available: bool
    pass_count: int = 0
    fail_count: int = 0
    pass_percentage: float | None = None
    enrolled_students: int = 0


class PerformanceTrendsRead(BaseModel):
    meta: PerformanceMeta
    periods: list[TrendPeriodRead]


class PerformanceFollowUpRead(BaseModel):
    follow_up_id: str
    student_user_id: str
    category: str
    description: str
    status: str
    due_date: date | None
    created_at: datetime