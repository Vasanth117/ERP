"""Examination cell — authoritative exam session registry."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType


class ExamSession(Document):
    tenant_id: PydanticObjectId
    session_id: str
    session_code: str
    name: str
    examination_type: ExamSessionType = ExamSessionType.REGULAR
    academic_year_label: str
    semester_label: str
    season_id: str | None = Field(
        default=None,
        description="Links to semester_examination_seasons.season_id when provisioned.",
    )
    registration_start_at: datetime
    registration_end_at: datetime
    examination_start_at: datetime
    examination_end_at: datetime
    result_processing_deadline_at: datetime | None = None
    status: ExamSessionStatus = ExamSessionStatus.DRAFT
    cancelled_at: datetime | None = None
    archived_at: datetime | None = None
    created_by: PydanticObjectId | None = None
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_sessions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("session_code", ASCENDING)],
                unique=True,
                name="unique_exam_session_code",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("session_id", ASCENDING)],
                unique=True,
                name="unique_exam_session_id",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("academic_year_label", ASCENDING),
                    ("semester_label", ASCENDING),
                    ("status", ASCENDING),
                ],
                name="exam_sessions_by_term_status",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("season_id", ASCENDING)],
                name="exam_sessions_by_season",
                sparse=True,
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("examination_start_at", ASCENDING)],
                name="exam_sessions_by_schedule",
            ),
        ]


class ExamSessionAcademicScope(Document):
    tenant_id: PydanticObjectId
    exam_session_id: PydanticObjectId
    department_codes: list[str] = Field(default_factory=list)
    programme_codes: list[str] = Field(default_factory=list)
    batch_labels: list[str] = Field(default_factory=list)
    semester_labels: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_session_academic_scopes"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING)],
                unique=True,
                name="unique_exam_session_scope",
            ),
        ]


class ExamSessionStatusHistory(Document):
    tenant_id: PydanticObjectId
    exam_session_id: PydanticObjectId
    from_status: ExamSessionStatus | None = None
    to_status: ExamSessionStatus
    actor_id: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_session_status_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_session_history_timeline",
            ),
        ]


class ExamSessionRegistrationRules(Document):
    """Per-session registration eligibility toggles (college admin setup)."""

    tenant_id: PydanticObjectId
    exam_session_id: PydanticObjectId
    block_unpaid_students: bool = True
    block_below_attendance: bool = True
    allow_late_registration: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_session_registration_rules"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING)],
                unique=True,
                name="unique_exam_session_registration_rules",
            ),
        ]


class ExamActivityLog(Document):
    tenant_id: PydanticObjectId
    event_id: str
    exam_session_id: PydanticObjectId | None = None
    season_id: str | None = None
    action: str
    summary: str
    actor_id: PydanticObjectId | None = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_activity_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("event_id", ASCENDING)],
                unique=True,
                name="unique_exam_activity_event",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_activity_recent",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_activity_by_session",
                sparse=True,
            ),
        ]