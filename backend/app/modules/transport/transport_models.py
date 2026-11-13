"""Central transport collections (authoritative)."""

from datetime import datetime, time

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.transport.transport_enums import TransportRequestStatus, TransportRequestType


class TransportRoute(Document):
    tenant_id: PydanticObjectId
    route_id: str
    name: str = Field(max_length=200)
    fee_amount: float = Field(default=0, ge=0)
    published: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "transport_routes"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("route_id", ASCENDING)],
                unique=True,
                name="unique_transport_route",
            ),
        ]


class TransportStop(Document):
    tenant_id: PydanticObjectId
    stop_id: str
    route_id: str
    name: str = Field(max_length=200)
    pickup_time: time | None = None
    drop_time: time | None = None
    sequence: int = Field(default=1, ge=1)

    class Settings:
        name = "transport_stops"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("stop_id", ASCENDING)],
                unique=True,
                name="unique_transport_stop",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("route_id", ASCENDING), ("sequence", ASCENDING)],
                name="stops_by_route",
            ),
        ]


class TransportSchedule(Document):
    tenant_id: PydanticObjectId
    schedule_id: str
    route_id: str
    day_of_week: int = Field(ge=0, le=6)
    departure_time: time
    published: bool = True

    class Settings:
        name = "transport_schedules"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("schedule_id", ASCENDING)],
                unique=True,
                name="unique_transport_schedule",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("route_id", ASCENDING), ("day_of_week", ASCENDING)],
                name="schedules_by_route",
            ),
        ]


class TransportAllocation(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    allocation_id: str
    route_id: str
    route_name: str
    pickup_stop: str
    drop_stop: str
    fee_amount: float = Field(default=0, ge=0)
    published: bool = True
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "transport_allocations"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("allocation_id", ASCENDING)],
                unique=True,
                name="unique_transport_allocation",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING)],
                unique=True,
                name="unique_transport_per_student",
            ),
        ]


class TransportServiceRequest(Document):
    tenant_id: PydanticObjectId
    student_user_id: PydanticObjectId
    request_id: str
    request_type: TransportRequestType
    description: str = Field(max_length=4000)
    status: TransportRequestStatus = TransportRequestStatus.SUBMITTED
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "transport_service_requests"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("request_id", ASCENDING)],
                unique=True,
                name="unique_transport_request",
            ),
            IndexModel(
                [("tenant_id", ASCENDING), ("student_user_id", ASCENDING), ("created_at", DESCENDING)],
                name="transport_requests_by_student",
            ),
        ]


class TransportNotification(Document):
    tenant_id: PydanticObjectId
    notification_id: str
    route_id: str | None = None
    title: str = Field(max_length=200)
    body: str = Field(max_length=4000)
    published: bool = True
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "transport_notifications"
        indexes = [
            IndexModel(
                [("tenant_id", ASCENDING), ("notification_id", ASCENDING)],
                unique=True,
                name="unique_transport_notification",
            ),
        ]
