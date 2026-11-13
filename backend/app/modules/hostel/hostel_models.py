"""Central hostel collections (authoritative)."""

from datetime import date, datetime

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.hostel.hostel_enums import HostelApplicationStatus, HostelRequestStatus, HostelRequestType


class HostelApplication(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    application_id: str
    academic_year_label: str
    status: HostelApplicationStatus = HostelApplicationStatus.SUBMITTED
    submitted_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_applications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("application_id", ASCENDING)],
                unique=True,
                name="unique_hostel_application",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING)],
                name="hostel_app_by_student",
            ),
        ]


class HostelRoomAllocation(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    allocation_id: str
    hostel_name: str
    block: str
    room_number: str
    bed_label: str
    fee_amount: float = Field(default=0, ge=0)
    effective_from: date | None = None
    published: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_room_allocations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("allocation_id", ASCENDING)],
                unique=True,
                name="unique_hostel_allocation",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_allocation_per_student",
            ),
        ]


class HostelNotice(Document):
    tenant_id: PydanticObjectId
    notice_id: str
    title: str = Field(max_length=200)
    body: str = Field(max_length=8000)
    audience: str = "residents"
    published: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_notices"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("notice_id", ASCENDING)],
                unique=True,
                name="unique_hostel_notice",
            ),
        ]


class HostelServiceRequest(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    request_id: str
    request_type: HostelRequestType
    description: str = Field(max_length=4000)
    payload: dict = Field(default_factory=dict)
    status: HostelRequestStatus = HostelRequestStatus.SUBMITTED
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "hostel_service_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_hostel_request",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="hostel_requests_by_student",
            ),
        ]
