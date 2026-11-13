"""Faculty personal documents and report exports."""

from datetime import datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class FacultyPersonalDocument(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    label: str = Field(max_length=200)
    storage_key: str
    mime_type: str
    file_name: str
    document_type: str = "personal"
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_personal_documents"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="personal_docs_by_faculty",
            ),
        ]


class FacultyReportExport(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    report_type: str
    status: str = "ready"
    storage_key: str | None = None
    payload: dict = Field(default_factory=dict)
    download_token_hash: str | None = None
    expires_at: datetime | None = None
    generated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_report_exports"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("generated_at", DESCENDING)],
                name="report_exports_by_faculty",
            ),
        ]


class FacultyDocumentAccessLog(Document):
    tenant_id: PydanticObjectId
    faculty_user_id: PydanticObjectId
    document_id: str
    document_type: str
    action: str
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "faculty_document_access_logs"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("faculty_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="doc_access_logs",
            ),
        ]
