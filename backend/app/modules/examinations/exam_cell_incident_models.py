"""Examination incidents and malpractice case management."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_revaluation_enums import (
    ExamDisciplinaryActionType,
    ExamIncidentHistoryAction,
    ExamIncidentStatus,
    ExamIncidentType,
    ExamMalpracticeCaseStatus,
)


class ExamIncidentRecord(Document):
    tenant_id: PydanticObjectId
    incident_id: str
    exam_session_id: PydanticObjectId | None = None
    incident_type: ExamIncidentType
    location_label: str | None = None
    occurred_at: datetime
    description: str = Field(max_length=5000)
    student_user_ids: list[PydanticObjectId] = Field(default_factory=list)
    staff_user_ids: list[PydanticObjectId] = Field(default_factory=list)
    status: ExamIncidentStatus = ExamIncidentStatus.REPORTED
    reported_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_incident_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("incident_id", ASCENDING)],
                unique=True,
                name="unique_exam_incident_record",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("status", ASCENDING)],
                name="exam_incidents_by_session",
            ),
        ]


class ExamMalpracticeCase(Document):
    tenant_id: PydanticObjectId
    case_id: str
    incident_id: str
    exam_session_id: PydanticObjectId | None = None
    student_user_id: PydanticObjectId
    course_code: str | None = None
    status: ExamMalpracticeCaseStatus = ExamMalpracticeCaseStatus.ALLEGED
    investigator_user_id: PydanticObjectId | None = None
    allegation_summary: str = Field(max_length=3000)
    finding_summary: str | None = Field(default=None, max_length=4000)
    committee_recommendation: str | None = Field(default=None, max_length=2000)
    proven: bool | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_malpractice_cases"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("case_id", ASCENDING)],
                unique=True,
                name="unique_exam_malpractice_case",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("incident_id", ASCENDING)],
                name="exam_malpractice_by_incident",
            ),
        ]


class ExamIncidentEvidence(Document):
    tenant_id: PydanticObjectId
    evidence_id: str
    incident_id: str
    case_id: str | None = None
    reference_label: str = Field(max_length=200)
    storage_key: str | None = None
    description: str | None = Field(default=None, max_length=2000)
    restricted: bool = True
    uploaded_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_incident_evidence"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("evidence_id", ASCENDING)],
                unique=True,
                name="unique_exam_incident_evidence",
            ),
        ]


class ExamInvestigationRecord(Document):
    tenant_id: PydanticObjectId
    investigation_id: str
    case_id: str
    investigator_user_id: PydanticObjectId
    statement: str = Field(max_length=5000)
    status: str = "open"
    recorded_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_investigation_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("investigation_id", ASCENDING)],
                unique=True,
                name="unique_exam_investigation_record",
            ),
        ]


class ExamDisciplinaryDecision(Document):
    tenant_id: PydanticObjectId
    decision_id: str
    case_id: str
    action_type: ExamDisciplinaryActionType
    authorized_by: PydanticObjectId | None = None
    details: str = Field(max_length=3000)
    result_withheld: bool = False
    appeal_allowed_until: datetime | None = None
    decided_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_disciplinary_decisions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("decision_id", ASCENDING)],
                unique=True,
                name="unique_exam_disciplinary_decision",
            ),
        ]


class ExamIncidentHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    incident_id: str
    case_id: str | None = None
    action: ExamIncidentHistoryAction
    actor_id: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=2000)
    restricted: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_incident_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("history_id", ASCENDING)],
                unique=True,
                name="unique_exam_incident_history",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("incident_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_incident_history_timeline",
            ),
        ]