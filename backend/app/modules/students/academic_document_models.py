"""Student academic document references, requests, and download audit."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.students.academic_grading_enums import (
    AcademicDocumentRequestStatus,
    AcademicDocumentRequestType,
)


class StudentMarksheetReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    document_id: str
    season_id: str | None = None
    last_viewed_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_marksheet_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("document_id", ASCENDING)],
                unique=True,
                name="unique_marksheet_ref",
            ),
        ]


class StudentGradeCardReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    document_id: str
    season_id: str
    last_viewed_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_grade_card_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("season_id", ASCENDING)],
                unique=True,
                name="unique_grade_card_ref",
            ),
        ]


class StudentTranscriptReference(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    document_id: str
    last_viewed_at: datetime | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_transcript_references"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING)],
                unique=True,
                name="unique_transcript_ref",
            ),
        ]


class StudentAcademicDocumentRequest(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    request_id: str
    request_type: AcademicDocumentRequestType
    season_id: str | None = None
    reason: str | None = Field(default=None, max_length=1000)
    status: AcademicDocumentRequestStatus = AcademicDocumentRequestStatus.SUBMITTED
    fulfilled_document_id: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_academic_document_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_document_request_id",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("created_at", DESCENDING)],
                name="document_requests_by_student",
            ),
        ]


class StudentDocumentDownloadLog(Document):
    tenant_id: PydanticObjectId
    user_id: PydanticObjectId
    document_id: str
    document_type: str
    ip_address: str | None = None
    user_agent: str | None = None
    downloaded_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "student_document_download_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("user_id", ASCENDING), ("downloaded_at", DESCENDING)],
                name="student_doc_downloads",
            ),
        ]
