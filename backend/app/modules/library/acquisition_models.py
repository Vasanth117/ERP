"""Acquisition quotations, receipts, history and inventory registration."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class LibraryAcquisitionQuotation(Document):
    tenant_id: PydanticObjectId
    quotation_id: str
    acquisition_id: str
    vendor_id: str
    amount: float = Field(ge=0)
    currency: str = "INR"
    valid_until: date | None = None
    selected: bool = False
    notes: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId | None = None

    class Settings:
        name = "library_acquisition_quotations"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("quotation_id", ASCENDING)], unique=True, name="unique_acquisition_quote"),
            IndexModel([("tenant_id", ASCENDING), ("acquisition_id", ASCENDING)], name="quotes_by_acquisition"),
        ]


class LibraryAcquisitionReceipt(Document):
    tenant_id: PydanticObjectId
    receipt_id: str
    acquisition_id: str
    quantity: int = Field(ge=1)
    received_at: datetime = Field(default_factory=utcnow)
    verified_by: PydanticObjectId | None = None
    notes: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_acquisition_receipts"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("receipt_id", ASCENDING)], unique=True, name="unique_acquisition_receipt"),
            IndexModel([("tenant_id", ASCENDING), ("acquisition_id", ASCENDING), ("received_at", DESCENDING)], name="receipts_by_acquisition"),
        ]


class LibraryAcquisitionHistory(Document):
    tenant_id: PydanticObjectId
    acquisition_id: str
    action: str
    actor_id: PydanticObjectId | None = None
    changes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_acquisition_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("acquisition_id", ASCENDING), ("created_at", DESCENDING)],
                name="acquisition_history_by_id",
            ),
        ]


class LibraryInventoryRegistrationRequest(Document):
    tenant_id: PydanticObjectId
    registration_id: str
    acquisition_id: str
    book_id: str
    branch_code: str | None = None
    quantity_expected: int = Field(ge=1)
    quantity_registered: int = Field(default=0, ge=0)
    status: str = "pending"
    created_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId | None = None

    class Settings:
        name = "library_inventory_registration_requests"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("registration_id", ASCENDING)], unique=True, name="unique_reg_request"),
            IndexModel([("tenant_id", ASCENDING), ("acquisition_id", ASCENDING)], name="reg_by_acquisition"),
        ]