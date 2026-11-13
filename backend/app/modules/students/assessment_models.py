"""Student assessment portal collections (preferences, progress, notifications)."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.students.assessment_enums import AssessmentNotificationKind


class StudentCiaViewPreferences(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    group_by_subject: bool = True
    include_unpublished_placeholders: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_cia_view_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_cia_view_prefs",
            ),
        ]


class StudentAssignmentProgress(Document):
    """Cached progress flags; authoritative submission state remains in LMS collections."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    assignment_id: PydanticObjectId
    course_code: str
    last_viewed_at: datetime = Field(default_factory=utcnow)
    submission_status: str | None = None
    evaluation_published: bool = False

    class Settings:
        name = "student_assignment_progress"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("assignment_id", ASCENDING)],
                unique=True,
                name="unique_assignment_progress",
            ),
        ]


class StudentAssessmentNotification(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    kind: AssessmentNotificationKind
    title: str
    body: str
    course_code: str | None = None
    reference_id: str | None = None
    read_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_assessment_notifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="assessment_notifications_by_student",
            ),
        ]
