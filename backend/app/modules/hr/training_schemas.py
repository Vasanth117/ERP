"""Training management API schemas."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from app.modules.hr.enums import HrTrainingEnrollmentStatus, HrTrainingProgramStatus
from app.modules.hr.training_models import HrTrainingEnrollment, HrTrainingProgram


class TrainingProgramUpsert(BaseModel):
    program_code: str
    title: str
    description: str | None = None
    category: str
    objectives: list[str] = Field(default_factory=list)
    trainer_name: str | None = None
    provider: str | None = None
    venue: str | None = None
    mode: str = "in_person"
    duration_hours: int = 0
    schedule: dict[str, Any] = Field(default_factory=dict)
    capacity: int = 0
    eligibility_rules: dict[str, Any] = Field(default_factory=dict)
    completion_criteria: dict[str, Any] = Field(default_factory=dict)
    status: HrTrainingProgramStatus = HrTrainingProgramStatus.DRAFT


class TrainingProgramRead(BaseModel):
    id: str
    program_code: str
    title: str
    status: str

    @classmethod
    def from_doc(cls, doc: HrTrainingProgram) -> "TrainingProgramRead":
        return cls(id=str(doc.id), program_code=doc.program_code, title=doc.title, status=doc.status.value)


class TrainingEnrollmentCreate(BaseModel):
    training_program_id: str
    employee_user_id: str
    enrollment_source: str = "self"


class TrainingEnrollmentReview(BaseModel):
    action: str = Field(pattern="^(confirm|waitlist|reject|cancel)$")


class TrainingEnrollmentRead(BaseModel):
    id: str
    program_code: str
    employee_user_id: str
    status: HrTrainingEnrollmentStatus

    @classmethod
    def from_doc(cls, doc: HrTrainingEnrollment) -> "TrainingEnrollmentRead":
        return cls(id=str(doc.id), program_code=doc.program_code, employee_user_id=str(doc.employee_user_id), status=doc.status)


class TrainingAttendanceUpsert(BaseModel):
    session_code: str
    session_date: date
    status: str = "present"
    attended_minutes: int = 0


class TrainingAssessmentSubmit(BaseModel):
    score: str
    max_score: str
    feedback: str | None = None