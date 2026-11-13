"""College admin library administration collections."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class LibraryBranch(Document):
    tenant_id: PydanticObjectId
    branch_code: str
    name: str = Field(max_length=200)
    campus_id: PydanticObjectId | None = None
    address: str | None = Field(default=None, max_length=500)
    is_active: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_branches"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("branch_code", ASCENDING)], unique=True, name="unique_library_branch"),
        ]


class LibraryCatalogueEntry(Document):
    """Admin catalogue row; authoritative copy metadata in `library_catalog_items`."""

    tenant_id: PydanticObjectId
    book_id: str
    branch_code: str | None = None
    accession_prefix: str | None = None
    catalog_item_id: PydanticObjectId | None = None
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_catalogue"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("book_id", ASCENDING)], unique=True, name="unique_library_catalogue_entry"),
        ]


class LibraryBookCopyRecord(Document):
    tenant_id: PydanticObjectId
    copy_id: str
    book_id: str
    barcode: str
    accession_number: str | None = None
    branch_code: str | None = None
    authoritative_copy_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_book_copies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("copy_id", ASCENDING)], unique=True, name="unique_admin_library_copy"),
            IndexModel(
                [("tenant_id", ASCENDING), ("accession_number", ASCENDING)],
                unique=True,
                name="unique_accession_per_tenant",
                partialFilterExpression={"accession_number": {"$type": "string"}},
            ),
        ]


class LibraryMembershipReference(Document):
    tenant_id: PydanticObjectId
    member_user_id: PydanticObjectId
    member_type: str = "student"
    branch_code: str | None = None
    eligible: bool = True
    borrowing_limit: int = Field(default=5, ge=0)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_membership_references"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("member_user_id", ASCENDING)], unique=True, name="unique_library_member"),
        ]


class LibraryBorrowingPolicy(Document):
    tenant_id: PydanticObjectId
    branch_code: str | None = None
    max_books: int = Field(default=5, ge=0)
    loan_days: int = Field(default=14, ge=1)
    renewal_limit: int = Field(default=2, ge=0)
    fine_per_day: float = Field(default=5.0, ge=0)
    version: int = 1
    updated_by: PydanticObjectId | None = None
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_borrowing_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("branch_code", ASCENDING)], name="borrowing_policy_by_branch"),
        ]


class LibraryCirculationRecord(Document):
    """Admin audit overlay; circulation truth is `library_circulations`."""

    tenant_id: PydanticObjectId
    circulation_id: str
    branch_code: str | None = None
    action: str
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_circulation_records"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("circulation_id", ASCENDING), ("created_at", DESCENDING)], name="circulation_audit"),
        ]


class LibraryAcquisition(Document):
    tenant_id: PydanticObjectId
    acquisition_id: str
    branch_code: str | None = None
    vendor: str | None = None
    book_id: str | None = None
    quantity: int = Field(default=1, ge=1)
    status: str = "ordered"
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_acquisitions"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("acquisition_id", ASCENDING)], unique=True, name="unique_acquisition"),
        ]


class LibraryInventoryHistory(Document):
    tenant_id: PydanticObjectId
    branch_code: str | None = None
    copy_id: str | None = None
    event_type: str
    note: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_inventory_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="inventory_history_recent"),
        ]
