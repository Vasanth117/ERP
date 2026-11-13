"""Semester and university examination authority (examination cell writes)."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.enums import ExaminationAnnouncementAudience, ExaminationEligibilityStatus


class ExaminationCentre(Document):
    tenant_id: PydanticObjectId
    centre_code: str
    name: str
    building: str | None = None
    address: str | None = None
    contact_phone: str | None = None
    room_labels: list[str] = Field(default_factory=list)
    is_active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_centres"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("centre_code", ASCENDING)],
                unique=True,
                name="unique_examination_centre",
            ),
        ]


class SemesterExaminationSeason(Document):
    tenant_id: PydanticObjectId
    season_id: str
    title: str
    academic_year_label: str
    semester_label: str
    starts_at: datetime
    ends_at: datetime
    published: bool = False
    regulations_summary: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "semester_examination_seasons"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("season_id", ASCENDING)],
                unique=True,
                name="unique_exam_season",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("academic_year_label", ASCENDING), ("semester_label", ASCENDING)],
                name="exam_season_by_term",
            ),
        ]


class SemesterExaminationSession(Document):
    tenant_id: PydanticObjectId
    season_id: str
    session_code: str
    course_code: str
    course_name: str | None = None
    section: str | None = None
    paper_code: str | None = None
    scheduled_start: datetime
    scheduled_end: datetime | None = None
    centre_code: str | None = None
    room: str | None = None
    instructions: str | None = None
    published: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "semester_examination_sessions"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("season_id", ASCENDING),
                    ("session_code", ASCENDING),
                ],
                unique=True,
                name="unique_semester_exam_session",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("season_id", ASCENDING), ("scheduled_start", ASCENDING)],
                name="semester_sessions_by_schedule",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("course_code", ASCENDING), ("published", ASCENDING)],
                name="semester_sessions_by_course",
            ),
        ]


class StudentExaminationEligibility(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    season_id: str
    status: ExaminationEligibilityStatus = ExaminationEligibilityStatus.PENDING_REVIEW
    eligible: bool = False
    reasons: list[str] = Field(default_factory=list)
    attendance_cleared: bool | None = None
    fee_cleared: bool | None = None
    arrear_course_codes: list[str] = Field(default_factory=list)
    semester_course_codes: list[str] = Field(default_factory=list)
    published: bool = False
    published_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_examination_eligibility"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("season_id", ASCENDING),
                ],
                unique=True,
                name="unique_student_exam_eligibility",
            ),
        ]


class ExaminationRegulation(Document):
    tenant_id: PydanticObjectId
    season_id: str | None = None
    regulation_id: str
    title: str
    body: str
    version: str = "1.0"
    published: bool = False
    published_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_regulations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("regulation_id", ASCENDING)],
                unique=True,
                name="unique_examination_regulation",
            ),
        ]


class ExaminationAnnouncement(Document):
    tenant_id: PydanticObjectId
    season_id: str | None = None
    announcement_id: str
    title: str
    body: str
    audience: ExaminationAnnouncementAudience = ExaminationAnnouncementAudience.STUDENTS
    published: bool = False
    published_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_announcements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("announcement_id", ASCENDING)],
                unique=True,
                name="unique_examination_announcement",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("published", ASCENDING), ("published_at", DESCENDING)],
                name="exam_announcements_published",
            ),
        ]


class ExaminationScheduleChange(Document):
    tenant_id: PydanticObjectId
    season_id: str | None = None
    session_code: str | None = None
    course_code: str | None = None
    change_type: str
    summary: str
    previous_values: dict = Field(default_factory=dict)
    new_values: dict = Field(default_factory=dict)
    effective_at: datetime
    published: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "examination_schedule_changes"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("season_id", ASCENDING), ("effective_at", DESCENDING)],
                name="exam_changes_by_season",
            ),
        ]
