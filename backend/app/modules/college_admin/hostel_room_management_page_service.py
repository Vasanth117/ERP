"""Hostel room management (CA 13.03)."""

from __future__ import annotations

import math

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBedStatus, HostelBlock, HostelRoom
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelRoomManagementPageRead,
    HostelRoomManagementTableRow,
    PoliciesPagination,
    UserListFilterOption,
)

_PAGE_SIZE = 4
_TABLE_HEADERS = ["Room", "Block", "Floor", "Type", "Beds", "Occupied", "Status"]
_ALL = ""


def _room_type_label(room_type: str | None) -> str:
    if not room_type:
        return "—"
    return room_type.replace("_", " ").title()


def _room_status(room: HostelRoom, occupied: int, capacity: int) -> tuple[str, str]:
    maint = (room.maintenance_status or "available").lower()
    if maint not in {"", "available", "active"}:
        return "Maintenance", "warning"
    op = (room.operational_status or "active").lower()
    if op in {"inactive", "closed"}:
        return "Inactive", "muted"
    if capacity > 0 and occupied >= capacity:
        return "Full", "success"
    return "Available", "info"


async def get_hostel_room_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
    search: str | None = None,
    block_code: str | None = None,
    floor_id: str | None = None,
    room_type: str | None = None,
) -> HostelRoomManagementPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    rooms = await HostelRoom.find(Eq(HostelRoom.tenant_id, tenant_id)).sort("room_code").to_list()
    blocks = await HostelBlock.find(Eq(HostelBlock.tenant_id, tenant_id)).to_list()
    block_name_by_code: dict[tuple[str, str], str] = {
        (b.building_code, b.block_code): (b.name or b.block_code) for b in blocks
    }
    beds = await HostelBed.find(Eq(HostelBed.tenant_id, tenant_id)).to_list()
    occupied_by_room: dict[tuple[str, str, str], int] = {}
    for bed in beds:
        if bed.status == HostelBedStatus.ALLOCATED:
            key = (bed.building_code, bed.block_code, bed.room_code)
            occupied_by_room[key] = occupied_by_room.get(key, 0) + 1

    needle = (search or "").strip().lower()

    block_codes: set[str] = set()
    floor_ids: set[str] = set()
    type_codes: set[str] = set()
    for room in rooms:
        block_codes.add(room.block_code)
        if room.floor_id:
            floor_ids.add(room.floor_id)
        if room.floor_label:
            floor_ids.add(room.floor_label)
        if room.room_type:
            type_codes.add(room.room_type)

    def block_option_label(code: str) -> str:
        for (building_code, bcode), name in block_name_by_code.items():
            if bcode == code:
                return name
        return code

    block_options = [UserListFilterOption(value=_ALL, label="All blocks")]
    block_options.extend(
        UserListFilterOption(value=code, label=block_option_label(code)) for code in sorted(block_codes)
    )
    floor_options = [UserListFilterOption(value=_ALL, label="All floors")]
    floor_options.extend(UserListFilterOption(value=fid, label=fid) for fid in sorted(floor_ids, key=lambda x: (len(x), x)))
    type_options = [UserListFilterOption(value=_ALL, label="All types")]
    type_options.extend(UserListFilterOption(value=t, label=_room_type_label(t)) for t in sorted(type_codes))

    table_rows: list[HostelRoomManagementTableRow] = []
    for room in rooms:
        if block_code and block_code != _ALL and room.block_code != block_code:
            continue
        floor_key = room.floor_id or room.floor_label or ""
        if floor_id and floor_id != _ALL and floor_key != floor_id:
            continue
        if room_type and room_type != _ALL and (room.room_type or "") != room_type:
            continue
        label_blob = f"{room.room_code} {block_option_label(room.block_code)} {floor_key}".lower()
        if needle and needle not in label_blob:
            continue

        capacity = room.bed_capacity or room.capacity or 0
        key = (room.building_code, room.block_code, room.room_code)
        occupied = occupied_by_room.get(key, 0)
        status_label, status_tone = _room_status(room, occupied, capacity)
        block_label = block_name_by_code.get((room.building_code, room.block_code), room.block_code)
        floor_label = room.floor_label or room.floor_id or "—"
        table_rows.append(
            HostelRoomManagementTableRow(
                room_code=room.room_code,
                room_label=room.room_code,
                block_label=block_label,
                floor_label=floor_label,
                type_label=_room_type_label(room.room_type),
                beds_label=str(capacity),
                occupied_label=str(occupied),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hostel/room-management?room={room.room_code}",
            )
        )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_rows = len(table_rows)
    total_pages = math.ceil(total_rows / page_size) if total_rows else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total_rows, start + len(paged_rows))
    showing_label = f"Showing {showing_end if total_rows else 0} of {total_rows:,}"

    return HostelRoomManagementPageRead(
        page_title="Room Management",
        page_subtitle="Rooms, types and amenities",
        add_room_label="Add room",
        add_room_href="/college-admin/hostel/room-management?action=create",
        search_placeholder="Search room number",
        block_filter_label="All blocks",
        floor_filter_label="All floors",
        type_filter_label="All types",
        block_options=block_options,
        floor_options=floor_options,
        type_options=type_options,
        rooms_section_title="Rooms",
        table_headers=_TABLE_HEADERS,
        room_rows=paged_rows,
        empty_table_message="No rooms match your search and filters.",
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total_rows,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )