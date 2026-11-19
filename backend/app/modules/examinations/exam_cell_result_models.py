"""Examination cell — result review and approval."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_grading_enums import (
    ExamResultApprovalStage,
    ExamResultReviewAction,
    ExamResultReviewStatus,
)


class ExamResultReviewRecord(Document):
    tenant_id: PydanticObjectId
    review_id: str
    exam_session_id: PydanticObjectId
    department_code: str | None = None
    student_user_id: PydanticObjectId | None = None
    course_code: str | None = None
    status: ExamResultReviewStatus = ExamResultReviewStatus.PENDING
    reviewer_comment: str | None = Field(default=None, max_length=2000)
    issues: list[str] = Field(default_factory=list)
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_result_review_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("review_id", ASCENDING)],
                unique=True,
                name="unique_exam_result_review_record",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("status", ASCENDING)],
                name="exam_result_reviews_by_session",
            ),
        ]


class ExamResultApprovalWorkflow(Document):
    tenant_id: PydanticObjectId
    workflow_id: str
    exam_session_id: PydanticObjectId
    current_stage: ExamResultApprovalStage = ExamResultApprovalStage.PROVISIONAL
    status: ExamResultReviewStatus = ExamResultReviewStatus.PENDING
    department_code: str | None = None
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    created_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_result_approval_workflows"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("workflow_id", ASCENDING)],
                unique=True,
                name="unique_exam_result_approval_workflow",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING)],
                unique=True,
                name="unique_workflow_per_session",
            ),
        ]


class ExamResultReviewHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    exam_session_id: PydanticObjectId
    workflow_id: str | None = None
    review_id: str | None = None
    action: ExamResultReviewAction
    actor_id: PydanticObjectId | None = None
    comment: str | None = Field(default=None, max_length=2000)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_result_review_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("history_id", ASCENDING)],
                unique=True,
                name="unique_exam_result_review_history",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_result_review_history_timeline",
            ),
        ]