"""Library membership API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.library.member_enums import LibraryMemberCategory, LibraryMemberStatus


class MemberRegisterRequest(BaseModel):
    member_user_id: str
    member_category: LibraryMemberCategory = LibraryMemberCategory.STUDENT
    branch_code: str | None = None
    borrowing_limit: int = Field(default=5, ge=0)
    activated_on: date | None = None
    expires_on: date | None = None
    eligible: bool = True


class MemberUpdateRequest(BaseModel):
    branch_code: str | None = None
    borrowing_limit: int | None = Field(default=None, ge=0)
    activated_on: date | None = None
    expires_on: date | None = None
    eligible: bool | None = None
    status: LibraryMemberStatus | None = None


class MemberSuspendRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class MemberRead(BaseModel):
    membership_number: str
    member_user_id: str
    member_category: LibraryMemberCategory
    display_name: str
    email: str
    branch_code: str | None = None
    status: LibraryMemberStatus
    eligible: bool
    borrowing_eligible: bool
    borrowing_limit: int
    activated_on: date | None = None
    expires_on: date | None = None
    suspension_reason: str | None = None
    suspended_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MemberBorrowingSummary(BaseModel):
    active_loans: int
    overdue_loans: int
    open_fines: int
    outstanding_fine_amount: float
    total_loan_history: int


class MemberHistoryEntry(BaseModel):
    action: str
    changes: dict
    actor_id: str | None = None
    created_at: datetime