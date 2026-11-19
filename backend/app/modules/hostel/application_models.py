"""Hostel application, waiting list and allocation workflow collections."""

from datetime import date, datetime
from enum import Enum
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow


class HostelOfferStatus(str, Enum):
    OFFERED = "offered"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class HostelTransferStatus(str, Enum):
    REQUESTED = "requested"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class HostelTransferType(str, Enum):
    ROOM = "room"
    BED = "bed"
    HOSTEL = "hostel"
    TEMPORARY = "temporary"
    EMERGENCY = "emergency"


class HostelWaitingList(Document):
    tenant_id: PydanticObjectId
    list_id: str
    title: str = Field(max_length=200)
    hostel_code: str | None = None
    room_type: str | None = None
    academic_year_label: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_waiting_lists"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("list_id", ASCENDING)],
                unique=True,
                name="unique_hostel_waiting_list",
            ),
        ]


class HostelApplicationReview(Document):
    tenant_id: PydanticObjectId
    review_id: str
    application_id: str
    decision: str
    remarks: str | None = Field(default=None, max_length=4000)
    reviewer_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_application_reviews"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("review_id", ASCENDING)],
                unique=True,
                name="unique_hostel_app_review",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("application_id", ASCENDING), ("created_at", DESCENDING)],
                name="app_reviews_by_application",
            ),
        ]


class HostelApplicationStatusHistory(Document):
    tenant_id: PydanticObjectId
    application_id: str
    from_status: str | None = None
    to_status: str
    actor_id: PydanticObjectId | None = None
    note: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_application_status_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("application_id", ASCENDING), ("created_at", DESCENDING)],
                name="app_status_history",
            ),
        ]


class HostelAllocationOffer(Document):
    tenant_id: PydanticObjectId
    offer_id: str
    application_id: str
    student_user_id: PydanticObjectId
    hostel_code: str
    bed_id: str | None = None
    building_code: str | None = None
    block_code: str | None = None
    room_code: str | None = None
    status: HostelOfferStatus = HostelOfferStatus.OFFERED
    response_deadline: datetime
    responded_at: datetime | None = None
    allocation_id: str | None = None
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_allocation_offers"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("offer_id", ASCENDING)],
                unique=True,
                name="unique_hostel_offer",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("application_id", ASCENDING), ("status", ASCENDING)],
                name="offers_by_application",
            ),
        ]


class HostelAllocationHistory(Document):
    tenant_id: PydanticObjectId
    allocation_id: str
    event_type: str = Field(max_length=64)
    from_status: str | None = None
    to_status: str | None = None
    from_bed_id: str | None = None
    to_bed_id: str | None = None
    from_hostel_code: str | None = None
    to_hostel_code: str | None = None
    note: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    actor_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_allocation_history"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("allocation_id", ASCENDING), ("created_at", DESCENDING)],
                name="allocation_history",
            ),
        ]


class HostelRoomTransferRequest(Document):
    tenant_id: PydanticObjectId
    transfer_id: str
    allocation_id: str
    student_user_id: PydanticObjectId
    transfer_type: HostelTransferType
    target_bed_id: str
    reason: str = Field(max_length=2000)
    status: HostelTransferStatus = HostelTransferStatus.REQUESTED
    new_allocation_id: str | None = None
    actor_id: PydanticObjectId | None = None
    approver_id: PydanticObjectId | None = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_room_transfer_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("transfer_id", ASCENDING)],
                unique=True,
                name="unique_hostel_transfer",
            ),
            IndexModel([("tenant_id", ASCENDING), ("allocation_id", ASCENDING)], name="transfers_by_allocation"),
        ]