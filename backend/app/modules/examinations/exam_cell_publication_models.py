"""Examination cell — official result publication and academic documents."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.examinations.exam_cell_publication_enums import (
    ExamPublicationHistoryAction,
    ExamPublicationScopeType,
    ExamPublicationStatus,
    ExamResultDocumentType,
)


class ExamResultPublication(Document):
    tenant_id: PydanticObjectId
    publication_id: str
    exam_session_id: PydanticObjectId
    workflow_id: str | None = None
    scope_type: ExamPublicationScopeType = ExamPublicationScopeType.SESSION
    programme_code: str | None = None
    semester_label: str | None = None
    student_group_label: str | None = None
    status: ExamPublicationStatus = ExamPublicationStatus.DRAFT
    version: int = Field(default=1, ge=1)
    policy_id: str | None = None
    policy_version: int | None = None
    publish_at: datetime | None = None
    published_at: datetime | None = None
    visibility_default: bool = True
    pending_count: int = 0
    withheld_count: int = 0
    unresolved_count: int = 0
    students_included: int = 0
    dataset_snapshot: dict = Field(default_factory=dict)
    created_by: PydanticObjectId | None = None
    approved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_result_publications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("publication_id", ASCENDING)],
                unique=True,
                name="unique_exam_result_publication",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("exam_session_id", ASCENDING), ("version", DESCENDING)],
                name="exam_publications_by_session",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING), ("publish_at", ASCENDING)],
                name="exam_publications_scheduled",
            ),
        ]


class ExamPublicationBatch(Document):
    tenant_id: PydanticObjectId
    batch_id: str
    publication_id: str
    exam_session_id: PydanticObjectId
    student_count: int = 0
    status: ExamPublicationStatus = ExamPublicationStatus.DRAFT
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_publication_batches"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("batch_id", ASCENDING)],
                unique=True,
                name="unique_exam_publication_batch",
            ),
            IndexModel([("tenant_id", ASCENDING), ("publication_id", ASCENDING)], name="exam_batches_by_publication"),
        ]


class ExamPublicationHistory(Document):
    tenant_id: PydanticObjectId
    history_id: str
    publication_id: str
    exam_session_id: PydanticObjectId
    action: ExamPublicationHistoryAction
    actor_id: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=2000)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_publication_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("history_id", ASCENDING)],
                unique=True,
                name="unique_exam_publication_history",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("publication_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_publication_history_timeline",
            ),
        ]


class ExamStudentResultVisibility(Document):
    tenant_id: PydanticObjectId
    visibility_id: str
    publication_id: str
    exam_session_id: PydanticObjectId
    student_user_id: PydanticObjectId
    visible: bool = True
    withheld: bool = False
    released_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_student_result_visibility"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("visibility_id", ASCENDING)],
                unique=True,
                name="unique_exam_student_result_visibility",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("publication_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                ],
                unique=True,
                name="unique_visibility_per_student_publication",
            ),
        ]


class ExamTranscript(Document):
    tenant_id: PydanticObjectId
    transcript_id: str
    student_user_id: PydanticObjectId
    publication_id: str | None = None
    document_id: str
    programme_code: str | None = None
    cgpa: float | None = None
    includes_arrear: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_transcripts"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("transcript_id", ASCENDING)],
                unique=True,
                name="unique_exam_transcript",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="exam_transcripts_by_student",
            ),
        ]


class ExamAcademicStatement(Document):
    tenant_id: PydanticObjectId
    statement_id: str
    student_user_id: PydanticObjectId
    publication_id: str | None = None
    document_id: str
    course_code: str
    exam_session_id: PydanticObjectId | None = None
    is_provisional: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_academic_statements"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("statement_id", ASCENDING)],
                unique=True,
                name="unique_exam_academic_statement",
            ),
        ]


class ExamResultDocument(Document):
    tenant_id: PydanticObjectId
    document_id: str
    document_type: ExamResultDocumentType
    publication_id: str
    exam_session_id: PydanticObjectId
    student_user_id: PydanticObjectId
    version: int = Field(default=1, ge=1)
    storage_key: str
    checksum: str
    verification_code: str
    file_name: str
    generated_at: datetime = Field(default_factory=utcnow)
    generated_by: PydanticObjectId | None = None

    class Settings:
        name = "exam_result_documents"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("document_id", ASCENDING)],
                unique=True,
                name="unique_exam_result_document",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("document_type", ASCENDING),
                    ("publication_id", ASCENDING),
                ],
                name="exam_documents_lookup",
            ),
        ]


class ExamDocumentVerificationRecord(Document):
    tenant_id: PydanticObjectId
    record_id: str
    document_id: str
    verification_code: str
    verified: bool
    actor_id: PydanticObjectId | None = None
    client_ip: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "exam_document_verification_records"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("record_id", ASCENDING)],
                unique=True,
                name="unique_exam_document_verification",
            ),
        ]