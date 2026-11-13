"""Hostel and transport reads for enrolled students."""

from beanie import PydanticObjectId

from app.modules.hostel.hostel_models import (
    HostelApplication,
    HostelNotice,
    HostelRoomAllocation,
    HostelServiceRequest,
)
from app.modules.transport.transport_models import (
    TransportAllocation,
    TransportNotification,
    TransportRoute,
    TransportSchedule,
    TransportServiceRequest,
    TransportStop,
)


async def hostel_application(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> HostelApplication | None:
    rows = (
        await HostelApplication.find({"tenant_id": tenant_id, "student_user_id": user_id})
        .sort("-submitted_at")
        .limit(1)
        .to_list()
    )
    return rows[0] if rows else None


async def hostel_allocation(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> HostelRoomAllocation | None:
    return await HostelRoomAllocation.find_one({"tenant_id": tenant_id, "student_user_id": user_id, "published": True})


async def hostel_notices(tenant_id: PydanticObjectId, limit: int = 30) -> list[HostelNotice]:
    return await HostelNotice.find({"tenant_id": tenant_id, "published": True}).sort("-created_at").limit(limit).to_list()


async def hostel_requests(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[HostelServiceRequest]:
    return await HostelServiceRequest.find({"tenant_id": tenant_id, "student_user_id": user_id}).sort("-created_at").to_list()


async def transport_routes(tenant_id: PydanticObjectId) -> list[TransportRoute]:
    return await TransportRoute.find({"tenant_id": tenant_id, "published": True}).sort("name").to_list()


async def transport_stops(tenant_id: PydanticObjectId, route_id: str) -> list[TransportStop]:
    return await TransportStop.find({"tenant_id": tenant_id, "route_id": route_id}).sort("sequence").to_list()


async def transport_schedules(tenant_id: PydanticObjectId, route_id: str | None = None) -> list[TransportSchedule]:
    filters: dict = {"tenant_id": tenant_id, "published": True}
    if route_id:
        filters["route_id"] = route_id
    return await TransportSchedule.find(filters).sort([("route_id", 1), ("day_of_week", 1)]).to_list()


async def transport_allocation(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> TransportAllocation | None:
    return await TransportAllocation.find_one({"tenant_id": tenant_id, "student_user_id": user_id, "published": True})


async def transport_requests(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[TransportServiceRequest]:
    return await TransportServiceRequest.find({"tenant_id": tenant_id, "student_user_id": user_id}).sort("-created_at").to_list()


async def transport_notifications(tenant_id: PydanticObjectId, route_id: str | None = None) -> list[TransportNotification]:
    filters: dict = {"tenant_id": tenant_id, "published": True}
    if route_id:
        filters["$or"] = [{"route_id": route_id}, {"route_id": None}]
    return await TransportNotification.find(filters).sort("-created_at").limit(50).to_list()
