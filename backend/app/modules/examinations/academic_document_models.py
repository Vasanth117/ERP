"""Official academic documents (registrar / examination cell publishes)."""

from datetime import datetime
from enum import Enum

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class AcademicDocumentType(str, Enum):
    GRADE_CARD = "grade_card"
    MARKSHEET = "marksheet"
    CONSOLIDATED_MARKSHEET = "consolidated_marksheet"
    TRANSCRIPT = "transcript"
    SEMESTER_STATEMENT = "semester_statement"


class AcademicDocumentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


class AcademicDocumentPublication(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    document_id: str
    document_type: AcademicDocumentType
    season_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    title: str
    version: str = "1.0"
    status: AcademicDocumentStatus = AcademicDocumentStatus.DRAFT
    storage_token: str | None = None
    checksum: str | None = None
    replaces_document_id: str | None = None
    gpa: float | None = None
    cgpa: float | None = None
    credits_earned: float | None = None
    grading_policy_version: str | None = None
    published_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "academic_document_publications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("document_id", ASCENDING)],
                unique=True,
                name="unique_academic_document_id",
            ),
            IndexModel(
                [
                    ("tenant_id", ASCENDING),
                    ("student_user_id", ASCENDING),
                    ("document_type", ASCENDING),
                    ("status", ASCENDING),
                ],
                name="academic_docs_by_student",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("season_id", ASCENDING)],
                name="academic_docs_by_season",
            ),
        ]
