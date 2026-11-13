"""Faculty assessment API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.examinations.enums import AssessmentComponentType, MarksBatchStatus


class AssignedAssessmentRead(BaseModel):
    assessment_id: str
    title: str
    course_code: str
    section: str
    subject_id: str | None


class AssessmentComponentRead(BaseModel):
    component_id: str
    code: str
    name: str
    component_type: AssessmentComponentType
    max_marks: float
    weight_percent: float
    faculty_may_enter: bool
    is_official_final: bool


class EligibleStudentRead(BaseModel):
    student_user_id: str
    roll_number: str
    display_name: str


class MarkEntryItem(BaseModel):
    student_user_id: str
    marks_obtained: float = Field(ge=0)


class MarksDraftSave(BaseModel):
    assessment_id: str
    component_id: str
    course_code: str
    section: str
    entries: list[MarkEntryItem] = Field(min_length=1)

    model_config = {"extra": "forbid"}


class MarksSubmitRequest(BaseModel):
    batch_id: str
    submit_for_approval: bool = True

    model_config = {"extra": "forbid"}


class MarksBatchRead(BaseModel):
    id: str
    assessment_id: str
    component_id: str
    course_code: str
    section: str
    status: MarksBatchStatus
    submitted_at: datetime | None


class StudentMarkRead(BaseModel):
    student_user_id: str
    marks_obtained: float
    max_marks: float
    status: str
    grade_letter: str | None = None


class MarksCorrectionCreate(BaseModel):
    batch_id: str
    student_user_id: str | None = None
    requested_marks: float | None = Field(default=None, ge=0)
    reason: str = Field(min_length=10, max_length=1000)

    model_config = {"extra": "forbid"}


class MarksCorrectionRead(BaseModel):
    id: str
    batch_id: str
    status: str
    reason: str
    created_at: datetime
    resolved_at: datetime | None


class ApprovalHistoryRead(BaseModel):
    action: str
    note: str | None
    created_at: datetime


class AssessmentReportRead(BaseModel):
    course_code: str
    section: str
    assessment_id: str
    component_id: str
    entries: list[StudentMarkRead]
    generated_at: datetime
