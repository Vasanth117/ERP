"""Hostel resident management (CA 13.06)."""

from __future__ import annotations

import math

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import HostelBlock
from app.modules.college_admin.hostel_residents_page_shared import (
    block_display_label,
    fee_column,
    register_number,
    resident_status_display,
    status_filter_matches,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelResidentManagementPageRead,
    HostelResidentManagementTableRow,
    PoliciesPagination,
    UserListFilterOption,
)
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.hostel.infrastructure_models import InstitutionHostel
from app.modules.hostel.mess_models import HostelMessBillingRecord
from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus
from app.modules.students.models import StudentProfile

_PAGE_SIZE = 4
_TABLE_HEADERS = ["Resident", "Register no.", "Room", "Block", "Fee", "Status"]
_ALL = ""
_ACTIVE_EXCLUDE = frozenset({HostelResidentStatus.CHECKED_OUT, HostelResidentStatus.CANCELLED})


async def get_hostel_resident_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
    search: str | None = None,
    block_code: str | None = None,
    status_filter: str | None = None,
) -> HostelResidentManagementPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    residents = await HostelResident.find(Eq(HostelResident.tenant_id, tenant_id)).sort("-updated_at").to_list()
    residents = [r for r in residents if r.status not in _ACTIVE_EXCLUDE]

    blocks = await HostelBlock.find(Eq(HostelBlock.tenant_id, tenant_id)).to_list()
    block_name: dict[tuple[str, str], str] = {
        (b.building_code, b.block_code): (b.name or b.block_code) for b in blocks
    }
    hostels = await InstitutionHostel.find(Eq(InstitutionHostel.tenant_id, tenant_id)).to_list()
    hostel_by_code = {h.hostel_code.upper(): h for h in hostels if h.hostel_code}

    user_ids = {r.student_user_id for r in residents}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    records = await StudentRecord.find(
        Eq(StudentRecord.tenant_id, tenant_id),
        In(StudentRecord.user_id, list(user_ids)),
    ).to_list() if user_ids else []
    record_by_user = {r.user_id: r for r in records}

    profiles = await StudentProfile.find(
        Eq(StudentProfile.tenant_id, tenant_id),
        In(StudentProfile.user_id, list(user_ids)),
    ).to_list() if user_ids else []
    profile_by_user = {p.user_id: p for p in profiles}

    fee_demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    demands_by_user: dict[PydanticObjectId, list[StudentFeeDemand]] = {}
    for demand in fee_demands:
        demands_by_user.setdefault(demand.student_user_id, []).append(demand)

    billing_rows = await HostelMessBillingRecord.find(Eq(HostelMessBillingRecord.tenant_id, tenant_id)).to_list()
    billing_by_user: dict[PydanticObjectId, list[HostelMessBillingRecord]] = {}
    for row in billing_rows:
        billing_by_user.setdefault(row.student_user_id, []).append(row)

    block_codes: set[str] = set()
    for resident in residents:
        block_codes.add(resident.block_code)

    block_options = [UserListFilterOption(value=_ALL, label="All blocks")]
    for code in sorted(block_codes):
        sample = next((r for r in residents if r.block_code == code), None)
        hostel = hostel_by_code.get((sample.hostel_code or "").upper()) if sample else None
        block_options.append(
            UserListFilterOption(
                value=code,
                label=block_display_label(
                    block_code=code,
                    hostel=hostel,
                    block_name=block_name.get((sample.building_code, code)) if sample else code,
                ),
            )
        )

    status_options = [
        UserListFilterOption(value=_ALL, label="All statuses"),
        UserListFilterOption(value="in_residence", label="In residence"),
        UserListFilterOption(value="notice", label="Notice"),
        UserListFilterOption(value="awaiting", label="Awaiting check-in"),
    ]

    needle = (search or "").strip().lower()
    selected_block = (block_code or "").strip()
    if selected_block == _ALL:
        selected_block = ""

    table_rows: list[HostelResidentManagementTableRow] = []
    for resident in residents:
        if selected_block and resident.block_code != selected_block:
            continue
        if not status_filter_matches(resident.status, (status_filter or "").strip() or None):
            continue
        user = user_by_id.get(resident.student_user_id)
        record = record_by_user.get(resident.student_user_id)
        profile = profile_by_user.get(resident.student_user_id)
        student_name = user.full_name if user else "—"
        roll = register_number(
            roll_number=(record.roll_number if record else None) or (profile.roll_number if profile else None),
            student_id=(record.student_id if record else None) or (profile.student_id if profile else None),
        )
        if needle:
            hay = f"{student_name} {roll}".lower()
            if needle not in hay:
                continue
        hostel = hostel_by_code.get((resident.hostel_code or "").upper())
        bname = block_name.get((resident.building_code, resident.block_code))
        fee_label, fee_tone = fee_column(
            demands=demands_by_user.get(resident.student_user_id, []),
            billing_rows=billing_by_user.get(resident.student_user_id, []),
        )
        status_label, status_tone = resident_status_display(resident.status)
        table_rows.append(
            HostelResidentManagementTableRow(
                resident_key=resident.resident_id,
                resident_label=student_name,
                register_label=roll,
                room_label=resident.room_code or "—",
                block_label=block_display_label(block_code=resident.block_code, hostel=hostel, block_name=bname),
                fee_label=fee_label,
                fee_tone=fee_tone,
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hostel/resident-management?id={resident.resident_id}",
            )
        )

    total = len(table_rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total, start + len(paged_rows))
    count_label = f"{showing_end} of {total}"
    showing_label = f"Showing {showing_end if total else 0} of {total:,}"

    return HostelResidentManagementPageRead(
        page_title="Resident Management",
        page_subtitle="Current residents and records",
        export_label="Export",
        export_href="/college-admin/hostel/resident-management?export=1",
        search_placeholder="Search name or register number",
        block_filter_label="All blocks",
        status_filter_label="All statuses",
        block_options=block_options,
        status_options=status_options,
        residents_section_title="Residents",
        table_headers=_TABLE_HEADERS,
        resident_rows=paged_rows,
        empty_table_message="No hostel residents yet.",
        count_label=count_label,
        showing_label=showing_label,
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )