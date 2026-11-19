"""Hostel room and bed availability reads."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBedStatus, HostelRoom
from app.modules.hostel.allocation_schemas import BedAvailabilityItem, RoomAvailabilityItem
from app.modules.hostel.infrastructure_validation import norm_code
from app.modules.hostel.policy import authorize_hostel_allocation_read, require_hostel_tenant_scope


def _bed_item(bed: HostelBed, room: HostelRoom | None) -> BedAvailabilityItem:
    return BedAvailabilityItem(
        bed_id=bed.bed_id,
        bed_label=bed.bed_label,
        status=bed.status,
        hostel_code=bed.hostel_code,
        building_code=bed.building_code,
        block_code=bed.block_code,
        room_code=bed.room_code,
        floor_id=room.floor_id if room else None,
        room_type=room.room_type if room else None,
    )


async def list_bed_availability(
    scope: AccessScope,
    pagination: Pagination,
    *,
    hostel_code: str | None = None,
    building_code: str | None = None,
    block_code: str | None = None,
    floor_id: str | None = None,
    room_type: str | None = None,
    status: HostelBedStatus | None = None,
    academic_year_label: str | None = None,
) -> Page[BedAvailabilityItem]:
    _ = academic_year_label
    authorize_hostel_allocation_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    query: dict = {"tenant_id": tenant_id}
    if hostel_code:
        query["hostel_code"] = norm_code(hostel_code)
    if building_code:
        query["building_code"] = norm_code(building_code)
    if block_code:
        query["block_code"] = norm_code(block_code)
    if status:
        query["status"] = status.value
    total = await HostelBed.find(query).count()
    beds = await HostelBed.find(query).skip(pagination.offset).limit(pagination.limit).to_list()
    room_keys = {(b.building_code, b.block_code, b.room_code) for b in beds}
    room_map: dict[tuple[str, str, str], HostelRoom] = {}
    for bc, blc, rc in room_keys:
        room = await HostelRoom.find_one(
            Eq(HostelRoom.tenant_id, tenant_id),
            Eq(HostelRoom.building_code, bc),
            Eq(HostelRoom.block_code, blc),
            Eq(HostelRoom.room_code, rc),
        )
        if room:
            room_map[(bc, blc, rc)] = room
    items: list[BedAvailabilityItem] = []
    for bed in beds:
        room = room_map.get((bed.building_code, bed.block_code, bed.room_code))
        if floor_id and (room is None or room.floor_id != norm_code(floor_id)):
            continue
        if room_type and (room is None or room.room_type != room_type):
            continue
        items.append(_bed_item(bed, room))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def list_room_availability(
    scope: AccessScope,
    pagination: Pagination,
    *,
    hostel_code: str | None = None,
    building_code: str | None = None,
    block_code: str | None = None,
    floor_id: str | None = None,
    room_type: str | None = None,
) -> Page[RoomAvailabilityItem]:
    authorize_hostel_allocation_read(scope)
    tenant_id = require_hostel_tenant_scope(scope)
    room_q: dict = {"tenant_id": tenant_id}
    if hostel_code:
        room_q["hostel_code"] = norm_code(hostel_code)
    if building_code:
        room_q["building_code"] = norm_code(building_code)
    if block_code:
        room_q["block_code"] = norm_code(block_code)
    if floor_id:
        room_q["floor_id"] = norm_code(floor_id)
    if room_type:
        room_q["room_type"] = room_type
    total = await HostelRoom.find(room_q).count()
    rooms = await HostelRoom.find(room_q).skip(pagination.offset).limit(pagination.limit).to_list()
    items: list[RoomAvailabilityItem] = []
    for room in rooms:
        beds = await HostelBed.find(
            Eq(HostelBed.tenant_id, tenant_id),
            Eq(HostelBed.building_code, room.building_code),
            Eq(HostelBed.block_code, room.block_code),
            Eq(HostelBed.room_code, room.room_code),
        ).to_list()
        occupied = sum(1 for b in beds if b.status == HostelBedStatus.ALLOCATED)
        available = sum(1 for b in beds if b.status == HostelBedStatus.AVAILABLE)
        items.append(
            RoomAvailabilityItem(
                building_code=room.building_code,
                block_code=room.block_code,
                room_code=room.room_code,
                hostel_code=room.hostel_code,
                floor_id=room.floor_id,
                room_type=room.room_type,
                capacity=room.capacity,
                bed_capacity=room.bed_capacity,
                occupied_beds=occupied,
                available_beds=available,
                beds=[_bed_item(b, room) for b in beds],
            )
        )
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)