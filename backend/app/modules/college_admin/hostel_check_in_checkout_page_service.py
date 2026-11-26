"""Hostel check-in / checkout (CA 13.07)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hostel_admin_models import HostelResidentHistory
from app.modules.college_admin.hostel_residents_page_shared import deposit_refund_total, week_start_ist
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelCheckInCheckoutPageRead,
    HostelCheckInCheckoutTableRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.hostel.resident_models import (
    HostelResident,
    HostelResidentCheckinRecord,
    HostelResidentCheckoutRecord,
    HostelResidentStatus,
)

_PAGE_SIZE = 3
_TABLE_HEADERS = ["Student", "Room", "Type", "Date", "Handover", "Status"]


@dataclass
class _Movement:
    movement_key: str
    student_user_id: PydanticObjectId
    room_code: str
    movement_type: str
    occurred_at: datetime
    handover_label: str
    handover_tone: str
    status_label: str
    status_tone: str
    detail_href: str
    sort_rank: int


def _format_short_date(when: datetime) -> str:
    return when.strftime("%d %b")


async def get_hostel_check_in_checkout_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HostelCheckInCheckoutPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    week_start = week_start_ist(now)

    checkins = await HostelResidentCheckinRecord.find(Eq(HostelResidentCheckinRecord.tenant_id, tenant_id)).to_list()
    checkouts = await HostelResidentCheckoutRecord.find(Eq(HostelResidentCheckoutRecord.tenant_id, tenant_id)).to_list()
    residents = await HostelResident.find(Eq(HostelResident.tenant_id, tenant_id)).to_list()
    resident_by_id = {r.resident_id: r for r in residents}
    resident_by_alloc = {r.allocation_id: r for r in residents}
    history = await HostelResidentHistory.find(Eq(HostelResidentHistory.tenant_id, tenant_id)).sort("-created_at").limit(200).to_list()

    checkins_week = sum(1 for row in checkins if row.checked_in_at >= week_start)
    checkouts_week = sum(1 for row in checkouts if row.checked_out_at >= week_start)

    pending_handover = 0
    for row in checkins:
        if not row.room_condition_ack or not row.keys_issued:
            pending_handover += 1
    for row in checkouts:
        if not row.keys_returned:
            pending_handover += 1
    for resident in residents:
        if resident.status == HostelResidentStatus.AWAITING_CHECKIN:
            pending_handover += 1

    refund_count = 0
    refund_total = 0.0
    for row in checkouts:
        amount = deposit_refund_total(row.clearance_status)
        if amount > 0:
            refund_count += 1
            refund_total += amount

    movements: list[_Movement] = []
    for row in checkins:
        resident = resident_by_id.get(row.resident_id) or resident_by_alloc.get(row.allocation_id)
        if resident is None:
            continue
        room = resident.room_code or "—"
        handover = "Complete" if row.room_condition_ack and row.keys_issued else "Pending"
        handover_tone = "success" if handover == "Complete" else "warning"
        done = resident is not None and resident.status == HostelResidentStatus.CHECKED_IN
        movements.append(
            _Movement(
                movement_key=f"cin:{row.record_id}",
                student_user_id=resident.student_user_id,
                room_code=room,
                movement_type="Check-in",
                occurred_at=row.checked_in_at,
                handover_label=handover,
                handover_tone=handover_tone,
                status_label="Done" if done else "Scheduled",
                status_tone="success" if done else "warning",
                detail_href=f"/college-admin/hostel/hostel-check-in-checkout?id={row.allocation_id}",
                sort_rank=0 if done else 1,
            )
        )

    for row in checkouts:
        resident = resident_by_id.get(row.resident_id) or resident_by_alloc.get(row.allocation_id)
        if resident is None:
            continue
        room = resident.room_code or "—"
        handover = "Complete" if row.keys_returned else "Pending"
        handover_tone = "success" if handover == "Complete" else "warning"
        done = resident is not None and resident.status == HostelResidentStatus.CHECKED_OUT
        movements.append(
            _Movement(
                movement_key=f"cout:{row.record_id}",
                student_user_id=resident.student_user_id,
                room_code=room,
                movement_type="Check-out",
                occurred_at=row.checked_out_at,
                handover_label=handover,
                handover_tone=handover_tone,
                status_label="Done" if done else "Scheduled",
                status_tone="success" if done else "warning",
                detail_href=f"/college-admin/hostel/hostel-check-in-checkout?id={row.allocation_id}",
                sort_rank=0 if done else 1,
            )
        )

    if not movements and history:
        alloc_ids = {h.allocation_id for h in history}
        resident_by_alloc = {r.allocation_id: r for r in residents}
        for item in history:
            resident = resident_by_alloc.get(item.allocation_id)
            is_in = item.event_type == "check_in"
            movements.append(
                _Movement(
                    movement_key=f"hist:{item.allocation_id}:{item.created_at.isoformat()}",
                    student_user_id=item.student_user_id,
                    room_code=resident.room_code if resident else "—",
                    movement_type="Check-in" if is_in else "Check-out",
                    occurred_at=item.created_at,
                    handover_label="—",
                    handover_tone="muted",
                    status_label="Done",
                    status_tone="success",
                    detail_href=f"/college-admin/hostel/hostel-check-in-checkout?id={item.allocation_id}",
                    sort_rank=0,
                )
            )

    movements.sort(key=lambda m: (m.sort_rank, -m.occurred_at.timestamp()))

    user_ids = {m.student_user_id for m in movements if m.student_user_id}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[HostelCheckInCheckoutTableRow] = []
    for movement in movements:
        student = user_by_id.get(movement.student_user_id)
        table_rows.append(
            HostelCheckInCheckoutTableRow(
                movement_key=movement.movement_key,
                student_label=student.full_name if student else "—",
                room_label=movement.room_code,
                type_label=movement.movement_type,
                date_label=_format_short_date(movement.occurred_at),
                handover_label=movement.handover_label,
                handover_tone=movement.handover_tone,
                status_label=movement.status_label,
                status_tone=movement.status_tone,
                detail_href=movement.detail_href,
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

    refund_hint = f"₹{refund_total:,.0f}" if refund_total > 0 else ""
    kpis = [
        UserDashboardKpi(
            key="checkins_week",
            label="Check-ins this week",
            value=f"{checkins_week:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="checkouts_week",
            label="Check-outs this week",
            value=f"{checkouts_week:,}",
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="pending_handover",
            label="Pending handover",
            value=f"{pending_handover:,}",
            hint_line="Keys and inventory" if pending_handover > 0 else "",
            hint_tone="warning" if pending_handover > 0 else "muted",
        ),
        UserDashboardKpi(
            key="deposit_refunds",
            label="Deposit refunds",
            value=f"{refund_count:,}",
            hint_line=refund_hint,
            hint_tone="info" if refund_total > 0 else "muted",
        ),
    ]

    return HostelCheckInCheckoutPageRead(
        page_title="Hostel Check-in / Checkout",
        page_subtitle="Arrivals, departures and handover",
        check_in_label="Check in",
        check_in_href="/college-admin/hostel/hostel-check-in-checkout?action=check-in",
        kpis=kpis,
        movements_section_title="Movements",
        table_headers=_TABLE_HEADERS,
        movement_rows=paged_rows,
        empty_table_message="No check-in or check-out movements yet.",
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
        generated_at=now,
    )