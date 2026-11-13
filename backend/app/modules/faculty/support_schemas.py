"""Faculty student support API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class StudentPerformanceRead(BaseModel):
    student_user_id: str
    roll_number: str | None = None
    display_name: str | None = None
    course_code: str
    attendance_percentage: float
    assessment_average: float
    at_risk: bool


class MentoringRecordCreate(BaseModel):
    student_user_id: str
    course_code: str | None = None
    notes: str = Field(max_length=4000)

    model_config = {"extra": "forbid"}


class MentoringRecordRead(BaseModel):
    id: str
    student_user_id: str
    course_code: str | None
    notes: str
    created_at: datetime


class CounsellingSessionCreate(BaseModel):
    student_user_id: str
    session_at: datetime
    summary: str = Field(max_length=4000)

    model_config = {"extra": "forbid"}


class CounsellingSessionRead(BaseModel):
    id: str
    student_user_id: str
    session_at: datetime
    summary: str
    created_at: datetime


class FollowupCreate(BaseModel):
    student_user_id: str
    title: str = Field(max_length=200)
    action_item: str = Field(max_length=1000)
    due_date: date | None = None

    model_config = {"extra": "forbid"}


class FollowupUpdate(BaseModel):
    status: str = Field(pattern="^(pending|completed|cancelled)$")

    model_config = {"extra": "forbid"}


class FollowupRead(BaseModel):
    id: str
    student_user_id: str
    title: str
    action_item: str
    due_date: date | None
    status: str


class ImprovementPlanCreate(BaseModel):
    student_user_id: str
    course_code: str
    goals: list[str] = Field(min_length=1)
    start_date: date
    target_date: date

    model_config = {"extra": "forbid"}


class ImprovementPlanRead(BaseModel):
    id: str
    student_user_id: str
    course_code: str
    goals: list[str]
    start_date: date
    target_date: date
    status: str


class AcademicReportRead(BaseModel):
    id: str
    report_type: str
    course_code: str | None
    student_user_id: str | None
    payload: dict
    generated_at: datetime
