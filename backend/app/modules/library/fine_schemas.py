"""Library fine API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.library.fine_enums import LibraryFineApprovalType, LibraryFineType
from app.modules.library.library_enums import LibraryFineStatus


class FinePolicyUpsert(BaseModel):
    branch_code: str | None = None
    fine_per_day: float = Field(default=5.0, ge=0)
    grace_days: int = Field(default=0, ge=0)
    max_overdue_days: int | None = Field(default=90, ge=1)
    lost_book_charge: float = Field(default=500.0, ge=0)
    damaged_book_charge: float = Field(default=150.0, ge=0)
    replacement_charge: float = Field(default=500.0, ge=0)


class DamageReportCreate(BaseModel):
    report_id: str | None = None
    member_user_id: str
    copy_id: str
    circulation_id: str | None = None
    report_type: LibraryFineType
    description: str = Field(min_length=3, max_length=2000)
    replacement_cost: float | None = Field(default=None, ge=0)


class FineWaiverRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class FineApprovalDecision(BaseModel):
    approved: bool
    note: str | None = Field(default=None, max_length=500)


class FinePaymentVerifyRequest(BaseModel):
    transaction_id: str


class FineRead(BaseModel):
    fine_id: str
    member_user_id: str
    fine_type: str
    book_id: str | None = None
    copy_id: str | None = None
    branch_code: str | None = None
    circulation_id: str | None = None
    amount: float
    amount_waived: float
    amount_paid: float
    balance: float
    reason: str
    status: LibraryFineStatus
    recovery_status: str
    demand_id: str | None = None
    payment_transaction_id: str | None = None
    due_date: date | None = None
    assessed_at: datetime
    created_at: datetime
    updated_at: datetime


class FineHistoryEntry(BaseModel):
    action: str
    actor_id: str | None = None
    changes: dict
    created_at: datetime