"""Result publication request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.examinations.exam_cell_publication_enums import (
    ExamPublicationScopeType,
    ExamPublicationStatus,
    ExamResultDocumentType,
)
from app.modules.examinations.exam_cell_publication_models import (
    ExamPublicationHistory,
    ExamResultDocument,
    ExamResultPublication,
)


class ExamPublicationCreate(BaseModel):
    exam_session_id: str
    workflow_id: str | None = None
    scope_type: ExamPublicationScopeType = ExamPublicationScopeType.SESSION
    programme_code: str | None = None
    semester_label: str | None = None
    student_group_label: str | None = None
    publish_at: datetime | None = None
    visibility_default: bool = True

    @field_validator("programme_code")
    @classmethod
    def normalize(cls, value: str | None) -> str | None:
        return value.strip().upper() if value else None


class ExamPublicationProcessRequest(BaseModel):
    exam_session_id: str
    workflow_id: str | None = None


class ExamPublicationValidationReport(BaseModel):
    ready: bool
    workflow_approved: bool
    pending_results: int
    withheld_results: int
    unresolved_results: int
    approved_subjects: int
    policy_id: str | None
    policy_version: int | None
    issues: list[str]


class ExamPublicationRead(BaseModel):
    publication_id: str
    exam_session_id: str
    status: ExamPublicationStatus
    version: int
    scope_type: ExamPublicationScopeType
    programme_code: str | None
    publish_at: datetime | None
    published_at: datetime | None
    students_included: int
    policy_id: str | None
    policy_version: int | None

    @classmethod
    def from_doc(cls, doc: ExamResultPublication) -> "ExamPublicationRead":
        return cls(
            publication_id=doc.publication_id,
            exam_session_id=str(doc.exam_session_id),
            status=doc.status,
            version=doc.version,
            scope_type=doc.scope_type,
            programme_code=doc.programme_code,
            publish_at=doc.publish_at,
            published_at=doc.published_at,
            students_included=doc.students_included,
            policy_id=doc.policy_id,
            policy_version=doc.policy_version,
        )


class ExamPublicationApprove(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class ExamPublicationWithholdRequest(BaseModel):
    student_user_id: str
    withhold: bool = True
    note: str | None = None


class ExamPublicationReleaseRequest(BaseModel):
    student_user_id: str
    note: str | None = None


class ExamPublicationReviseRequest(BaseModel):
    note: str | None = Field(default=None, max_length=500)


class ExamPublicationHistoryRead(BaseModel):
    action: str
    actor_id: str | None
    note: str | None
    created_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamPublicationHistory) -> "ExamPublicationHistoryRead":
        return cls(
            action=doc.action.value,
            actor_id=str(doc.actor_id) if doc.actor_id else None,
            note=doc.note,
            created_at=doc.created_at,
        )


class ExamDocumentGenerateRequest(BaseModel):
    publication_id: str
    student_user_id: str
    document_type: ExamResultDocumentType
    course_code: str | None = None
    include_arrear: bool = False


class ExamDocumentBulkGenerateRequest(BaseModel):
    publication_id: str
    document_type: ExamResultDocumentType
    student_user_ids: list[str] | None = None


class ExamDocumentRead(BaseModel):
    document_id: str
    document_type: ExamResultDocumentType
    publication_id: str
    student_user_id: str
    version: int
    verification_code: str
    file_name: str
    generated_at: datetime

    @classmethod
    def from_doc(cls, doc: ExamResultDocument) -> "ExamDocumentRead":
        return cls(
            document_id=doc.document_id,
            document_type=doc.document_type,
            publication_id=doc.publication_id,
            student_user_id=str(doc.student_user_id),
            version=doc.version,
            verification_code=doc.verification_code,
            file_name=doc.file_name,
            generated_at=doc.generated_at,
        )


class ExamDocumentVerifyRequest(BaseModel):
    document_id: str
    verification_code: str


class ExamDocumentVerifyResponse(BaseModel):
    valid: bool
    document_id: str
    document_type: ExamResultDocumentType | None
    student_user_id: str | None


class ExamStudentPublishedResultRead(BaseModel):
    course_code: str
    grade_letter: str | None
    grade_point: float | None
    credits_earned: float
    gpa: float | None
    cgpa: float | None
    publication_id: str
    published_at: datetime | None