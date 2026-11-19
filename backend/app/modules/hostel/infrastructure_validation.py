"""Hostel infrastructure validation helpers."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.core.exceptions import AppError
from app.modules.college_admin.hostel_admin_models import (
    HostelAllocation,
    HostelAllocationStatus,
    HostelBed,
    HostelBlock,
    HostelBuilding,
    HostelRoom,
)


def norm_code(code: str) -> str:
    return code.strip().upper()


async def get_hostel_building(tenant_id: PydanticObjectId, building_code: str) -> HostelBuilding:
    building = await HostelBuilding.find_one(
        Eq(HostelBuilding.tenant_id, tenant_id),
        Eq(HostelBuilding.building_code, norm_code(building_code)),
    )
    if building is None:
        raise AppError(code="NOT_FOUND", message="Building not found", status_code=404)
    return building


async def get_hostel_block(tenant_id: PydanticObjectId, building_code: str, block_code: str) -> HostelBlock:
    block = await HostelBlock.find_one(
        Eq(HostelBlock.tenant_id, tenant_id),
        Eq(HostelBlock.building_code, norm_code(building_code)),
        Eq(HostelBlock.block_code, norm_code(block_code)),
    )
    if block is None:
        raise AppError(code="NOT_FOUND", message="Block not found", status_code=404)
    return block


async def get_hostel_room(tenant_id: PydanticObjectId, building_code: str, block_code: str, room_code: str) -> HostelRoom:
    room = await HostelRoom.find_one(
        Eq(HostelRoom.tenant_id, tenant_id),
        Eq(HostelRoom.building_code, norm_code(building_code)),
        Eq(HostelRoom.block_code, norm_code(block_code)),
        Eq(HostelRoom.room_code, norm_code(room_code)),
    )
    if room is None:
        raise AppError(code="NOT_FOUND", message="Room not found", status_code=404)
    return room


def validate_room_capacities(*, capacity: int, bed_capacity: int) -> None:
    if bed_capacity > capacity:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Bed capacity cannot exceed room capacity",
            status_code=422,
        )


async def assert_no_active_allocations_for_room(
    tenant_id: PydanticObjectId,
    *,
    building_code: str,
    room_code: str,
) -> None:
    active = await HostelAllocation.find(
        {
            "tenant_id": tenant_id,
            "building_code": norm_code(building_code),
            "room_code": norm_code(room_code),
            "status": {"$in": [HostelAllocationStatus.PENDING.value, HostelAllocationStatus.ACTIVE.value]},
        }
    ).count()
    if active:
        raise AppError(
            code="CONFLICT",
            message="Room has active allocations; cannot delete infrastructure",
            status_code=409,
        )


async def assert_no_active_allocations_for_building(tenant_id: PydanticObjectId, building_code: str) -> None:
    active = await HostelAllocation.find(
        {
            "tenant_id": tenant_id,
            "building_code": norm_code(building_code),
            "status": {"$in": [HostelAllocationStatus.PENDING.value, HostelAllocationStatus.ACTIVE.value]},
        }
    ).count()
    if active:
        raise AppError(
            code="CONFLICT",
            message="Building has active allocations",
            status_code=409,
        )


async def count_beds_for_hostel(tenant_id: PydanticObjectId, hostel_code: str) -> int:
    code = norm_code(hostel_code)
    direct = await HostelBed.find({"tenant_id": tenant_id, "hostel_code": code}).count()
    building_codes = [
        b.building_code
        for b in await HostelBuilding.find({"tenant_id": tenant_id, "hostel_code": code}).to_list()
    ]
    via_building = 0
    if building_codes:
        via_building = await HostelBed.find(
            {"tenant_id": tenant_id, "building_code": {"$in": building_codes}, "hostel_code": None}
        ).count()
    return direct + via_building


async def assert_hostel_capacity(tenant_id: PydanticObjectId, hostel_code: str, configured_capacity: int, *, adding_beds: int = 0) -> None:
    if configured_capacity <= 0:
        return
    current = await count_beds_for_hostel(tenant_id, hostel_code)
    if current + adding_beds > configured_capacity:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Operation would exceed hostel configured bed capacity",
            status_code=422,
        )