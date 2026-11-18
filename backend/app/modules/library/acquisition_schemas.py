"""Acquisition API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.library.acquisition_enums import LibraryAcquisitionStatus, LibraryAcquisitionType


class AcquisitionCreateRequest(BaseModel):
    acquisition_id: str | None = None
    request_type: LibraryAcquisitionType = LibraryAcquisitionType.PURCHASE
    title: str = Field(min_length=2, max_length=300)
    isbn: str | None = None
    book_id: str | None = None
    branch_code: str | None = None
    vendor_id: str | None = None
    quantity: int = Field(default=1, ge=1)


class QuotationCreateRequest(BaseModel):
    quotation_id: str | None = None
    vendor_id: str
    amount: float = Field(ge=0)
    valid_until: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class ReceiptRecordRequest(BaseModel):
    receipt_id: str | None = None
    quantity: int = Field(ge=1)
    notes: str | None = Field(default=None, max_length=500)


class CatalogueLinkRequest(BaseModel):
    book_id: str


class ProcurementSyncRequest(BaseModel):
    purchase_request_id: str
    purchase_order_id: str | None = None


class AcquisitionApprovalDecision(BaseModel):
    approved: bool
    note: str | None = Field(default=None, max_length=500)


class AcquisitionRead(BaseModel):
    acquisition_id: str
    request_type: LibraryAcquisitionType
    title: str
    isbn: str | None = None
    book_id: str | None = None
    branch_code: str | None = None
    vendor_id: str | None = None
    quantity: int
    quantity_received: int
    status: str
    approval_status: str
    purchase_request_id: str | None = None
    purchase_order_id: str | None = None
    selected_quotation_id: str | None = None
    created_at: datetime
    updated_at: datetime


class AcquisitionHistoryEntry(BaseModel):
    action: str
    actor_id: str | None = None
    changes: dict
    created_at: datetime