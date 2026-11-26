"""Hostel bed allocation (CA 13.04)."""

from __future__ import annotations

import math

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admissions_page_shared import (
    allocation_queue_apps,
    conflicts_in_eligibility,
    format_allocated_bed,
    pick_academic_year_label,
    preference_label,
    study_year_ordinal,
)
from app.modules.college_admin.hostel_admin_models import (
    HostelAllocation,
    HostelAllocationStatus,
    HostelBed,
    HostelBedStatus,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelBedAllocationPageRead,
    HostelBedAllocationTableRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import StudentRecord
from app.modules.hostel.hostel_models import HostelApplication, HostelRoomAllocation
from app.modules.hostel.infrastructure_models import InstitutionHostel

_PAGE_SIZE = 3
_TABLE_HEADERS = ["Student", "Year", "Preference", "Allocated bed", "Status"]
_ACTIVE_ALLOC_STATUSES = frozenset(
    {
        HostelAllocationStatus.ACTIVE,
        HostelAllocationStatus.CONFIRMED,
        HostelAllocationStatus.APPROVED,
        HostelAllocationStatus.PENDING,
        HostelAllocationStatus.PENDING_APPROVAL,
    }
)


async def _load_students(
    tenant_id: PydanticObjectId, user_ids: set[PydanticObjectId]
) -> tuple[dict[PydanticObjectId, User], dict[PydanticObjectId, StudentRecord]]:
    if not user_ids:
        return {}, {}
    users = await User.find(In(User.id, list(user_ids))).to_list()
    records = await StudentRecord.find(
        Eq(StudentRecord.tenant_id, tenant_id),
        In(StudentRecord.user_id, list(user_ids)),
    ).to_list()
    return {u.id: u for u in users}, {r.user_id: r for r in records}


def _allocated_bed_for_app(
    app: HostelApplication,
    *,
    admin_alloc_by_app: dict[str, HostelAllocation],
    admin_alloc_by_student: dict[PydanticObjectId, HostelAllocation],
    room_alloc_by_student: dict[PydanticObjectId, HostelRoomAllocation],
) -> str:
    admin = None
    if app.allocation_id:
        admin = admin_alloc_by_app.get(app.allocation_id)
    if admin is None:
        admin = admin_alloc_by_student.get(app.student_user_id)
    if admin is not None:
        return format_allocated_bed(
            block=admin.block_code,
            room=admin.room_code,
            bed=admin.bed_label,
        )
    room_alloc = room_alloc_by_student.get(app.student_user_id)
    if room_alloc is not None:
        return format_allocated_bed(
            block=room_alloc.block,
            room=room_alloc.room_number,
            bed=room_alloc.bed_label,
        )
    return "—"


def _is_allocated(
    app: HostelApplication,
    *,
    admin_alloc_by_app: dict[str, HostelAllocation],
    admin_alloc_by_student: dict[PydanticObjectId, HostelAllocation],
    room_alloc_by_student: dict[PydanticObjectId, HostelRoomAllocation],
) -> bool:
    bed = _allocated_bed_for_app(
        app,
        admin_alloc_by_app=admin_alloc_by_app,
        admin_alloc_by_student=admin_alloc_by_student,
        room_alloc_by_student=room_alloc_by_student,
    )
    return bed != "—"


async def get_hostel_bed_allocation_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
    academic_year_label: str | None = None,
) -> HostelBedAllocationPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    all_apps = await HostelApplication.find(Eq(HostelApplication.tenant_id, tenant_id)).to_list()
    year_label = academic_year_label or pick_academic_year_label(all_apps)
    queue = allocation_queue_apps(all_apps, year_label)

    hostels = await InstitutionHostel.find(Eq(InstitutionHostel.tenant_id, tenant_id)).to_list()
    hostel_by_code = {h.hostel_code.upper(): h.name for h in hostels if h.hostel_code}

    admin_allocs = await HostelAllocation.find(Eq(HostelAllocation.tenant_id, tenant_id)).to_list()
    admin_alloc_by_app = {a.allocation_id: a for a in admin_allocs if a.allocation_id}
    admin_alloc_by_student: dict[PydanticObjectId, HostelAllocation] = {}
    for alloc in admin_allocs:
        if alloc.status not in _ACTIVE_ALLOC_STATUSES:
            continue
        prev = admin_alloc_by_student.get(alloc.student_user_id)
        if prev is None or alloc.updated_at > prev.updated_at:
            admin_alloc_by_student[alloc.student_user_id] = alloc

    room_allocs = await HostelRoomAllocation.find(Eq(HostelRoomAllocation.tenant_id, tenant_id)).to_list()
    room_alloc_by_student = {r.student_user_id: r for r in room_allocs if r.published}

    vacant_beds = await HostelBed.find(
        Eq(HostelBed.tenant_id, tenant_id),
        Eq(HostelBed.status, HostelBedStatus.AVAILABLE),
    ).count()

    approved_unallocated = 0
    allocated_term = 0
    conflicts = 0
    for app in queue:
        allocated = _is_allocated(
            app,
            admin_alloc_by_app=admin_alloc_by_app,
            admin_alloc_by_student=admin_alloc_by_student,
            room_alloc_by_student=room_alloc_by_student,
        )
        if allocated:
            allocated_term += 1
        else:
            approved_unallocated += 1
        if conflicts_in_eligibility(app.eligibility_result):
            conflicts += 1

    user_ids = {a.student_user_id for a in queue if a.student_user_id}
    users_by_id, records_by_user = await _load_students(tenant_id, user_ids)

    table_rows: list[HostelBedAllocationTableRow] = []
    for app in queue:
        student = users_by_id.get(app.student_user_id)
        record = records_by_user.get(app.student_user_id)
        hostel_name = hostel_by_code.get((app.preferred_hostel_code or "").upper())
        bed_label = _allocated_bed_for_app(
            app,
            admin_alloc_by_app=admin_alloc_by_app,
            admin_alloc_by_student=admin_alloc_by_student,
            room_alloc_by_student=room_alloc_by_student,
        )
        allocated = bed_label != "—"
        table_rows.append(
            HostelBedAllocationTableRow(
                row_key=app.application_id,
                student_label=student.full_name if student else "—",
                year_label=study_year_ordinal(
                    record.batch_label if record else None,
                    app.academic_year_label,
                ),
                preference_label=preference_label(
                    room_type=app.preferred_room_type,
                    hostel_name=hostel_name,
                ),
                allocated_bed_label=bed_label,
                status_label="Allocated" if allocated else "Unallocated",
                status_tone="success" if allocated else "warning",
                detail_href=f"/college-admin/hostel/bed-allocation?id={app.application_id}",
            )
        )

    table_rows.sort(key=lambda row: (0 if row.status_tone == "warning" else 1, row.student_label))

    total = len(table_rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total, start + len(paged_rows))
    count_label = f"{showing_end} of {total}"

    conflict_hint = "Gender or year" if conflicts > 0 else ""
    kpis = [
        UserDashboardKpi(
            key="approved_unallocated",
            label="Approved, unallocated",
            value=f"{approved_unallocated:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="allocated_term",
            label="Allocated this term",
            value=f"{allocated_term:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="vacant_beds",
            label="Vacant beds",
            value=f"{vacant_beds:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="conflicts",
            label="Conflicts",
            value=f"{conflicts:,}",
            hint_line=conflict_hint,
            hint_tone="error" if conflicts > 0 else "muted",
        ),
    ]

    return HostelBedAllocationPageRead(
        page_title="Bed Allocation",
        page_subtitle="Allocate beds to approved residents",
        auto_allocate_label="Auto allocate",
        auto_allocate_href="/college-admin/hostel/bed-allocation?action=auto-allocate",
        allocate_bed_label="Allocate bed",
        allocate_bed_href="/college-admin/hostel/bed-allocation?action=allocate",
        kpis=kpis,
        allocation_section_title="Allocation",
        table_headers=_TABLE_HEADERS,
        allocation_rows=paged_rows,
        empty_table_message="No approved residents awaiting allocation.",
        count_label=count_label,
        showing_label=f"Showing {showing_end if total else 0} of {total:,}",
        pagination=PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        academic_year_label=year_label,
        generated_at=now,
    )