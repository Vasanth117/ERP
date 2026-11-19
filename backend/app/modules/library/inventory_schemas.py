"""Book copy inventory API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.library.inventory_enums import InventoryAdjustmentType, StockVerificationStatus
from app.modules.library.library_enums import LibraryCopyCondition, LibraryCopyStatus


class CopyRegisterRequest(BaseModel):
    book_id: str = Field(min_length=2, max_length=64)
    branch_code: str = Field(min_length=2, max_length=32)
    barcode: str = Field(min_length=4, max_length=64)
    copy_id: str | None = Field(default=None, min_length=2, max_length=64)
    accession_number: str | None = Field(default=None, max_length=64)
    shelf_location_code: str | None = Field(default=None, max_length=64)
    condition: LibraryCopyCondition = LibraryCopyCondition.GOOD
    status: LibraryCopyStatus = LibraryCopyStatus.AVAILABLE
    notes: str | None = Field(default=None, max_length=1000)


class CopyUpdateRequest(BaseModel):
    barcode: str | None = Field(default=None, min_length=4, max_length=64)
    accession_number: str | None = None
    shelf_location_code: str | None = None
    condition: LibraryCopyCondition | None = None
    status: LibraryCopyStatus | None = None
    notes: str | None = None
    expected_version: int | None = Field(default=None, ge=1, description="Optimistic concurrency token")


class CopyTransferRequest(BaseModel):
    to_branch_code: str = Field(min_length=2, max_length=32)
    shelf_location_code: str | None = None
    reason: str = Field(min_length=2, max_length=500)
    expected_version: int = Field(ge=1)


class InventoryAdjustmentRequest(BaseModel):
    copy_id: str
    adjustment_type: InventoryAdjustmentType
    new_status: LibraryCopyStatus | None = None
    new_condition: LibraryCopyCondition | None = None
    reason: str = Field(min_length=2, max_length=500)
    expected_version: int = Field(ge=1)


class CopyInventoryRead(BaseModel):
    copy_id: str
    book_id: str
    barcode: str
    accession_number: str | None = None
    branch_code: str | None = None
    shelf_location_code: str | None = None
    condition: LibraryCopyCondition
    status: LibraryCopyStatus
    notes: str | None = None
    version: int
    created_at: datetime
    updated_at: datetime


class CopyDuplicateMatch(BaseModel):
    field: str
    value: str
    copy_ids: list[str]


class MissingCopySummary(BaseModel):
    copy_id: str
    book_id: str
    branch_code: str | None
    status: LibraryCopyStatus


class StockVerificationCreate(BaseModel):
    verification_id: str = Field(min_length=2, max_length=64)
    branch_code: str
    note: str | None = None


class StockVerificationScan(BaseModel):
    barcode: str | None = None
    copy_id: str | None = None


class StockVerificationRead(BaseModel):
    verification_id: str
    branch_code: str
    status: StockVerificationStatus
    expected_count: int
    scanned_count: int
    missing_count: int
    unexpected_count: int
    created_at: datetime
    completed_at: datetime | None = None


class InventoryHistoryRead(BaseModel):
    event_type: str
    branch_code: str | None = None
    copy_id: str | None = None
    note: str | None = None
    metadata: dict
    actor_id: str | None = None
    created_at: datetime