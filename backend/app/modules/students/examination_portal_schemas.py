"""Student practical and semester examination API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.examinations.enums import AssessmentComponentType, ExaminationEligibilityStatus


class LaboratorySubjectRead(BaseModel):
    course_id: str | None = None
    course_code: str
    course_name: str | None = None
    section: str
    laboratory: str | None = None
    weekly_sessions: int = 0


class PracticalScheduleRead(BaseModel):
    id: str
    title: str
    course_code: str
    section: str | None = None
    exam_type: str
    scheduled_at: datetime
    scheduled_end: datetime | None = None
    room: str | None = None
    laboratory: str | None = None
    source: str


class PracticalComponentRead(BaseModel):
    assessment_id: str
    component_id: str
    course_code: str
    code: str
    name: str
    component_type: AssessmentComponentType
    max_marks: float
    weight_percent: float


class PracticalMarkRead(BaseModel):
    assessment_id: str
    component_id: str
    course_code: str
    component_name: str | None = None
    marks_obtained: float
    max_marks: float
    percentage: float | None = None
    grade_letter: str | None = None
    published_at: datetime
    visibility: str = "published"


class UnpublishedPracticalMarkRead(BaseModel):
    assessment_id: str
    component_id: str
    course_code: str
    component_name: str
    visibility: str


class ModelExamScheduleRead(BaseModel):
    id: str
    title: str
    course_code: str
    section: str | None = None
    scheduled_at: datetime
    room: str | None = None
    centre_name: str | None = None


class ModelExamMarkRead(BaseModel):
    assessment_id: str
    component_id: str
    course_code: str
    marks_obtained: float
    max_marks: float
    percentage: float | None = None
    published_at: datetime


class PracticalFeedbackRead(BaseModel):
    assessment_id: str
    component_id: str
    course_code: str
    feedback: str | None = None
    published_at: datetime | None = None


class LaboratoryAttendanceRead(BaseModel):
    course_code: str
    section: str
    percentage: float | None = None
    sessions_held: int
    sessions_recorded: int
    authorized: bool = True


class PracticalExamHistoryItemRead(BaseModel):
    component_id: str
    assessment_id: str
    course_code: str
    marks_obtained: float
    max_marks: float
    status: str
    updated_at: datetime


class MarksCorrectionStudentRead(BaseModel):
    id: str
    batch_id: str
    status: str
    reason: str
    created_at: datetime
    resolved_at: datetime | None = None


class SemesterExamSeasonRead(BaseModel):
    season_id: str
    title: str
    academic_year_label: str
    semester_label: str
    starts_at: datetime
    ends_at: datetime


class SemesterExamSessionRead(BaseModel):
    session_code: str
    season_id: str
    course_code: str
    course_name: str | None = None
    section: str | None = None
    paper_code: str | None = None
    scheduled_start: datetime
    scheduled_end: datetime | None = None
    centre_code: str | None = None
    room: str | None = None
    instructions: str | None = None


class ExaminationCentreRead(BaseModel):
    centre_code: str
    name: str
    building: str | None = None
    address: str | None = None
    contact_phone: str | None = None
    room_labels: list[str] = Field(default_factory=list)


class ExaminationInstructionsRead(BaseModel):
    session_code: str | None = None
    course_code: str | None = None
    instructions: str
    source: str


class ExaminationEligibilityRead(BaseModel):
    season_id: str
    status: ExaminationEligibilityStatus
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    attendance_cleared: bool | None = None
    fee_cleared: bool | None = None
    published_at: datetime | None = None


class ExaminationRegulationRead(BaseModel):
    regulation_id: str
    season_id: str | None = None
    title: str
    version: str
    body: str
    published_at: datetime | None = None


class ExaminationAnnouncementRead(BaseModel):
    announcement_id: str
    season_id: str | None = None
    title: str
    body: str
    published_at: datetime | None = None
    expires_at: datetime | None = None


class ExaminationScheduleChangeRead(BaseModel):
    id: str
    season_id: str | None = None
    session_code: str | None = None
    course_code: str | None = None
    change_type: str
    summary: str
    effective_at: datetime


class ExaminationCalendarEventRead(BaseModel):
    event_id: str
    title: str
    event_at: datetime
    event_type: str
    course_code: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExaminationHistoryItemRead(BaseModel):
    season_id: str
    session_code: str
    course_code: str
    scheduled_start: datetime
    completed: bool = True


class ExaminationNotificationRead(BaseModel):
    id: str
    kind: str
    title: str
    body: str
    season_id: str | None = None
    course_code: str | None = None
    created_at: datetime
    read_at: datetime | None = None


class SemesterExaminationOverviewRead(BaseModel):
    academic_year_label: str
    semester_label: str
    upcoming_count: int
    next_examination_at: datetime | None = None
    eligibility: ExaminationEligibilityRead | None = None
