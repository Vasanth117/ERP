"""Hostel fee management (CA 13.08)."""

from __future__ import annotations

import math
from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hostel_fees_page_shared import (
    billing_record_paid_amount,
    demand_balance,
    demand_paid_amount,
    deposit_held_amount,
    fee_status_label,
    format_inr,
    format_inr_compact,
    is_hostel_fee_demand,
    pick_academic_year_label,
)
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    HostelFeeManagementPageRead,
    HostelFeeManagementTableRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.hostel.hostel_models import HostelRoomAllocation
from app.modules.hostel.mess_models import HostelMessBillingPeriod, HostelMessBillingRecord
from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus

_PAGE_SIZE = 3
_TABLE_HEADERS = ["Resident", "Room", "Billed", "Paid", "Balance", "Status"]
_EXCLUDED = frozenset({HostelResidentStatus.CHECKED_OUT, HostelResidentStatus.CANCELLED})


async def get_hostel_fee_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> HostelFeeManagementPageRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = date.today()

    residents = await HostelResident.find(Eq(HostelResident.tenant_id, tenant_id)).to_list()
    residents = [r for r in residents if r.status not in _EXCLUDED]
    resident_by_student = {r.student_user_id: r for r in residents}

    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    hostel_demands = [d for d in demands if is_hostel_fee_demand(d)]
    billing_rows = await HostelMessBillingRecord.find(Eq(HostelMessBillingRecord.tenant_id, tenant_id)).to_list()
    periods = await HostelMessBillingPeriod.find(Eq(HostelMessBillingPeriod.tenant_id, tenant_id)).sort("-period_start").to_list()
    period_labels = [p.label for p in periods if p.label]
    ay_label = pick_academic_year_label(demands=hostel_demands, period_labels=period_labels)

    room_allocs = await HostelRoomAllocation.find(
        Eq(HostelRoomAllocation.tenant_id, tenant_id),
        Eq(HostelRoomAllocation.published, True),
    ).to_list()
    rent_by_student = {a.student_user_id: a.fee_amount for a in room_allocs if a.fee_amount}

    totals: dict[PydanticObjectId, dict[str, float]] = {}
    overdue_flags: dict[PydanticObjectId, bool] = {}

    for demand in hostel_demands:
        paid = await demand_paid_amount(tenant_id, demand.demand_id)
        bucket = totals.setdefault(demand.student_user_id, {"billed": 0.0, "paid": 0.0, "balance": 0.0})
        bucket["billed"] += demand.amount + (demand.late_fee or 0)
        bucket["paid"] += paid
        bucket["balance"] += demand_balance(demand, paid)
        if demand.due_date < today and demand.status not in (FeeDemandStatus.PAID, FeeDemandStatus.WAIVED):
            overdue_flags[demand.student_user_id] = True

    for record in billing_rows:
        bucket = totals.setdefault(record.student_user_id, {"billed": 0.0, "paid": 0.0, "balance": 0.0})
        paid = billing_record_paid_amount(record)
        bucket["billed"] += record.amount
        bucket["paid"] += paid
        bucket["balance"] += max(0.0, record.amount - paid)

    for student_id, rent in rent_by_student.items():
        if rent <= 0:
            continue
        bucket = totals.setdefault(student_id, {"billed": 0.0, "paid": 0.0, "balance": 0.0})
        if bucket["billed"] == 0:
            bucket["billed"] += rent
            bucket["balance"] += rent

    for resident in residents:
        totals.setdefault(resident.student_user_id, {"billed": 0.0, "paid": 0.0, "balance": 0.0})

    total_billed = sum(v["billed"] for v in totals.values())
    total_paid = sum(v["paid"] for v in totals.values())
    total_outstanding = sum(v["balance"] for v in totals.values())
    outstanding_residents = sum(1 for v in totals.values() if v["balance"] > 0)
    deposits_held = sum(deposit_held_amount(r.clearance_status) for r in residents)

    collection_pct = (total_paid / total_billed * 100) if total_billed > 0 else 0.0
    billed_hint = ay_label or ""
    collected_hint = f"{collection_pct:.1f}%" if total_billed > 0 else ""
    outstanding_hint = f"{outstanding_residents:,} residents" if outstanding_residents else ""

    kpis = [
        UserDashboardKpi(
            key="billed",
            label="Billed",
            value=format_inr_compact(total_billed),
            hint_line=billed_hint,
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="collected",
            label="Collected",
            value=format_inr_compact(total_paid),
            hint_line=collected_hint,
            hint_tone="success" if collection_pct >= 80 else "warning",
        ),
        UserDashboardKpi(
            key="outstanding",
            label="Outstanding",
            value=format_inr_compact(total_outstanding),
            hint_line=outstanding_hint,
            hint_tone="warning" if outstanding_residents else "muted",
        ),
        UserDashboardKpi(
            key="deposits_held",
            label="Deposits held",
            value=format_inr_compact(deposits_held),
            hint_line="",
            hint_tone="muted",
        ),
    ]

    user_ids = set(totals.keys())
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[HostelFeeManagementTableRow] = []
    for student_id, amounts in totals.items():
        if amounts["billed"] <= 0 and amounts["paid"] <= 0 and amounts["balance"] <= 0:
            if student_id not in resident_by_student:
                continue
        user = user_by_id.get(student_id)
        resident = resident_by_student.get(student_id)
        room = resident.room_code if resident else "—"
        if room == "—" and student_id in rent_by_student:
            alloc = next((a for a in room_allocs if a.student_user_id == student_id), None)
            if alloc:
                room = alloc.room_number or "—"
        billed = amounts["billed"]
        paid = amounts["paid"]
        balance = amounts["balance"]
        status_label, status_tone = fee_status_label(
            balance=balance,
            overdue=overdue_flags.get(student_id, False),
            paid=paid,
            billed=billed,
        )
        detail_id = resident.resident_id if resident else str(student_id)
        table_rows.append(
            HostelFeeManagementTableRow(
                row_key=detail_id,
                resident_label=user.full_name if user else "—",
                room_label=room,
                billed_label=format_inr(billed),
                paid_label=format_inr(paid),
                balance_label=format_inr(balance),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/hostel/hostel-fee-management?id={detail_id}",
            )
        )

    table_rows.sort(key=lambda r: (0 if r.status_tone in {"warning", "error"} else 1, r.resident_label))

    total = len(table_rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total, start + len(paged_rows))
    count_label = f"{showing_end} of {total}"

    return HostelFeeManagementPageRead(
        page_title="Hostel Fee Management",
        page_subtitle="Room rent, mess and deposits",
        generate_fees_label="Generate fees",
        generate_fees_href="/college-admin/hostel/hostel-fee-management?action=generate",
        kpis=kpis,
        fees_section_title="Hostel fees",
        table_headers=_TABLE_HEADERS,
        fee_rows=paged_rows,
        empty_table_message="No hostel fee records for this period.",
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
        academic_year_label=ay_label,
        generated_at=now,
    )