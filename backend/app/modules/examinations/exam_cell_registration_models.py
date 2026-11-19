"""Examination cell — eligibility and registration collections."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_registration_enums import (
    ExamEligibilityRuleCode,
    ExamRegistrationHistoryAction,
    ExamRegistrationStatus,
    ExamRegistrationSubjectType,
)


class ExamEligibilityRecord(Document):
    tenant_id: PydanticObjectId
    eligibility_id: str
    exam_session_id: PydanticObjectId
    season_id: str | None = None
    student_user_id: PydanticObjectId
    overall_eligible: bool = False
    summary_reasons: list[str] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=utcnow)
    published: bool = False
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_eligibility_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("eligibility_id", ASCENDING)],
                unique=True,
                name="unique_exam_eligibility_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("exam_session_id", ASCENDING)],
                unique=True,
                name="unique_exam_eligibility_per_student_session",
            ),
        ]


class ExamEligibilityRuleResult(Document):
    tenant_id: PydanticObjectId
    eligibility_id: str
    rule_code: ExamEligibilityRuleCode
    passed: bool
    message: str
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_eligibility_rule_results"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("eligibility_id", ASCENDING), ("rule_code", ASCENDING)],
                unique=True,
                name="unique_exam_eligibility_rule",
            ),
        ]


class ExamRegistration(Document):
    tenant_id: PydanticObjectId
    registration_id: str
    exam_session_id: PydanticObjectId
    season_id: str | None = None
    student_user_id: PydanticObjectId
    academic_year_label: str
    semester_label: str
    status: ExamRegistrationStatus = ExamRegistrationStatus.DRAFT
    fee_verified: bool = False
    submitted_at: datetime | None = None
    confirmed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_registrations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("registration_id", ASCENDING)],
                unique=True,
                name="unique_exam_registration_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("exam_session_id", ASCENDING)],
                name="exam_registrations_by_student_session",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("status", ASCENDING)],
                name="exam_registrations_by_session_status",
            ),
        ]


class ExamRegistrationSubject(Document):
    tenant_id: PydanticObjectId
    registration_id: str
    student_user_id: PydanticObjectId
    exam_session_id: PydanticObjectId
    course_code: str
    subject_code: str | None = None
    paper_code: str | None = None
    subject_type: ExamRegistrationSubjectType = ExamRegistrationSubjectType.SEMESTER
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_registration_subjects"
        indexes = [
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("exam_session_id", ASCENDING),
                    ("course_code", ASCENDING),
                ],
                unique=True,
                name="unique_exam_reg_subject",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("registration_id", ASCENDING)],
                name="exam_reg_subjects_by_registration",
            ),
        ]


class ExamRegistrationHistory(Document):
    tenant_id: PydanticObjectId
    registration_id: str
    exam_session_id: PydanticObjectId
    student_user_id: PydanticObjectId
    action: ExamRegistrationHistoryAction
    actor_id: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_registration_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("registration_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_registration_history_timeline",
            ),
        ]