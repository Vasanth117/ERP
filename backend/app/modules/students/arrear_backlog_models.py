"""Student arrear, backlog, and supplementary registration portal data."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.students.arrear_backlog_enums import BacklogStatus, SupplementaryRegistrationStatus


class StudentArrearReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    course_code: str
    backlog_status: BacklogStatus = BacklogStatus.PENDING
    last_attempt_season_id: str | None = None
    last_outcome: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_arrear_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("course_code", ASCENDING)],
                unique=True,
                name="unique_arrear_ref",
            ),
        ]


class StudentExamAttemptHistory(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    course_code: str
    season_id: str
    attempt_number: int
    outcome: str
    is_supplementary: bool = False
    recorded_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_exam_attempt_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("recorded_at", DESCENDING)],
                name="attempt_history_by_student",
            ),
        ]


class StudentSupplementaryRegistration(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    registration_id: str
    supplementary_season_id: str
    course_code: str
    attempt_number: int = Field(ge=1, default=1)
    status: SupplementaryRegistrationStatus = SupplementaryRegistrationStatus.SUBMITTED
    fee_verified: bool = False
    submitted_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_supplementary_registrations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("registration_id", ASCENDING)],
                unique=True,
                name="unique_supplementary_registration",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("user_id", ASCENDING),
                    ("supplementary_season_id", ASCENDING),
                    ("course_code", ASCENDING),
                ],
                unique=True,
                name="unique_supplementary_per_course",
            ),
        ]
