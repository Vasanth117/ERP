"""Fine policy, approvals and history."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.library.fine_enums import LibraryFineApprovalStatus, LibraryFineApprovalType


class LibraryFinePolicy(Document):
    tenant_id: PydanticObjectId
    branch_code: str | None = None
    fine_per_day: float = Field(default=5.0, ge=0)
    grace_days: int = Field(default=0, ge=0)
    max_overdue_days: int | None = Field(default=90, ge=1)
    lost_book_charge: float = Field(default=500.0, ge=0)
    damaged_book_charge: float = Field(default=150.0, ge=0)
    replacement_charge: float = Field(default=500.0, ge=0)
    updated_at: datetime = Field(default_factory=utcnow)
    updated_by: PydanticObjectId | None = None

    class Settings:
        name = "library_fine_policies"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("branch_code", ASCENDING)], unique=True, name="unique_fine_policy"),
        ]


class LibraryFineApproval(Document):
    tenant_id: PydanticObjectId
    approval_id: str
    fine_id: str
    approval_type: LibraryFineApprovalType
    status: LibraryFineApprovalStatus = LibraryFineApprovalStatus.PENDING
    reason: str = Field(max_length=500)
    requested_by: PydanticObjectId
    decided_by: PydanticObjectId | None = None
    decision_note: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utcnow)
    decided_at: datetime | None = None

    class Settings:
        name = "library_fine_approvals"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("approval_id", ASCENDING)], unique=True, name="unique_fine_approval"),
            IndexModel([("tenant_id", ASCENDING), ("fine_id", ASCENDING), ("status", ASCENDING)], name="fine_approval_by_fine"),
        ]


class LibraryFineHistory(Document):
    tenant_id: PydanticObjectId
    fine_id: str
    action: str
    actor_id: PydanticObjectId | None = None
    changes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_fine_history"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("fine_id", ASCENDING), ("created_at", DESCENDING)], name="fine_history_by_id"),
        ]


class LibraryDamageReport(Document):
    tenant_id: PydanticObjectId
    report_id: str
    fine_id: str | None = None
    circulation_id: str | None = None
    copy_id: str
    book_id: str
    branch_code: str | None = None
    member_user_id: PydanticObjectId
    report_type: str
    description: str = Field(max_length=2000)
    replacement_cost: float = Field(default=0, ge=0)
    recovery_status: str = "open"
    created_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId | None = None

    class Settings:
        name = "library_damage_reports"
        indexes = [
            IndexModel([("tenant_id", ASCENDING), ("report_id", ASCENDING)], unique=True, name="unique_damage_report"),
            IndexModel([("tenant_id", ASCENDING), ("copy_id", ASCENDING), ("created_at", DESCENDING)], name="damage_by_copy"),
        ]