"""Hostel building / block management (CA 13.02)."""

from __future__ import annotations

import math

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import HostelBed, HostelBlock, HostelBuilding, HostelRoom
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelBuildingManagementPageRead,
    HostelBuildingManagementTableRow,
    PoliciesPagination,
)
from app.modules.hostel.hostel_portal_enums import HostelCategory
from app.modules.hostel.infrastructure_models import HostelFloor, InstitutionHostel

_PAGE_SIZE = 4
_TABLE_HEADERS = ["Block", "Type", "Floors", "Rooms", "Beds", "Warden", "Status"]


def _type_label(building: HostelBuilding | None, hostel: InstitutionHostel | None) -> str:
    if building and building.building_type:
        return building.building_type.replace("_", " ").title()
    if hostel:
        if hostel.category == HostelCategory.CUSTOM and hostel.custom_category_label:
            return hostel.custom_category_label
        return hostel.category.value.replace("_", " ").title()
    return "—"


def _status(building: HostelBuilding | None, *, block_active: bool) -> tuple[str, str]:
    if building is None:
        return ("Active", "success") if block_active else ("Inactive", "muted")
    key = (building.operating_status or "active").lower()
    if not building.is_active or not block_active:
        return "Inactive", "muted"
    if key in {"maintenance", "renovation", "temporarily_closed"}:
        return "Renovation", "warning"
    if key == "inactive":
        return "Inactive", "muted"
    return "Active", "success"


async def _load_warden_names(tenant_id: PydanticObjectId, user_ids: set[PydanticObjectId]) -> dict[PydanticObjectId, str]:
    if not user_ids:
        return {}
    users = await User.find(In(User.id, list(user_ids))).to_list()
    return {u.id: u.full_name or "—" for u in users}


async def get_hostel_building_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HostelBuildingManagementPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    blocks = await HostelBlock.find(Eq(HostelBlock.tenant_id, tenant_id)).sort("name").to_list()
    buildings = await HostelBuilding.find(Eq(HostelBuilding.tenant_id, tenant_id)).to_list()
    building_by_code = {b.building_code: b for b in buildings}
    hostels = await InstitutionHostel.find(Eq(InstitutionHostel.tenant_id, tenant_id)).to_list()
    hostel_by_code = {h.hostel_code: h for h in hostels}

    rooms = await HostelRoom.find(Eq(HostelRoom.tenant_id, tenant_id)).to_list()
    beds = await HostelBed.find(Eq(HostelBed.tenant_id, tenant_id)).to_list()
    floors = await HostelFloor.find(Eq(HostelFloor.tenant_id, tenant_id)).to_list()

    rooms_by_block: dict[tuple[str, str], int] = {}
    beds_by_block: dict[tuple[str, str], int] = {}
    for room in rooms:
        key = (room.building_code, room.block_code)
        rooms_by_block[key] = rooms_by_block.get(key, 0) + 1
        beds_by_block[key] = beds_by_block.get(key, 0) + room.bed_capacity
    for bed in beds:
        key = (bed.building_code, bed.block_code)
        if key not in beds_by_block or beds_by_block[key] == 0:
            beds_by_block[key] = beds_by_block.get(key, 0) + 1

    floors_by_building: dict[str, set[str]] = {}
    for fl in floors:
        floors_by_building.setdefault(fl.building_code, set()).add(fl.floor_id)
    for room in rooms:
        if room.floor_id:
            floors_by_building.setdefault(room.building_code, set()).add(room.floor_id)

    warden_ids: set[PydanticObjectId] = set()
    for block in blocks:
        if block.responsible_staff_user_id:
            warden_ids.add(block.responsible_staff_user_id)
    for hostel in hostels:
        if hostel.warden_user_id:
            warden_ids.add(hostel.warden_user_id)
    warden_by_id = await _load_warden_names(tenant_id, warden_ids)

    table_rows: list[HostelBuildingManagementTableRow] = []
    for block in blocks:
        building = building_by_code.get(block.building_code)
        hostel = hostel_by_code.get(block.hostel_code or (building.hostel_code if building else None) or "")
        key = (block.building_code, block.block_code)
        floor_count = len(floors_by_building.get(block.building_code, set()))
        room_count = rooms_by_block.get(key, 0)
        bed_count = beds_by_block.get(key, 0)
        warden_id = block.responsible_staff_user_id
        if not warden_id and hostel:
            warden_id = hostel.warden_user_id
        warden_label = warden_by_id.get(warden_id, "—") if warden_id else "—"
        status_label, status_tone = _status(building, block_active=block.is_active)
        block_label = block.name or block.block_code
        table_rows.append(
            HostelBuildingManagementTableRow(
                block_key=f"{block.building_code}:{block.block_code}",
                block_label=block_label,
                type_label=_type_label(building, hostel),
                floors_label=str(floor_count),
                rooms_label=str(room_count),
                beds_label=str(bed_count),
                warden_label=warden_label,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hostel/hostel-building-management?block={block.block_code}",
            )
        )

    if not table_rows and buildings:
        for building in buildings:
            hostel = hostel_by_code.get(building.hostel_code or "")
            floor_count = len(floors_by_building.get(building.building_code, set()))
            building_rooms = [r for r in rooms if r.building_code == building.building_code]
            room_count = len(building_rooms)
            bed_count = sum(r.bed_capacity for r in building_rooms) or sum(
                1 for b in beds if b.building_code == building.building_code
            )
            warden_id = hostel.warden_user_id if hostel else None
            warden_label = warden_by_id.get(warden_id, "—") if warden_id else "—"
            status_label, status_tone = _status(building, block_active=building.is_active)
            table_rows.append(
                HostelBuildingManagementTableRow(
                    block_key=building.building_code,
                    block_label=building.name or building.building_code,
                    type_label=_type_label(building, hostel),
                    floors_label=str(floor_count),
                    rooms_label=str(room_count),
                    beds_label=str(bed_count),
                    warden_label=warden_label,
                    status_label=status_label,
                    status_tone=status_tone,
                    detail_href=f"/college-admin/hostel/hostel-building-management?building={building.building_code}",
                )
            )

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_rows = len(table_rows)
    total_pages = math.ceil(total_rows / page_size) if total_rows else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total_rows, start + len(paged_rows))
    count_label = f"{showing_end} of {total_rows}"
    showing_label = f"Showing {showing_end if total_rows else 0} of {total_rows:,}"

    return HostelBuildingManagementPageRead(
        page_title="Hostel Building Management",
        page_subtitle="Blocks, floors and wardens",
        add_building_label="Add building",
        add_building_href="/college-admin/hostel/hostel-building-management?action=create",
        buildings_section_title="Buildings",
        table_headers=_TABLE_HEADERS,
        block_rows=paged_rows,
        empty_table_message="No hostel blocks yet. Add a building to get started.",
        count_label=count_label,
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