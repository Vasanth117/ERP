"""Examination cell — marks entry and assessment management."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_marks_enums import (
    ExamMarksCandidateStatus,
    ExamMarksComponentStatus,
    ExamMarksCorrectionStatus,
    ExamMarksHistoryAction,
    ExamMarksSubmissionStatus,
)


class ExamMarksSubmission(Document):
    tenant_id: PydanticObjectId
    submission_id: str
    exam_session_id: PydanticObjectId
    course_code: str
    assessment_config_id: str | None = None
    primary_examiner_user_id: PydanticObjectId
    authorized_examiner_user_ids: list[PydanticObjectId] = Field(default_factory=list)
    status: ExamMarksSubmissionStatus = ExamMarksSubmissionStatus.DRAFT
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    locked_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_marks_submissions"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("submission_id", ASCENDING)],
                unique=True,
                name="unique_exam_marks_submission_id",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("exam_session_id", ASCENDING),
                    ("course_code", ASCENDING),
                    ("primary_examiner_user_id", ASCENDING),
                ],
                name="exam_marks_submission_scope",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("status", ASCENDING)],
                name="exam_marks_submissions_by_status",
            ),
        ]


class ExamMarksEntry(Document):
    tenant_id: PydanticObjectId
    entry_id: str
    submission_id: str
    exam_session_id: PydanticObjectId
    student_user_id: PydanticObjectId
    course_code: str
    candidate_status: ExamMarksCandidateStatus = ExamMarksCandidateStatus.PRESENT
    total_marks: float | None = Field(default=None, ge=0)
    max_marks: float | None = Field(default=None, ge=0)
    locked: bool = False
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_marks_entries"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("entry_id", ASCENDING)],
                unique=True,
                name="unique_exam_marks_entry_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("submission_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_exam_marks_entry_student",
            ),
        ]


class ExamMarksComponent(Document):
    tenant_id: PydanticObjectId
    submission_id: str
    entry_id: str
    component_code: str
    component_type: str
    marks_obtained: float | None = Field(default=None, ge=0)
    max_marks: float = Field(ge=0)
    min_marks: float = Field(default=0, ge=0)
    status: ExamMarksComponentStatus = ExamMarksComponentStatus.DRAFT
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_marks_components"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("entry_id", ASCENDING), ("component_code", ASCENDING)],
                unique=True,
                name="unique_exam_marks_component",
            ),
            IndexModel([("tenant_id", ASCENDING), ("submission_id", ASCENDING)], name="exam_marks_components_by_submission"),
        ]


class ExamMarksCorrection(Document):
    tenant_id: PydanticObjectId
    correction_id: str
    submission_id: str
    entry_id: str
    component_code: str | None = None
    requested_marks: float | None = Field(default=None, ge=0)
    reason: str = Field(max_length=1000)
    status: ExamMarksCorrectionStatus = ExamMarksCorrectionStatus.PENDING
    requested_by: PydanticObjectId
    resolved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None

    class Settings:
        name = "exam_marks_corrections"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("correction_id", ASCENDING)],
                unique=True,
                name="unique_exam_marks_correction_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("submission_id", ASCENDING), ("status", ASCENDING)],
                name="exam_marks_corrections_by_submission",
            ),
        ]


class ExamMarksHistory(Document):
    tenant_id: PydanticObjectId
    submission_id: str
    entry_id: str | None = None
    action: ExamMarksHistoryAction
    actor_id: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=500)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_marks_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("submission_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_marks_history_submission",
            ),
        ]