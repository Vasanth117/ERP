"""Student examination portal preferences and notifications (not authoritative schedules)."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.students.examination_portal_enums import ExaminationNotificationKind


class StudentExaminationPreferences(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    calendar_view: str = "month"
    show_eligibility_warnings: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_examination_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_student_exam_prefs",
            ),
        ]


class StudentExaminationNotification(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    kind: ExaminationNotificationKind
    title: str
    body: str
    season_id: str | None = None
    session_code: str | None = None
    course_code: str | None = None
    reference_id: str | None = None
    read_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_examination_notifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="student_exam_notifications",
            ),
        ]
