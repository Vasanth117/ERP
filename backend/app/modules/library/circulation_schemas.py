"""Circulation API schemas."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from app.modules.library.circulation_enums import ReturnDisposition
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryCopyCondition


class IssueLoanRequest(BaseModel):
    member_user_id: str
    copy_id: str
    branch_code: str | None = None


class ReturnLoanRequest(BaseModel):
    disposition: ReturnDisposition = ReturnDisposition.GOOD
    condition: LibraryCopyCondition | None = None
    notes: str | None = Field(default=None, max_length=500)


class CirculationRead(BaseModel):
    circulation_id: str
    member_user_id: str
    membership_number: str | None = None
    book_id: str
    copy_id: str
    branch_code: str | None = None
    title: str
    issued_at: datetime
    due_at: date
    returned_at: datetime | None = None
    status: LibraryCirculationStatus
    renewal_count: int
    return_disposition: str | None = None


class CirculationHistoryEntry(BaseModel):
    action: str
    branch_code: str | None = None
    actor_id: str | None = None
    metadata: dict
    created_at: datetime