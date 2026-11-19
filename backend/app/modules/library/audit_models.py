"""Immutable library audit trail and inventory discrepancy collections."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.library.audit_enums import (
    LibraryAuditDomain,
    StockAdjustmentRequestStatus,
    StockDiscrepancyKind,
    StockDiscrepancyStatus,
)
from app.modules.library.inventory_enums import InventoryAdjustmentType
from app.modules.library.library_enums import LibraryCopyCondition, LibraryCopyStatus


class LibraryAuditEvent(Document):
    """Append-only library audit with before/after deltas (no update/delete APIs)."""

    tenant_id: PydanticObjectId
    event_id: str
    domain: LibraryAuditDomain
    action: str
    resource_type: str
    resource_id: str | None = None
    branch_code: str | None = None
    actor_id: PydanticObjectId | None = None
    before_state: dict[str, Any] = Field(default_factory=dict)
    after_state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    institution_audit_hash: str | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_audit_events"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("event_id", ASCENDING)],
                unique=True,
                name="unique_library_audit_event",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("created_at", DESCENDING)],
                name="library_audit_recent",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("domain", ASCENDING), ("created_at", DESCENDING)],
                name="library_audit_by_domain",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("resource_type", ASCENDING), ("resource_id", ASCENDING), ("created_at", DESCENDING)],
                name="library_audit_by_resource",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("created_at", DESCENDING)],
                name="library_audit_by_branch",
            ),
        ]


class LibraryStockDiscrepancy(Document):
    tenant_id: PydanticObjectId
    discrepancy_id: str
    verification_id: str
    branch_code: str
    copy_id: str | None = None
    kind: StockDiscrepancyKind
    status: StockDiscrepancyStatus = StockDiscrepancyStatus.OPEN
    note: str | None = Field(default=None, max_length=1000)
    resolution_note: str | None = Field(default=None, max_length=1000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    reported_by: PydanticObjectId | None = None
    resolved_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    resolved_at: datetime | None = None

    class Settings:
        name = "library_stock_discrepancies"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("discrepancy_id", ASCENDING)],
                unique=True,
                name="unique_stock_discrepancy",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("verification_id", ASCENDING), ("status", ASCENDING)],
                name="discrepancies_by_verification",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("status", ASCENDING)],
                name="discrepancies_by_branch",
            ),
        ]


class LibraryStockAdjustmentRequest(Document):
    """Proposed copy correction after stock audit; apply only after approval."""

    tenant_id: PydanticObjectId
    request_id: str
    discrepancy_id: str | None = None
    copy_id: str
    branch_code: str
    adjustment_type: InventoryAdjustmentType
    proposed_status: LibraryCopyStatus | None = None
    proposed_condition: LibraryCopyCondition | None = None
    expected_version: int = Field(ge=1)
    reason: str = Field(max_length=500)
    status: StockAdjustmentRequestStatus = StockAdjustmentRequestStatus.PENDING
    adjustment_id: str | None = None
    requested_by: PydanticObjectId | None = None
    decided_by: PydanticObjectId | None = None
    decision_note: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)
    decided_at: datetime | None = None
    applied_at: datetime | None = None

    class Settings:
        name = "library_stock_adjustment_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_stock_adjustment_request",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING), ("created_at", DESCENDING)],
                name="stock_adjustment_by_status",
            ),
            IndexModel([("tenant_id", ASCENDING), ("copy_id", ASCENDING)], name="stock_adjustment_by_copy"),
        ]