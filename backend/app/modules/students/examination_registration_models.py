"""Student examination registration, hall ticket refs, and result preferences."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.students.examination_registration_enums import (
    ExamRegistrationHistoryAction,
    ExamRegistrationSubjectType,
    ResultNotificationKind,
    StudentExamRegistrationStatus,
)


class StudentExamRegistration(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    season_id: str
    registration_id: str
    academic_year_label: str
    semester_label: str
    status: StudentExamRegistrationStatus = StudentExamRegistrationStatus.DRAFT
    fee_verified: bool = False
    submitted_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_exam_registrations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("registration_id", ASCENDING)],
                unique=True,
                name="unique_student_exam_registration_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("season_id", ASCENDING)],
                name="exam_registrations_by_student_season",
            ),
        ]


class StudentExamRegistrationSubject(Document):
    tenant_id: PydanticObjectId
    registration_id: str
    user_id: PydanticObjectId
    season_id: str
    course_code: str
    course_name: str | None = None
    subject_type: ExamRegistrationSubjectType = ExamRegistrationSubjectType.SEMESTER
    paper_code: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_exam_registration_subjects"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("user_id", ASCENDING),
                    ("season_id", ASCENDING),
                    ("course_code", ASCENDING),
                ],
                unique=True,
                name="unique_exam_reg_subject_per_season",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("registration_id", ASCENDING)],
                name="exam_reg_subjects_by_registration",
            ),
        ]


class StudentExamRegistrationHistory(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    registration_id: str
    season_id: str
    action: ExamRegistrationHistoryAction
    note: str | None = None
    actor_user_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_exam_registration_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_reg_history_by_student",
            ),
        ]


class StudentHallTicketReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    season_id: str
    hall_ticket_id: PydanticObjectId
    ticket_number: str
    last_viewed_at: datetime | None = None
    availability_status: str = "unknown"
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_hall_ticket_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("season_id", ASCENDING)],
                unique=True,
                name="unique_hall_ticket_ref",
            ),
        ]


class StudentHallTicketDownloadLog(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    season_id: str
    ticket_number: str
    ip_address: str | None = None
    user_agent: str | None = None
    downloaded_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_hall_ticket_download_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("downloaded_at", DESCENDING)],
                name="hall_ticket_downloads",
            ),
        ]


class StudentResultViewPreferences(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    group_by_semester: bool = True
    show_attempt_history: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_result_view_preferences"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_result_view_prefs",
            ),
        ]


class StudentResultNotification(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    kind: ResultNotificationKind
    season_id: str | None = None
    title: str
    body: str
    read_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_result_notifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="result_notifications_by_student",
            ),
        ]
