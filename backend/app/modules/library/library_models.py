"""Central library collections (authoritative)."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.library.library_enums import (
    LibraryCirculationStatus,
    LibraryCopyCondition,
    LibraryCopyStatus,
    LibraryFineStatus,
    LibraryReservationStatus,
)


class LibraryCatalogItem(Document):
    """Authoritative catalogue title (physical copies live in `library_copies`)."""

    tenant_id: PydanticObjectId
    book_id: str
    isbn: str | None = Field(default=None, max_length=20)
    isbn13: str | None = Field(default=None, max_length=17)
    title: str = Field(max_length=300)
    subtitle: str | None = Field(default=None, max_length=300)
    authors: list[str] = Field(default_factory=list)
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
    keywords: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    description: str | None = Field(default=None, max_length=8000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    cover_storage_key: str | None = Field(default=None, max_length=512)
    cover_url: str | None = Field(default=None, max_length=2048)
    primary_library_code: str | None = Field(default=None, max_length=32)
    archived: bool = False
    published: bool = True
    created_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_catalog_items"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("book_id", ASCENDING)],
                unique=True,
                name="unique_library_book",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("title", ASCENDING)],
                name="library_catalog_title",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("isbn", ASCENDING)],
                unique=True,
                name="unique_catalog_isbn10",
                partialFilterExpression={"isbn": {"$type": "string"}},
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("isbn13", ASCENDING)],
                unique=True,
                name="unique_catalog_isbn13",
                partialFilterExpression={"isbn13": {"$type": "string"}},
            ),
            IndexModel([("tenant_id", ASCENDING), ("category", ASCENDING), ("subcategory", ASCENDING)], name="catalog_category"),
            IndexModel([("tenant_id", ASCENDING), ("archived", ASCENDING), ("updated_at", DESCENDING)], name="catalog_active_recent"),
            IndexModel([("tenant_id", ASCENDING), ("primary_library_code", ASCENDING)], name="catalog_by_library"),
        ]


class LibraryCatalogHistory(Document):
    tenant_id: PydanticObjectId
    book_id: str
    action: str
    actor_id: PydanticObjectId | None = None
    snapshot: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_catalog_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("book_id", ASCENDING), ("created_at", DESCENDING)],
                name="catalog_history_by_book",
            ),
        ]


class LibraryCopy(Document):
    tenant_id: PydanticObjectId
    copy_id: str
    book_id: str
    barcode: str
    branch_code: str | None = None
    shelf_location_code: str | None = None
    condition: LibraryCopyCondition = LibraryCopyCondition.GOOD
    status: LibraryCopyStatus = LibraryCopyStatus.AVAILABLE
    reserved_reservation_id: str | None = Field(default=None, max_length=64)
    notes: str | None = Field(default=None, max_length=1000)
    version: int = 1
    created_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_copies"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("copy_id", ASCENDING)],
                unique=True,
                name="unique_library_copy",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("barcode", ASCENDING)],
                unique=True,
                name="unique_copy_barcode",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("book_id", ASCENDING), ("status", ASCENDING)],
                name="library_copies_by_book",
            ),
            IndexModel([("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("status", ASCENDING)], name="library_copies_by_branch"),
        ]


class LibraryCirculation(Document):
    tenant_id: PydanticObjectId
    circulation_id: str
    student_user_id: PydanticObjectId
    book_id: str
    copy_id: str
    branch_code: str | None = None
    membership_number: str | None = None
    title: str
    issued_at: datetime
    due_at: date
    returned_at: datetime | None = None
    status: LibraryCirculationStatus = LibraryCirculationStatus.ACTIVE
    renewal_count: int = Field(default=0, ge=0)
    return_disposition: str | None = Field(default=None, max_length=32)
    applied_policy_id: str | None = None
    applied_policy_version: int | None = None
    applied_policy_snapshot: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_circulations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("circulation_id", ASCENDING)],
                unique=True,
                name="unique_circulation",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)],
                name="circulation_by_student",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("copy_id", ASCENDING)],
                unique=True,
                name="unique_active_loan_per_copy",
                partialFilterExpression={"status": {"$in": ["active", "overdue"]}},
            ),
            IndexModel([("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("status", ASCENDING)], name="circulation_by_branch"),
            IndexModel([("tenant_id", ASCENDING), ("issued_at", DESCENDING)], name="circulation_issued_at"),
            IndexModel(
                [("tenant_id", ASCENDING), ("returned_at", DESCENDING)],
                name="circulation_returned_at",
                partialFilterExpression={"returned_at": {"$type": "date"}},
            ),
            IndexModel([("tenant_id", ASCENDING), ("due_at", ASCENDING), ("status", ASCENDING)], name="circulation_due_status"),
        ]


class LibraryReservation(Document):
    tenant_id: PydanticObjectId
    reservation_id: str
    student_user_id: PydanticObjectId
    membership_number: str | None = None
    book_id: str
    title: str
    branch_code: str | None = None
    copy_id: str | None = None
    status: LibraryReservationStatus = LibraryReservationStatus.QUEUED
    queue_position: int = Field(default=1, ge=1)
    priority: int = Field(default=0, ge=0)
    ready_at: datetime | None = None
    expires_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancel_reason: str | None = Field(default=None, max_length=500)
    notification_sent_at: datetime | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_reservations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("reservation_id", ASCENDING)],
                unique=True,
                name="unique_library_reservation",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)],
                name="reservations_by_student",
            ),
            IndexModel([("tenant_id", ASCENDING), ("status", ASCENDING)], name="reservations_by_status"),
            IndexModel(
                [("tenant_id", ASCENDING), ("book_id", ASCENDING), ("branch_code", ASCENDING), ("status", ASCENDING), ("priority", DESCENDING), ("created_at", ASCENDING)],
                name="reservation_queue_fifo",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("copy_id", ASCENDING)],
                unique=True,
                name="unique_ready_reservation_per_copy",
                partialFilterExpression={"status": "ready", "copy_id": {"$type": "string"}},
            ),
            IndexModel([("tenant_id", ASCENDING), ("expires_at", ASCENDING), ("status", ASCENDING)], name="reservation_expiry"),
        ]


class LibraryFine(Document):
    tenant_id: PydanticObjectId
    fine_id: str
    student_user_id: PydanticObjectId
    circulation_id: str | None = None
    book_id: str | None = None
    copy_id: str | None = None
    branch_code: str | None = None
    fine_type: str = "overdue"
    amount: float = Field(ge=0)
    amount_waived: float = Field(default=0, ge=0)
    amount_paid: float = Field(default=0, ge=0)
    balance: float = Field(ge=0)
    reason: str = Field(max_length=500)
    recovery_status: str = "open"
    status: LibraryFineStatus = LibraryFineStatus.OPEN
    demand_id: str | None = None
    payment_transaction_id: str | None = None
    approval_id: str | None = None
    assessed_at: datetime = Field(default_factory=utcnow)
    due_date: date | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId | None = None
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_fines"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("fine_id", ASCENDING)],
                unique=True,
                name="unique_library_fine",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("status", ASCENDING)],
                name="fines_by_student",
            ),
            IndexModel([("tenant_id", ASCENDING), ("circulation_id", ASCENDING)], name="fines_by_circulation"),
            IndexModel([("tenant_id", ASCENDING), ("demand_id", ASCENDING)], name="fines_by_demand"),
            IndexModel([("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("status", ASCENDING)], name="fines_by_branch"),
        ]


class LibraryDigitalResource(Document):
    tenant_id: PydanticObjectId
    resource_id: str
    resource_type: str = "ebook"
    title: str = Field(max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    category: str | None = Field(default=None, max_length=120)
    subcategory: str | None = Field(default=None, max_length=120)
    authors: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    book_id: str | None = Field(default=None, max_length=64)
    url: str | None = None
    storage_key: str | None = None
    file_name: str | None = None
    checksum: str | None = None
    file_size_bytes: int | None = None
    mime_type: str = "application/pdf"
    published: bool = False
    availability_status: str = "available"
    license_type: str | None = Field(default=None, max_length=64)
    license_expires_at: datetime | None = None
    max_downloads: int | None = Field(default=None, ge=1)
    max_downloads_per_user: int | None = Field(default=None, ge=1)
    download_count: int = 0
    allow_download: bool = True
    allow_external_link: bool = True
    requires_membership: bool = True
    eligibility_member_categories: list[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_digital_resources"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("resource_id", ASCENDING)],
                unique=True,
                name="unique_digital_resource",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("published", ASCENDING), ("availability_status", ASCENDING)],
                name="digital_published_availability",
            ),
            IndexModel([("tenant_id", ASCENDING), ("category", ASCENDING)], name="digital_by_category"),
            IndexModel([("tenant_id", ASCENDING), ("book_id", ASCENDING)], name="digital_by_book"),
            IndexModel([("tenant_id", ASCENDING), ("resource_type", ASCENDING)], name="digital_by_type"),
        ]
