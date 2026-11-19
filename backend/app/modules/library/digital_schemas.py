"""Digital library API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.modules.library.digital_enums import DigitalAvailabilityStatus, DigitalResourceType


class DigitalResourceCreate(BaseModel):
    resource_id: str | None = Field(default=None, max_length=64)
    resource_type: DigitalResourceType = DigitalResourceType.EBOOK
    title: str = Field(min_length=1, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=120)
    subcategory: str | None = Field(default=None, max_length=120)
    authors: list[str] = Field(default_factory=list, max_length=30)
    keywords: list[str] = Field(default_factory=list, max_length=50)
    book_id: str | None = Field(default=None, max_length=64)
    external_url: str | None = Field(default=None, max_length=2000)
    license_type: str | None = Field(default=None, max_length=64)
    license_expires_at: datetime | None = None
    max_downloads: int | None = Field(default=None, ge=1)
    max_downloads_per_user: int | None = Field(default=None, ge=1)
    allow_download: bool = True
    allow_external_link: bool = True
    requires_membership: bool = True
    eligibility_member_categories: list[str] = Field(default_factory=list, max_length=20)
    published: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class DigitalResourceUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = None
    subcategory: str | None = None
    authors: list[str] | None = None
    keywords: list[str] | None = None
    book_id: str | None = None
    external_url: str | None = None
    license_type: str | None = None
    license_expires_at: datetime | None = None
    max_downloads: int | None = Field(default=None, ge=1)
    max_downloads_per_user: int | None = Field(default=None, ge=1)
    allow_download: bool | None = None
    allow_external_link: bool | None = None
    requires_membership: bool | None = None
    eligibility_member_categories: list[str] | None = None
    availability_status: DigitalAvailabilityStatus | None = None
    published: bool | None = None
    metadata: dict[str, Any] | None = None


class DigitalFileUpload(BaseModel):
    file_name: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=3, max_length=120)
    file_content_base64: str = Field(min_length=4)

    @field_validator("file_content_base64")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        return value.strip()


class DigitalResourceRead(BaseModel):
    resource_id: str
    resource_type: DigitalResourceType
    title: str
    description: str | None
    category: str | None
    subcategory: str | None
    authors: list[str]
    keywords: list[str]
    book_id: str | None
    has_file: bool
    has_external_link: bool
    mime_type: str
    published: bool
    availability_status: DigitalAvailabilityStatus
    license_type: str | None
    license_expires_at: datetime | None
    license_valid: bool
    allow_download: bool
    allow_external_link: bool
    requires_membership: bool
    eligibility_member_categories: list[str]
    download_count: int
    created_at: datetime
    updated_at: datetime


class DigitalResourcePatronRead(BaseModel):
    resource_id: str
    resource_type: DigitalResourceType
    title: str
    description: str | None
    category: str | None
    book_id: str | None
    allow_download: bool
    allow_external_link: bool
    has_file: bool


class DigitalDownloadRead(BaseModel):
    resource_id: str
    file_name: str
    content_type: str
    content_base64: str
    checksum: str | None


class DigitalExternalLinkRead(BaseModel):
    resource_id: str
    url: str


class DigitalAccessLogEntry(BaseModel):
    user_id: str
    action: str
    created_at: datetime
    metadata: dict[str, Any]