"""Book copy inventory workflow collections."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.library.inventory_enums import InventoryAdjustmentType, StockVerificationStatus, StockVerificationItemOutcome
from app.modules.library.library_enums import LibraryCopyCondition, LibraryCopyStatus


class LibraryInventoryAdjustment(Document):
    tenant_id: PydanticObjectId
    adjustment_id: str
    copy_id: str
    branch_code: str | None = None
    adjustment_type: InventoryAdjustmentType
    previous_status: LibraryCopyStatus | None = None
    new_status: LibraryCopyStatus | None = None
    previous_condition: LibraryCopyCondition | None = None
    new_condition: LibraryCopyCondition | None = None
    reason: str = Field(max_length=500)
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_inventory_adjustments"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("adjustment_id", ASCENDING)],
                unique=True,
                name="unique_inventory_adjustment",
            ),
            IndexModel([("tenant_id", ASCENDING), ("copy_id", ASCENDING), ("created_at", DESCENDING)], name="adjustments_by_copy"),
        ]


class LibraryStockVerification(Document):
    tenant_id: PydanticObjectId
    verification_id: str
    branch_code: str
    status: StockVerificationStatus = StockVerificationStatus.OPEN
    expected_count: int = 0
    scanned_count: int = 0
    missing_count: int = 0
    unexpected_count: int = 0
    note: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None
    actor_id: PydanticObjectId | None = None

    class Settings:
        name = "library_stock_verifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("verification_id", ASCENDING)],
                unique=True,
                name="unique_stock_verification",
            ),
            IndexModel([("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("status", ASCENDING)], name="verifications_by_branch"),
        ]


class LibraryStockVerificationItem(Document):
    tenant_id: PydanticObjectId
    verification_id: str
    copy_id: str
    outcome: StockVerificationItemOutcome
    scanned_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_stock_verification_items"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("verification_id", ASCENDING), ("copy_id", ASCENDING)],
                unique=True,
                name="unique_verification_item",
            ),
        ]