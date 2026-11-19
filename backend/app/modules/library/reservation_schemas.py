"""Reservation API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.library.library_enums import LibraryReservationStatus


class ReservationCreateRequest(BaseModel):
    reservation_id: str | None = Field(default=None, max_length=64)
    member_user_id: str
    book_id: str
    branch_code: str | None = None
    priority: int = Field(default=0, ge=0)


class ReservationCancelRequest(BaseModel):
    reason: str = Field(min_length=2, max_length=500)


class ReservationAllocateRequest(BaseModel):
    copy_id: str | None = None


class ReservationPolicyUpsert(BaseModel):
    branch_code: str | None = None
    hold_hours: int = Field(default=72, ge=1, le=168)
    max_active_per_member: int = Field(default=5, ge=1)
    reserve_only_when_unavailable: bool = True


class ReservationRead(BaseModel):
    reservation_id: str
    member_user_id: str
    membership_number: str | None = None
    book_id: str
    title: str
    branch_code: str | None = None
    copy_id: str | None = None
    status: LibraryReservationStatus
    queue_position: int
    priority: int
    ready_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ReservationHistoryEntry(BaseModel):
    action: str
    actor_id: str | None = None
    changes: dict
    created_at: datetime