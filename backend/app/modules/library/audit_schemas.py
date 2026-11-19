"""Library audit and inventory-control API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.library.audit_enums import (
    LibraryAuditDomain,
    StockAdjustmentRequestStatus,
    StockDiscrepancyKind,
    StockDiscrepancyStatus,
)
from app.modules.library.inventory_enums import InventoryAdjustmentType
from app.modules.library.library_enums import LibraryCopyCondition, LibraryCopyStatus


class LibraryAuditEventRead(BaseModel):
    event_id: str
    domain: LibraryAuditDomain
    action: str
    resource_type: str
    resource_id: str | None
    branch_code: str | None
    actor_id: str | None
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime


class LibraryAuditSearch(BaseModel):
    domain: LibraryAuditDomain | None = None
    branch_code: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    actor_id: str | None = None
    action_prefix: str | None = None


class LibraryAuditTimelineItem(BaseModel):
    source: str
    event_type: str
    resource_id: str | None = None
    summary: str
    actor_id: str | None = None
    branch_code: str | None = None
    before_state: dict[str, Any] = Field(default_factory=dict)
    after_state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class LibraryAuditReportRead(BaseModel):
    generated_at: datetime
    branch_code: str | None
    domains: list[str]
    event_count: int
    open_discrepancies: int
    pending_adjustments: int
    sample_events: list[LibraryAuditEventRead]


class StockDiscrepancyRead(BaseModel):
    discrepancy_id: str
    verification_id: str
    branch_code: str
    copy_id: str | None
    kind: StockDiscrepancyKind
    status: StockDiscrepancyStatus
    note: str | None
    resolution_note: str | None
    created_at: datetime
    resolved_at: datetime | None


class StockDiscrepancyResolve(BaseModel):
    resolution: StockDiscrepancyStatus = Field(description="resolved or dismissed")
    resolution_note: str = Field(min_length=2, max_length=1000)


class StockAdjustmentPropose(BaseModel):
    copy_id: str
    discrepancy_id: str | None = None
    adjustment_type: InventoryAdjustmentType
    proposed_status: LibraryCopyStatus | None = None
    proposed_condition: LibraryCopyCondition | None = None
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=500)


class StockAdjustmentDecision(BaseModel):
    decision_note: str | None = Field(default=None, max_length=500)


class StockAdjustmentRequestRead(BaseModel):
    request_id: str
    discrepancy_id: str | None
    copy_id: str
    branch_code: str
    adjustment_type: InventoryAdjustmentType
    proposed_status: LibraryCopyStatus | None
    proposed_condition: LibraryCopyCondition | None
    expected_version: int
    reason: str
    status: StockAdjustmentRequestStatus
    adjustment_id: str | None
    requested_by: str | None
    decided_by: str | None
    created_at: datetime
    decided_at: datetime | None
    applied_at: datetime | None