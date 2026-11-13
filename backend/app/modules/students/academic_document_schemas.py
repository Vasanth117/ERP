"""Academic document API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class AcademicDocumentSummaryRead(BaseModel):
    document_id: str
    document_type: str
    title: str
    season_id: str | None = None
    academic_year_label: str | None = None
    semester_label: str | None = None
    version: str
    status: str
    gpa: float | None = None
    cgpa: float | None = None
    published_at: datetime | None = None
    is_reissue: bool = False


class AcademicDocumentDownloadRead(BaseModel):
    document_id: str
    document_type: str
    download_token: str
    content_type: str = "application/pdf"
    expires_at: datetime


class AcademicDocumentRequestCreate(BaseModel):
    request_type: str
    season_id: str | None = None
    reason: str | None = Field(default=None, max_length=1000)

    model_config = {"extra": "forbid"}


class AcademicDocumentRequestRead(BaseModel):
    request_id: str
    request_type: str
    season_id: str | None = None
    status: str
    reason: str | None = None
    fulfilled_document_id: str | None = None
    created_at: datetime
    updated_at: datetime


class AcademicDocumentHistoryRead(BaseModel):
    document_id: str
    document_type: str
    title: str
    version: str
    published_at: datetime | None = None
    downloaded_at: datetime | None = None
