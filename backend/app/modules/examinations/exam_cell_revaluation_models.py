"""Revaluation and supplementary examination collections."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_revaluation_enums import (
    ExamRevaluationApplicationStatus,
    ExamRevaluationApplicationType,
    ExamRevaluationHistoryAction,
    ExamSupplementaryRegistrationStatus,
)


class ExamRevaluationApplication(Document):
    tenant_id: PydanticObjectId
    application_id: str
    application_type: ExamRevaluationApplicationType
    student_user_id: PydanticObjectId
    exam_session_id: PydanticObjectId
    course_code: str
    subject_result_id: str
    publication_id: str | None = None
    season_id: str | None = None
    status: ExamRevaluationApplicationStatus = ExamRevaluationApplicationStatus.SUBMITTED
    fee_code: str | None = None
    fee_amount: float = Field(default=0, ge=0)
    fee_verified: bool = False
    payment_request_id: str | None = None
    deadline_at: datetime | None = None
    evaluator_user_id: PydanticObjectId | None = None
    original_marks: float | None = None
    original_grade: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_revaluation_applications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("application_id", ASCENDING)],
                unique=True,
                name="unique_exam_revaluation_application",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("exam_session_id", ASCENDING), ("course_code", ASCENDING)],
                name="exam_revaluation_by_student_course",
            ),
        ]


class ExamRevaluationEvaluation(Document):
    tenant_id: PydanticObjectId
    evaluation_id: str
    application_id: str
    evaluator_user_id: PydanticObjectId
    original_marks: float | None = None
    original_max_marks: float | None = None
    revised_marks: float | None = None
    revised_max_marks: float | None = None
    findings: str | None = Field(default=None, max_length=4000)
    recorded_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_revaluation_evaluations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("evaluation_id", ASCENDING)],
                unique=True,
                name="unique_exam_revaluation_evaluation",
            ),
            IndexModel([("tenant_id", ASCENDING), ("application_id", ASCENDING)], name="exam_revaluation_eval_by_app"),
        ]


class ExamRevaluationApproval(Document):
    tenant_id: PydanticObjectId
    approval_id: str
    application_id: str
    approved: bool
    approver_id: PydanticObjectId | None = None
    comment: str | None = Field(default=None, max_length=2000)
    decided_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_revaluation_approvals"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("approval_id", ASCENDING)],
                unique=True,
                name="unique_exam_revaluation_approval",
            ),
        ]


class ExamRevaluationHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    application_id: str
    action: ExamRevaluationHistoryAction
    actor_id: PydanticObjectId | None = None
    before_snapshot: dict = Field(default_factory=dict)
    after_snapshot: dict = Field(default_factory=dict)
    note: str | None = Field(default=None, max_length=2000)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_revaluation_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("history_id", ASCENDING)],
                unique=True,
                name="unique_exam_revaluation_history",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("application_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_revaluation_history_timeline",
            ),
        ]


class ExamSupplementaryRegistration(Document):
    tenant_id: PydanticObjectId
    registration_id: str
    student_user_id: PydanticObjectId
    exam_session_id: PydanticObjectId | None = None
    supplementary_season_id: str | None = None
    course_codes: list[str] = Field(default_factory=list)
    status: ExamSupplementaryRegistrationStatus = ExamSupplementaryRegistrationStatus.DRAFT
    fee_verified: bool = False
    payment_request_id: str | None = None
    registration_deadline_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_supplementary_registrations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("registration_id", ASCENDING)],
                unique=True,
                name="unique_exam_supplementary_registration",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("supplementary_season_id", ASCENDING)],
                name="exam_supplementary_by_student",
            ),
        ]


class ExamSupplementaryAttempt(Document):
    tenant_id: PydanticObjectId
    attempt_id: str
    registration_id: str
    student_user_id: PydanticObjectId
    course_code: str
    exam_session_id: PydanticObjectId | None = None
    attempt_number: int = Field(default=1, ge=1)
    outcome: str | None = None
    grade_letter: str | None = None
    grade_point: float | None = None
    result_snapshot: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_supplementary_attempts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("attempt_id", ASCENDING)],
                unique=True,
                name="unique_exam_supplementary_attempt",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("course_code", ASCENDING),
                    ("attempt_number", ASCENDING),
                ],
                unique=True,
                name="unique_supplementary_attempt_number",
            ),
        ]