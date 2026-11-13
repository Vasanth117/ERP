"""Student CIA and continuous assessment API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.examinations.enums import AssessmentComponentType
from app.modules.lms.enums import SubmissionStatus
from app.modules.students.assessment_enums import MarkVisibility


class CiaScheduleRead(BaseModel):
    id: str
    title: str
    course_code: str
    assessment_type: str
    scheduled_at: datetime
    source: str


class AssessmentComponentStudentRead(BaseModel):
    assessment_id: str
    component_id: str
    code: str
    name: str
    component_type: AssessmentComponentType
    max_marks: float
    weight_percent: float


class PublishedMarkRead(BaseModel):
    assessment_id: str
    component_id: str
    course_code: str | None = None
    subject_id: str | None = None
    marks_obtained: float
    max_marks: float
    percentage: float
    grade_letter: str | None = None
    published_at: datetime
    visibility: MarkVisibility = MarkVisibility.PUBLISHED


class UnpublishedComponentRead(BaseModel):
    assessment_id: str
    component_id: str
    component_name: str
    course_code: str
    visibility: MarkVisibility


class SubjectInternalMarksRead(BaseModel):
    course_code: str
    subject_id: str | None = None
    components: list[PublishedMarkRead]
    total_obtained: float
    total_max: float
    weighted_percentage: float | None = None


class CiaSummaryRead(BaseModel):
    academic_year_label: str
    semester_label: str
    published_count: int
    unpublished_count: int
    missing_count: int
    subjects: list[SubjectInternalMarksRead]
    unpublished_components: list[UnpublishedComponentRead]


class MarksCorrectionStatusRead(BaseModel):
    id: str
    batch_id: str
    status: str
    reason: str
    created_at: datetime
    resolved_at: datetime | None = None


class CiaHistoryItemRead(BaseModel):
    component_id: str
    assessment_id: str
    marks_obtained: float
    max_marks: float
    status: str
    updated_at: datetime


class AssignmentListRead(BaseModel):
    id: str
    title: str
    course_code: str
    section: str
    deadline_at: datetime
    max_marks: float
    instructions_preview: str


class AssignmentDetailRead(BaseModel):
    id: str
    title: str
    course_code: str
    section: str
    instructions: str
    max_marks: float
    deadline_at: datetime
    academic_year_label: str
    semester_label: str


class QuizScheduleRead(BaseModel):
    id: str
    title: str
    course_code: str
    scheduled_at: datetime
    assessment_type: str = "quiz"


class SubmissionStatusRead(BaseModel):
    assignment_id: str
    status: SubmissionStatus
    submitted_at: datetime | None = None
    file_name: str | None = None
    late: bool = False
    missing: bool = False
    evaluated: bool = False


class ContinuousAssessmentMarkRead(BaseModel):
    assignment_id: str
    course_code: str
    title: str
    marks_awarded: float | None = None
    max_marks: float
    visibility: MarkVisibility
    evaluated_at: datetime | None = None


class FeedbackRead(BaseModel):
    assignment_id: str
    submission_id: str
    feedback: str
    created_at: datetime


class ResubmissionEligibilityRead(BaseModel):
    assignment_id: str
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    max_resubmissions: int = 0
    attempts_used: int = 0


class AssessmentProgressRead(BaseModel):
    assignment_id: str
    course_code: str
    title: str
    submission_status: str
    evaluation_published: bool
    marks_awarded: float | None = None
    pending_evaluation: bool = False
