"""Student revaluation, rechecking, and marks correction requests."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.students.exam_review_enums import ExamReviewRequestStatus, ExamReviewRequestType


class StudentRevaluationRequest(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_id: str
    season_id: str
    course_code: str
    component_id: str | None = None
    reason: str = Field(max_length=2000)
    status: ExamReviewRequestStatus = ExamReviewRequestStatus.SUBMITTED
    fee_verified: bool = False
    revised_mark_published: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_revaluation_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_revaluation_id"),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("user_id", ASCENDING),
                    ("season_id", ASCENDING),
                    ("course_code", ASCENDING),
                ],
                name="revaluation_by_student_season",
            ),
        ]


class StudentRecheckingRequest(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_id: str
    season_id: str
    course_code: str
    reason: str = Field(max_length=2000)
    status: ExamReviewRequestStatus = ExamReviewRequestStatus.SUBMITTED
    fee_verified: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_rechecking_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_rechecking_id"),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("season_id", ASCENDING), ("course_code", ASCENDING)],
                unique=True,
                name="unique_rechecking_active",
                partialFilterExpression={"status": {"$in": ["submitted", "payment_pending", "under_review", "approved"]}},
            ),
        ]


class StudentMarksCorrectionRequest(Document):
    """Student-initiated correction requests (distinct from faculty `marks_correction_requests`)."""

    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_id: str
    season_id: str
    course_code: str
    component_id: str | None = None
    reason: str = Field(max_length=2000)
    status: ExamReviewRequestStatus = ExamReviewRequestStatus.SUBMITTED
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_marks_correction_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("request_id", ASCENDING)], unique=True, name="unique_student_correction"),
        ]


class StudentExamReviewRequestHistory(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_id: str
    request_type: ExamReviewRequestType
    action: str
    note: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_exam_review_request_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_review_history",
            ),
        ]


class StudentExamReviewPaymentReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_id: str
    fee_code: str
    payment_verified: bool = False
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_exam_review_payment_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_review_payment_ref",
            ),
        ]
