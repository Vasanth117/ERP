"""Book catalogue API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.modules.library.catalogue_enums import CatalogueSortField, CatalogueSortOrder


class CatalogueAuthorInput(BaseModel):
    authors: list[str] = Field(default_factory=list, max_length=30)

    @field_validator("authors")
    @classmethod
    def strip_authors(cls, value: list[str]) -> list[str]:
        cleaned = [a.strip() for a in value if a and a.strip()]
        if len(cleaned) > 30:
            raise ValueError("Too many authors")
        return cleaned


class CatalogueRecordCreate(CatalogueAuthorInput):
    book_id: str = Field(min_length=2, max_length=64)
    title: str = Field(min_length=1, max_length=300)
    subtitle: str | None = Field(default=None, max_length=300)
    isbn: str | None = None
    isbn13: str | None = None
    publisher: str | None = Field(default=None, max_length=200)
    publication_year: int | None = Field(default=None, ge=0, le=2100)
    publication_place: str | None = Field(default=None, max_length=120)
    edition: str | None = Field(default=None, max_length=64)
    volume: str | None = Field(default=None, max_length=64)
    language: str | None = Field(default=None, max_length=64)
    category: str | None = Field(default=None, max_length=120)
    subcategory: str | None = Field(default=None, max_length=120)
    subject: str | None = Field(default=None, max_length=200)
    academic_classification: str | None = Field(default=None, max_length=64)
    keywords: list[str] = Field(default_factory=list, max_length=50)
    tags: list[str] = Field(default_factory=list, max_length=50)
    description: str | None = Field(default=None, max_length=8000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    cover_storage_key: str | None = None
    cover_url: str | None = None
    primary_library_code: str | None = Field(default=None, max_length=32)
    published: bool = True


class CatalogueRecordUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=300)
    subtitle: str | None = None
    isbn: str | None = None
    isbn13: str | None = None
    authors: list[str] | None = None
    publisher: str | None = None
    publication_year: int | None = Field(default=None, ge=0, le=2100)
    publication_place: str | None = None
    edition: str | None = None
    volume: str | None = None
    language: str | None = None
    category: str | None = None
    subcategory: str | None = None
    subject: str | None = None
    academic_classification: str | None = None
    keywords: list[str] | None = None
    tags: list[str] | None = None
    description: str | None = None
    metadata: dict[str, Any] | None = None
    cover_storage_key: str | None = None
    cover_url: str | None = None
    primary_library_code: str | None = None
    published: bool | None = None


class CatalogueRecordRead(BaseModel):
    book_id: str
    isbn: str | None = None
    isbn13: str | None = None
    title: str
    subtitle: str | None = None
    authors: list[str]
    publisher: str | None = None
    publication_year: int | None = None
    publication_place: str | None = None
    edition: str | None = None
    volume: str | None = None
    language: str | None = None
    category: str | None = None
    subcategory: str | None = None
    subject: str | None = None
    academic_classification: str | None = None
    keywords: list[str]
    tags: list[str]
    description: str | None = None
    metadata: dict[str, Any]
    cover_storage_key: str | None = None
    cover_url: str | None = None
    primary_library_code: str | None = None
    archived: bool
    published: bool
    created_at: datetime
    updated_at: datetime


class CatalogueSearchParams(BaseModel):
    q: str | None = None
    category: str | None = None
    subcategory: str | None = None
    language: str | None = None
    primary_library_code: str | None = None
    include_archived: bool = False
    sort_by: CatalogueSortField = CatalogueSortField.TITLE
    sort_order: CatalogueSortOrder = CatalogueSortOrder.ASC


class CatalogueDuplicateMatch(BaseModel):
    book_id: str
    title: str
    match_reason: str


class CatalogueDuplicateCheckResult(BaseModel):
    duplicates: list[CatalogueDuplicateMatch]


class CatalogueBulkImportRequest(BaseModel):
    items: list[CatalogueRecordCreate] = Field(min_length=1, max_length=500)
    dry_run: bool = False
    update_existing: bool = False


class CatalogueBulkImportError(BaseModel):
    row: int
    book_id: str | None = None
    message: str


class CatalogueBulkImportResult(BaseModel):
    created: int
    updated: int
    skipped: int
    errors: list[CatalogueBulkImportError]
    dry_run: bool


class CatalogueHistoryEntry(BaseModel):
    action: str
    actor_id: str | None = None
    snapshot: dict[str, Any]
    created_at: datetime