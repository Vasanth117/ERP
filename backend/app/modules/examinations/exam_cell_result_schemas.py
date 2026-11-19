"""Result review and approval schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.examinations.exam_cell_grading_enums import (
    ExamResultApprovalStage,
    ExamResultReviewAction,
    ExamResultReviewStatus,
)
from app.modules.examinations.exam_cell_result_models import (
    ExamResultApprovalWorkflow,
    ExamResultReviewHistory,
    ExamResultReviewRecord,
)


class ExamResultReviewStart(BaseModel):
    exam_session_id: str
    department_code: str | None = None
    comment: str | None = Field(default=None, max_length=2000)


class ExamResultReviewComment(BaseModel):
    comment: str = Field(min_length=1, max_length=2000)


class ExamResultReviewDecision(BaseModel):
    approve: bool = True
    comment: str | None = Field(default=None, max_length=2000)


class ExamResultReviewRecordRead(BaseModel):
    review_id: str
    exam_session_id: str
    department_code: str | None
    status: ExamResultReviewStatus
    reviewer_comment: str | None
    issues: list[str]

    @classmethod
    def from_doc(cls, doc: ExamResultReviewRecord) -> "ExamResultReviewRecordRead":
        return cls(
            review_id=doc.review_id,
            exam_session_id=str(doc.exam_session_id),
            department_code=doc.department_code,
            status=doc.status,
            reviewer_comment=doc.reviewer_comment,
            issues=list(doc.issues),
        )


class ExamResultWorkflowRead(BaseModel):
    workflow_id: str
    exam_session_id: str
    current_stage: ExamResultApprovalStage
    status: ExamResultReviewStatus
    department_code: str | None
    submitted_at: datetime | None
    approved_at: datetime | None

    @classmethod
    def from_doc(cls, doc: ExamResultApprovalWorkflow) -> "ExamResultWorkflowRead":
        return cls(
            workflow_id=doc.workflow_id,
            exam_session_id=str(doc.exam_session_id),
            current_stage=doc.current_stage,
            status=doc.status,
            department_code=doc.department_code,
            submitted_at=doc.submitted_at,
            approved_at=doc.approved_at,
        )


class ExamResultSessionSummary(BaseModel):
    exam_session_id: str
    subject_results: int
    semester_results: int
    pass_count: int
    fail_count: int
    absent_count: int
    withheld_count: int
    malpractice_count: int
    missing_marks: int
    workflow_stage: ExamResultApprovalStage | None


class ExamResultReviewHistoryRead(BaseModel):
    history_id: str
    action: ExamResultReviewAction
    actor_id: str | None
    comment: str | None
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamResultReviewHistory) -> "ExamResultReviewHistoryRead":
        return cls(
            history_id=doc.history_id,
            action=doc.action,
            actor_id=str(doc.actor_id) if doc.actor_id else None,
            comment=doc.comment,
            created_at=doc.created_at,
        )