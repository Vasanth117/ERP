"""Versioned library borrowing and related policy rules."""

from datetime import date, datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class LibraryBorrowingRule(Document):
    tenant_id: PydanticObjectId
    policy_id: str
    version: int = 1
    policy_type: str = "borrowing"
    branch_code: str | None = None
    member_category: str | None = None
    resource_type: str = "any"
    status: str = "draft"
    effective_from: date
    effective_until: date | None = None
    max_books: int = Field(default=5, ge=0)
    loan_days: int = Field(default=14, ge=1)
    renewal_limit: int = Field(default=2, ge=0)
    fine_per_day: float = Field(default=5.0, ge=0)
    grace_days: int = Field(default=0, ge=0)
    max_overdue_days: int | None = Field(default=90, ge=1)
    max_reservations_per_member: int = Field(default=5, ge=1)
    hold_hours: int = Field(default=72, ge=1, le=168)
    reserve_only_when_unavailable: bool = True
    lost_book_charge: float = Field(default=500.0, ge=0)
    damaged_book_charge: float = Field(default=150.0, ge=0)
    eligibility_restrictions: list[str] = Field(default_factory=list)
    borrowing_restrictions: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    notes: str | None = Field(default=None, max_length=2000)
    created_by: PydanticObjectId | None = None
    updated_by: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_borrowing_rules"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_id", ASCENDING), ("version", ASCENDING)],
                unique=True,
                name="unique_library_policy_version",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("status", ASCENDING), ("effective_from", ASCENDING)],
                name="library_policy_active_lookup",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("branch_code", ASCENDING), ("member_category", ASCENDING), ("resource_type", ASCENDING)],
                name="library_policy_scope",
            ),
        ]


class LibraryPolicyHistory(Document):
    tenant_id: PydanticObjectId
    policy_id: str
    policy_type: str
    version: int
    action: str
    actor_id: PydanticObjectId | None = None
    changes: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "library_policy_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("policy_id", ASCENDING), ("created_at", DESCENDING)],
                name="library_policy_history_by_policy",
            ),
        ]