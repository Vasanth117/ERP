"""Incident and malpractice schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.examinations.exam_cell_revaluation_enums import (
    ExamDisciplinaryActionType,
    ExamIncidentStatus,
    ExamIncidentType,
    ExamMalpracticeCaseStatus,
)
from app.modules.examinations.exam_cell_incident_models import ExamIncidentRecord, ExamMalpracticeCase


class ExamIncidentCreate(BaseModel):
    exam_session_id: str | None = None
    incident_type: ExamIncidentType
    location_label: str | None = None
    occurred_at: datetime
    description: str = Field(min_length=10, max_length=5000)
    student_user_ids: list[str] = Field(default_factory=list)
    staff_user_ids: list[str] = Field(default_factory=list)


class ExamMalpracticeCaseCreate(BaseModel):
    incident_id: str
    student_user_id: str
    course_code: str | None = None
    allegation_summary: str = Field(min_length=10, max_length=3000)


class ExamIncidentAssignInvestigator(BaseModel):
    investigator_user_id: str


class ExamInvestigationStatement(BaseModel):
    statement: str = Field(min_length=5, max_length=5000)


class ExamMalpracticeFinding(BaseModel):
    finding_summary: str = Field(min_length=5, max_length=4000)
    committee_recommendation: str | None = Field(default=None, max_length=2000)
    proven: bool | None = None


class ExamDisciplinaryDecisionCreate(BaseModel):
    action_type: ExamDisciplinaryActionType
    details: str = Field(min_length=5, max_length=3000)
    result_withheld: bool = False


class ExamIncidentEvidenceCreate(BaseModel):
    reference_label: str = Field(max_length=200)
    storage_key: str | None = None
    description: str | None = Field(default=None, max_length=2000)


class ExamIncidentRead(BaseModel):
    incident_id: str
    incident_type: ExamIncidentType
    status: ExamIncidentStatus
    occurred_at: datetime
    description: str

    @classmethod
    def from_doc(cls, doc: ExamIncidentRecord) -> "ExamIncidentRead":
        return cls(
            incident_id=doc.incident_id,
            incident_type=doc.incident_type,
            status=doc.status,
            occurred_at=doc.occurred_at,
            description=doc.description,
        )


class ExamMalpracticeCaseRead(BaseModel):
    case_id: str
    incident_id: str
    student_user_id: str
    status: ExamMalpracticeCaseStatus
    proven: bool | None

    @classmethod
    def from_doc(cls, doc: ExamMalpracticeCase) -> "ExamMalpracticeCaseRead":
        return cls(
            case_id=doc.case_id,
            incident_id=doc.incident_id,
            student_user_id=str(doc.student_user_id),
            status=doc.status,
            proven=doc.proven,
        )