"""Library settings API schemas."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.library.settings_enums import LibraryPolicyStatus, LibraryResourceType


class BorrowingRuleCreate(BaseModel):
    policy_id: str | None = Field(default=None, max_length=64)
    branch_code: str | None = None
    member_category: str | None = None
    resource_type: LibraryResourceType = LibraryResourceType.ANY
    effective_from: date | None = None
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
    eligibility_restrictions: list[str] = Field(default_factory=list, max_length=20)
    borrowing_restrictions: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    notes: str | None = None


class BorrowingRuleUpdate(BaseModel):
    max_books: int | None = Field(default=None, ge=0)
    loan_days: int | None = Field(default=None, ge=1)
    renewal_limit: int | None = Field(default=None, ge=0)
    fine_per_day: float | None = Field(default=None, ge=0)
    grace_days: int | None = None
    max_overdue_days: int | None = Field(default=None, ge=1)
    max_reservations_per_member: int | None = Field(default=None, ge=1)
    hold_hours: int | None = Field(default=None, ge=1, le=168)
    reserve_only_when_unavailable: bool | None = None
    lost_book_charge: float | None = Field(default=None, ge=0)
    damaged_book_charge: float | None = Field(default=None, ge=0)
    eligibility_restrictions: list[str] | None = None
    borrowing_restrictions: dict[str, Any] | None = None
    effective_until: date | None = None
    notes: str | None = None


class BorrowingRuleRead(BaseModel):
    policy_id: str
    version: int
    branch_code: str | None
    member_category: str | None
    resource_type: str
    status: LibraryPolicyStatus
    effective_from: date
    effective_until: date | None
    max_books: int
    loan_days: int
    renewal_limit: int
    fine_per_day: float
    grace_days: int
    max_overdue_days: int | None
    max_reservations_per_member: int
    hold_hours: int
    reserve_only_when_unavailable: bool
    lost_book_charge: float
    damaged_book_charge: float
    eligibility_restrictions: list[str]
    borrowing_restrictions: dict[str, Any]
    requires_approval: bool
    notes: str | None
    updated_at: datetime


class PolicyHistoryEntry(BaseModel):
    policy_id: str
    version: int
    action: str
    actor_id: str | None
    changes: dict[str, Any]
    created_at: datetime


class EffectivePolicyPreview(BaseModel):
    branch_code: str | None
    member_category: str | None
    resource_type: str | None
    snapshot: dict[str, Any]