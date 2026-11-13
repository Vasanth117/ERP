"""Grade, GPA, and credit API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.students.enums import AcademicStanding


class SubjectGradeRead(BaseModel):
    season_id: str
    course_code: str
    course_name: str | None = None
    grade_letter: str | None = None
    grade_points: float | None = None
    credit_units: float | None = None
    pass_fail: str | None = None
    published_at: datetime | None = None
    grading_policy_version: str | None = None


class SemesterGpaRead(BaseModel):
    season_id: str
    academic_year_label: str
    semester_label: str
    gpa: float | None = None
    credits_attempted: float = 0
    credits_earned: float = 0
    official_gpa: float | None = None
    grading_policy_version: str | None = None


class CgpaRead(BaseModel):
    cgpa: float | None = None
    credits_earned: float = 0
    credits_required: float | None = None
    credits_pending: float | None = None
    grading_policy_version: str | None = None


class SemesterPerformanceRead(BaseModel):
    season_id: str
    academic_year_label: str
    semester_label: str
    gpa: float | None = None
    overall_pass: bool | None = None
    published_at: datetime | None = None


class GradeHistoryItemRead(BaseModel):
    season_id: str
    course_code: str
    grade_letter: str | None = None
    grade_points: float | None = None
    attempt_number: int = 1
    published_at: datetime | None = None


class CreditSummaryRead(BaseModel):
    credits_earned: float = 0
    credits_registered: float = 0
    credits_pending: float | None = None
    credits_required: float | None = None
    completion_percentage: float | None = None


class AcademicStandingRead(BaseModel):
    standing: AcademicStanding
    programme_code: str | None = None
    promotion_eligible: bool | None = None
    probation: bool = False
    source: str = "student_academic_record"


class GpaCalculationBreakdownRead(BaseModel):
    season_id: str | None = None
    lines: list[dict] = Field(default_factory=list)
    semester_gpa: float | None = None
    cgpa: float | None = None
    grading_policy_version: str | None = None
    rounding: str = "half_up_2dp"
