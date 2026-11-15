"""Department Admin phase 5.1 — assessment schedule and marks monitoring."""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.examinations.enums import AssessmentComponentType, MarksBatchStatus


class AssessmentMonitoringFilters(BaseModel):
    academic_year_label: str | None = Field(default=None, max_length=32)
    semester_label: str | None = Field(default=None, max_length=32)
    programme_code: str | None = Field(default=None, max_length=32)
    batch_label: str | None = Field(default=None, max_length=64)
    section_code: str | None = Field(default=None, max_length=16)
    course_code: str | None = Field(default=None, max_length=32)
    assessment_type: str | None = Field(default=None, max_length=32)
    faculty_user_id: str | None = None
    assessment_id: str | None = Field(default=None, max_length=64)
    date_from: datetime | None = None
    date_to: datetime | None = None

    @field_validator("date_to")
    @classmethod
    def validate_range(cls, date_to: datetime | None, info) -> datetime | None:
        date_from = info.data.get("date_from")
        if date_from and date_to and date_from > date_to:
            raise ValueError("date_from must be on or before date_to")
        return date_to


class AssessmentSummaryRead(BaseModel):
    assessment_id: str
    title: str
    course_code: str
    section: str
    faculty_user_id: str
    academic_year_label: str
    semester_label: str
    programme_code: str | None = None
    batch_label: str | None = None
    completion_state: str
    marks_batch_summary: dict[str, int] = Field(default_factory=dict)


class AssessmentScheduleItemRead(BaseModel):
    source: str = Field(description="upcoming_assessment|assignment|pending_evaluation")
    assessment_id: str | None = None
    title: str
    course_code: str
    section: str | None = None
    assessment_type: str | None = None
    scheduled_at: datetime | None = None
    submission_deadline: datetime | None = None
    deadline_basis: str = "not_configured"
    faculty_user_id: str | None = None
    status: str | None = None
    programme_code: str | None = None
    batch_label: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None


class AssessmentCompletionRowRead(BaseModel):
    assessment_id: str
    course_code: str
    section: str
    faculty_user_id: str
    component_id: str
    component_code: str
    component_type: AssessmentComponentType
    batch_status: MarksBatchStatus | None = None
    batch_id: str | None = None
    submitted_at: datetime | None = None
    submission_deadline: datetime | None = None
    overdue: bool | None = None
    completion_state: str


class FacultyMarksSubmissionRead(BaseModel):
    faculty_user_id: str
    faculty_name: str | None = None
    batch_counts: dict[str, int]
    pending_assignments: int = 0
    overdue_batches: int = 0


class SubjectMarksSubmissionRead(BaseModel):
    course_code: str
    batch_counts: dict[str, int]
    pending_components: int = 0


class BatchMarksSubmissionRead(BaseModel):
    batch_label: str
    batch_counts: dict[str, int]
    pending_components: int = 0


class MarksSubmissionOverviewRead(BaseModel):
    academic_year_label: str | None
    semester_label: str | None
    totals: dict[str, int]
    by_faculty: list[FacultyMarksSubmissionRead]
    by_subject: list[SubjectMarksSubmissionRead]
    by_batch: list[BatchMarksSubmissionRead]
    marks_detail_visible: bool = False


class StudentSubmissionStatusRead(BaseModel):
    student_user_id: str
    roll_number: str | None = None
    display_name: str | None = None
    submission_status: str
    marks_obtained: float | None = None
    max_marks: float | None = None
    grade_letter: str | None = None


class ExaminationScheduleItemRead(BaseModel):
    source: str
    course_code: str
    section: str | None = None
    exam_type: str | None = None
    title: str
    scheduled_at: datetime | None = None
    scheduled_end: datetime | None = None
    room: str | None = None
    centre_code: str | None = None
    faculty_user_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    season_id: str | None = None
    session_code: str | None = None
    examination_session_code: str | None = None
    published: bool | None = None


class ExaminationReadinessRead(BaseModel):
    course_code: str
    section: str | None = None
    season_id: str | None = None
    indicators: list[dict]
    all_required_met: bool
    readiness_type: str
    formal_approval_authority: str


class ExaminationPendingTaskRead(BaseModel):
    task_type: str
    title: str
    reference_id: str
    course_code: str | None = None
    section: str | None = None
    faculty_user_id: str | None = None
    due_at: datetime | None = None
    status: str | None = None
    severity: str | None = None


class CoordinationIssueReferences(BaseModel):
    course_code: str | None = None
    assessment_id: str | None = None
    faculty_user_id: str | None = None
    season_id: str | None = None
    session_code: str | None = None


class CoordinationIssueCreate(BaseModel):
    issue_type: str = Field(min_length=2, max_length=64)
    severity: str = Field(default="warning", max_length=16)
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=2, max_length=2000)
    references: CoordinationIssueReferences = Field(default_factory=CoordinationIssueReferences)
    assigned_faculty_user_id: str | None = None
    due_date: date | None = None
    idempotency_key: str | None = Field(default=None, max_length=128)


class CoordinationIssueUpdate(BaseModel):
    status: str | None = None
    resolution_notes: str | None = Field(default=None, max_length=2000)
    assigned_faculty_user_id: str | None = None
    due_date: date | None = None


class CoordinationIssueRead(BaseModel):
    issue_id: str
    issue_type: str
    severity: str
    title: str
    description: str
    references: dict
    assigned_faculty_user_id: str | None = None
    due_date: date | None = None
    status: str
    resolution_notes: str | None = None
    created_by: str
    created_at: datetime
    updated_at: datetime


class CoordinationReminderRead(BaseModel):
    event_id: str
    status: str