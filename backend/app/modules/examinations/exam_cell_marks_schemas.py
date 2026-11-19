"""Examination cell — marks entry schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.examinations.exam_cell_marks_enums import (
    ExamMarksCandidateStatus,
    ExamMarksCorrectionStatus,
    ExamMarksHistoryAction,
    ExamMarksSubmissionStatus,
)
from app.modules.examinations.exam_cell_marks_models import ExamMarksCorrection, ExamMarksEntry, ExamMarksSubmission


class ExamMarksAccessGrant(BaseModel):
    exam_session_id: str
    course_code: str
    assessment_config_id: str | None = None
    primary_examiner_user_id: str
    authorized_examiner_user_ids: list[str] = Field(default_factory=list)

    @field_validator("course_code")
    @classmethod
    def normalize_course(cls, value: str) -> str:
        return value.strip().upper()


class ExamMarksSubmissionRead(BaseModel):
    id: str
    submission_id: str
    exam_session_id: str
    course_code: str
    assessment_config_id: str | None
    primary_examiner_user_id: str
    authorized_examiner_user_ids: list[str]
    status: ExamMarksSubmissionStatus
    submitted_at: datetime | None
    approved_at: datetime | None
    locked_at: datetime | None

    @classmethod
    def from_doc(cls, doc: ExamMarksSubmission) -> "ExamMarksSubmissionRead":
        return cls(
            id=str(doc.id),
            submission_id=doc.submission_id,
            exam_session_id=str(doc.exam_session_id),
            course_code=doc.course_code,
            assessment_config_id=doc.assessment_config_id,
            primary_examiner_user_id=str(doc.primary_examiner_user_id),
            authorized_examiner_user_ids=[str(x) for x in doc.authorized_examiner_user_ids],
            status=doc.status,
            submitted_at=doc.submitted_at,
            approved_at=doc.approved_at,
            locked_at=doc.locked_at,
        )


class ExamMarksComponentInput(BaseModel):
    component_code: str
    component_type: str = "theory"
    marks_obtained: float | None = Field(default=None, ge=0)
    max_marks: float = Field(gt=0)
    min_marks: float = Field(default=0, ge=0)

    @field_validator("component_code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()


class ExamMarksEntryUpsert(BaseModel):
    student_user_id: str
    candidate_status: ExamMarksCandidateStatus = ExamMarksCandidateStatus.PRESENT
    components: list[ExamMarksComponentInput] = Field(default_factory=list)


class ExamMarksBulkUpsert(BaseModel):
    entries: list[ExamMarksEntryUpsert] = Field(min_length=1)


class ExamMarksEntryRead(BaseModel):
    entry_id: str
    submission_id: str
    student_user_id: str
    course_code: str
    candidate_status: ExamMarksCandidateStatus
    total_marks: float | None
    max_marks: float | None
    locked: bool
    components: list[ExamMarksComponentInput]

    @classmethod
    def from_parts(cls, doc: ExamMarksEntry, components: list[ExamMarksComponentInput]) -> "ExamMarksEntryRead":
        return cls(
            entry_id=doc.entry_id,
            submission_id=doc.submission_id,
            student_user_id=str(doc.student_user_id),
            course_code=doc.course_code,
            candidate_status=doc.candidate_status,
            total_marks=doc.total_marks,
            max_marks=doc.max_marks,
            locked=doc.locked,
            components=components,
        )


class ExamMarksSubmitRequest(BaseModel):
    note: str | None = Field(default=None, max_length=300)


class ExamMarksCorrectionRequest(BaseModel):
    entry_id: str
    component_code: str | None = None
    requested_marks: float | None = Field(default=None, ge=0)
    reason: str = Field(min_length=3, max_length=1000)


class ExamMarksCorrectionRead(BaseModel):
    correction_id: str
    submission_id: str
    entry_id: str
    component_code: str | None
    requested_marks: float | None
    reason: str
    status: ExamMarksCorrectionStatus

    @classmethod
    def from_doc(cls, doc: ExamMarksCorrection) -> "ExamMarksCorrectionRead":
        return cls(
            correction_id=doc.correction_id,
            submission_id=doc.submission_id,
            entry_id=doc.entry_id,
            component_code=doc.component_code,
            requested_marks=doc.requested_marks,
            reason=doc.reason,
            status=doc.status,
        )


class ExamMarksImportRow(BaseModel):
    roll_number: str | None = None
    student_user_id: str | None = None
    candidate_status: ExamMarksCandidateStatus = ExamMarksCandidateStatus.PRESENT
    component_code: str
    marks_obtained: float | None = Field(default=None, ge=0)
    max_marks: float = Field(gt=0)


class ExamMarksImportRequest(BaseModel):
    rows: list[ExamMarksImportRow] = Field(min_length=1)


class ExamMarksImportError(BaseModel):
    row_index: int
    message: str


class ExamMarksImportResult(BaseModel):
    accepted: int
    rejected: int
    errors: list[ExamMarksImportError]


class ExamMarksSubjectSummary(BaseModel):
    course_code: str
    entries_total: int
    entries_with_marks: int
    submitted: bool
    status: ExamMarksSubmissionStatus


class ExamMarksHistoryRead(BaseModel):
    submission_id: str
    action: ExamMarksHistoryAction
    actor_id: str | None
    note: str | None
    created_at: datetime