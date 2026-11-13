"""Faculty LMS API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.lms.enums import LmsAssignmentStatus, MaterialPublishState, SubmissionStatus


class LearningMaterialRead(BaseModel):
    id: str
    title: str
    course_code: str
    section: str | None
    subject_id: str | None
    unit_no: int | None
    file_id: str
    file_name: str
    mime_type: str
    size_bytes: int
    publish_state: MaterialPublishState


class LearningMaterialUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    publish_state: MaterialPublishState | None = None
    unit_no: int | None = Field(default=None, ge=1)

    model_config = {"extra": "forbid"}


class AssignmentRuleInput(BaseModel):
    allowed_extensions: list[str] | None = None
    max_file_size_bytes: int | None = Field(default=None, ge=1)
    late_submission_allowed: bool | None = None
    late_penalty_percent: float | None = Field(default=None, ge=0, le=100)
    resubmission_allowed: bool | None = None
    max_resubmissions: int | None = Field(default=None, ge=0)


class LmsAssignmentCreate(BaseModel):
    course_code: str
    section: str
    title: str = Field(max_length=200)
    instructions: str = Field(max_length=8000)
    max_marks: float = Field(ge=0)
    deadline_at: datetime
    subject_id: str | None = None
    rules: AssignmentRuleInput | None = None

    model_config = {"extra": "forbid"}


class LmsAssignmentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    instructions: str | None = Field(default=None, max_length=8000)
    max_marks: float | None = Field(default=None, ge=0)
    deadline_at: datetime | None = None

    model_config = {"extra": "forbid"}


class LmsAssignmentRead(BaseModel):
    id: str
    course_code: str
    section: str
    title: str
    instructions: str
    max_marks: float
    deadline_at: datetime
    status: LmsAssignmentStatus
    subject_id: str | None


class SubmissionRead(BaseModel):
    id: str
    student_user_id: str
    status: SubmissionStatus
    submitted_at: datetime | None
    attempt_no: int
    file_name: str | None


class EvaluationCreate(BaseModel):
    marks_awarded: float = Field(ge=0)
    feedback: str | None = Field(default=None, max_length=4000)

    model_config = {"extra": "forbid"}


class EvaluationRead(BaseModel):
    submission_id: str
    marks_awarded: float
    feedback: str | None
    evaluated_at: datetime


class ResubmissionAuthorize(BaseModel):
    student_user_id: str
    reason: str | None = Field(default=None, max_length=500)

    model_config = {"extra": "forbid"}
