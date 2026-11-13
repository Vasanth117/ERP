"""Central library collections (authoritative)."""

from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.library.library_enums import (
    LibraryCirculationStatus,
    LibraryCopyStatus,
    LibraryFineStatus,
    LibraryReservationStatus,
)


class LibraryCatalogItem(Document):
    tenant_id: PydanticObjectId
    book_id: str
    isbn: str | None = None
    title: str = Field(max_length=300)
    authors: list[str] = Field(default_factory=list)
    category: str | None = Field(default=None, max_length=120)
    edition: str | None = None
    published: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

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
        ]


class LibraryCopy(Document):
    tenant_id: PydanticObjectId
    copy_id: str
    book_id: str
    barcode: str
    status: LibraryCopyStatus = LibraryCopyStatus.AVAILABLE
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_copies"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("copy_id", ASCENDING)],
                unique=True,
                name="unique_library_copy",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("book_id", ASCENDING), ("status", ASCENDING)],
                name="library_copies_by_book",
            ),
        ]


class LibraryCirculation(Document):
    tenant_id: PydanticObjectId
    circulation_id: str
    student_user_id: PydanticObjectId
    book_id: str
    copy_id: str
    title: str
    issued_at: datetime
    due_at: date
    returned_at: datetime | None = None
    status: LibraryCirculationStatus = LibraryCirculationStatus.ACTIVE
    created_at: datetime = Field(default_factory=utcnow)

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
        ]


class LibraryReservation(Document):
    tenant_id: PydanticObjectId
    reservation_id: str
    student_user_id: PydanticObjectId
    book_id: str
    title: str
    status: LibraryReservationStatus = LibraryReservationStatus.QUEUED
    queue_position: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utcnow)

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
        ]


class LibraryFine(Document):
    tenant_id: PydanticObjectId
    fine_id: str
    student_user_id: PydanticObjectId
    circulation_id: str | None = None
    amount: float = Field(ge=0)
    reason: str = Field(max_length=500)
    status: LibraryFineStatus = LibraryFineStatus.OPEN
    created_at: datetime = Field(default_factory=utcnow)

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
        ]


class LibraryDigitalResource(Document):
    tenant_id: PydanticObjectId
    resource_id: str
    title: str = Field(max_length=300)
    description: str | None = Field(default=None, max_length=2000)
    url: str | None = None
    storage_key: str | None = None
    mime_type: str = "application/pdf"
    published: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_digital_resources"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("resource_id", ASCENDING)],
                unique=True,
                name="unique_digital_resource",
            ),
        ]
