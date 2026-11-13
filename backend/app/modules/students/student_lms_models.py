"""Student LMS portal tracking."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class StudentLearningProgress(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    course_code: str
    materials_viewed: int = 0
    assignments_submitted: int = 0
    quizzes_completed: int = 0
    last_activity_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_learning_progress"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("course_code", ASCENDING)],
                unique=True,
                name="unique_learning_progress",
            ),
        ]


class StudentMaterialAccessLog(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    material_id: PydanticObjectId
    course_code: str
    action: str = "view"
    accessed_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_material_access_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("accessed_at", DESCENDING)],
                name="material_access_logs",
            ),
        ]


class StudentLmsPreferences(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    group_by_unit: bool = True
    show_recorded_lectures: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_lms_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_lms_prefs",
            ),
        ]


class StudentLmsNotificationLog(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    title: str
    body: str
    course_code: str | None = None
    read_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_lms_notification_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="lms_notifications",
            ),
        ]
