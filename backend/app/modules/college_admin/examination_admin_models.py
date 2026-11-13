"""College admin examination administration collections."""

from datetime import datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.enums import AssessmentComponentType, MarksBatchStatus


class ExaminationType(str, Enum):
    SEMESTER = "semester"
    SUPPLEMENTARY = "supplementary"
    ARREAR = "arrear"
    PRACTICAL = "practical"


class ExaminationConfiguration(Document):
    tenant_id: PydanticObjectId
    season_id: str
    examination_type: ExaminationType = ExaminationType.SEMESTER
    title: str
    academic_year_label: str
    semester_label: str
    component_definitions: list[dict[str, Any]] = Field(default_factory=list)
    regulations: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    published: bool = False
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_configurations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("season_id", ASCENDING)],
                unique=True,
                name="unique_exam_configuration_season",
            ),
        ]


class ExaminationSessionRecord(Document):
    """Admin registry; authoritative schedule is `semester_examination_sessions`."""

    tenant_id: PydanticObjectId
    season_id: str
    session_code: str
    semester_session_id: PydanticObjectId | None = None
    examination_type: ExaminationType = ExaminationType.SEMESTER
    published: bool = False
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_sessions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("season_id", ASCENDING), ("session_code", ASCENDING)],
                unique=True,
                name="unique_examination_session_admin",
            ),
        ]


class InstitutionExaminationSchedule(Document):
    tenant_id: PydanticObjectId
    season_id: str
    session_code: str
    course_code: str
    scheduled_start: datetime
    scheduled_end: datetime | None = None
    centre_code: str | None = None
    room: str | None = None
    seating_plan: dict[str, Any] = Field(default_factory=dict)
    semester_session_id: PydanticObjectId | None = None
    published: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "college_examination_schedules"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("season_id", ASCENDING), ("session_code", ASCENDING)],
                unique=True,
                name="unique_exam_schedule",
            ),
        ]


class ExaminationEligibilityRecord(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    season_id: str
    eligible: bool
    reasons: list[str] = Field(default_factory=list)
    authoritative_eligibility_id: PydanticObjectId | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_eligibility_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("season_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_eligibility_history",
            ),
        ]


class HallTicketRecord(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    season_id: str
    hall_ticket_id: PydanticObjectId | None = None
    workflow_status: str = "draft"
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hall_ticket_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("season_id", ASCENDING)],
                name="hall_ticket_records_by_student",
            ),
        ]


class ExaminationMarkRecord(Document):
    tenant_id: PydanticObjectId
    batch_id: PydanticObjectId
    assessment_id: str
    component_id: str
    course_code: str
    review_status: MarksBatchStatus = MarksBatchStatus.PENDING_APPROVAL
    component_type: AssessmentComponentType | None = None
    actor_id: PydanticObjectId | None = None
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_marks"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("batch_id", ASCENDING)], unique=True, name="unique_exam_mark_review"),
        ]


class ExaminationApprovalRecord(Document):
    tenant_id: PydanticObjectId
    scope: str = Field(max_length=64)
    resource_type: str
    resource_id: str
    decision: str
    actor_id: PydanticObjectId
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_approval_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="exam_approvals_recent"),
        ]


class ExaminationResultPublicationRecord(Document):
    """Audit overlay when college admin publishes semester results."""

    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    season_id: str
    publication_id: PydanticObjectId | None = None
    published: bool = False
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_result_publications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("season_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_result_publication_log",
            ),
        ]
