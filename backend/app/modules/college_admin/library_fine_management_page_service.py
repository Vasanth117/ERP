"""Fine management overview (CA 12.09)."""

from __future__ import annotations

import math
from calendar import monthrange
from datetime import date
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LibraryFineManagementPageRead,
    LibraryFineManagementTableRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.library.fine_enums import LibraryFineApprovalStatus
from app.modules.library.fine_models import LibraryFineApproval
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryFineStatus
from app.modules.library.library_models import LibraryCirculation, LibraryFine

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3
_TABLE_HEADERS = ["Member", "Book", "Days late", "Fine", "Status"]
_OPEN_STATUSES = frozenset(
    {
        LibraryFineStatus.OPEN,
        LibraryFineStatus.PENDING_WAIVER,
        LibraryFineStatus.PENDING_WRITEOFF,
    },
)


def _fine_status(fine: LibraryFine, days_late: int) -> tuple[str, str]:
    if fine.status == LibraryFineStatus.PAID:
        return "Paid", "success"
    if fine.status == LibraryFineStatus.WAIVED or fine.status == LibraryFineStatus.WRITTEN_OFF:
        return "Paid", "success"
    if days_late > 0 or fine.fine_type == "overdue":
        if fine.balance > 0 and days_late > 7:
            return "Overdue", "error"
    if fine.balance > 0:
        return "Unpaid", "warning"
    return "Paid", "success"


def _month_window(day: date) -> tuple[date, date]:
    start = day.replace(day=1)
    _, last = monthrange(day.year, day.month)
    end = day.replace(day=last)
    return start, end


async def get_library_fine_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LibraryFineManagementPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()
    month_start, month_end = _month_window(today)

    fines = await LibraryFine.find(Eq(LibraryFine.tenant_id, tenant_id)).sort("-assessed_at").to_list()

    assessed_month = 0.0
    for fine in fines:
        assessed = fine.assessed_at.astimezone(_IST).date()
        if month_start <= assessed <= month_end:
            assessed_month += fine.amount

    collected = sum(f.amount_paid for f in fines)
    outstanding = sum(f.balance for f in fines if f.status in _OPEN_STATUSES or f.balance > 0)

    waiver_pending = await LibraryFineApproval.find(
        Eq(LibraryFineApproval.tenant_id, tenant_id),
        Eq(LibraryFineApproval.status, LibraryFineApprovalStatus.PENDING),
    ).count()

    kpis = [
        UserDashboardKpi(
            key="fines_assessed",
            label="Fines assessed",
            value=f"₹{assessed_month:,.0f}",
            hint_line="This month",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="collected",
            label="Collected",
            value=f"₹{collected:,.0f}",
            hint_line="Payments received",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="outstanding",
            label="Outstanding",
            value=f"₹{outstanding:,.0f}",
            hint_line="Open balances",
            hint_tone="warning" if outstanding else "success",
        ),
        UserDashboardKpi(
            key="waiver_requests",
            label="Waiver requests",
            value=f"{waiver_pending:,}",
            hint_line="Pending approval",
            hint_tone="warning" if waiver_pending else "success",
        ),
    ]

    circ_ids = {f.circulation_id for f in fines if f.circulation_id}
    circs = (
        await LibraryCirculation.find(
            Eq(LibraryCirculation.tenant_id, tenant_id),
            In(LibraryCirculation.circulation_id, list(circ_ids)),
        ).to_list()
        if circ_ids
        else []
    )
    circ_by_id = {c.circulation_id: c for c in circs}

    user_ids = {f.student_user_id for f in fines}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[LibraryFineManagementTableRow] = []
    for fine in fines:
        member = user_by_id.get(fine.student_user_id)
        member_name = member.full_name if member else "—"
        circ = circ_by_id.get(fine.circulation_id or "")
        book_title = circ.title if circ else (fine.book_id or "—")
        days_late = 0
        if circ and circ.due_at < today and circ.status in (
            LibraryCirculationStatus.ACTIVE,
            LibraryCirculationStatus.OVERDUE,
        ):
            days_late = (today - circ.due_at).days
        elif circ and circ.status == LibraryCirculationStatus.RETURNED and circ.returned_at:
            days_late = max(0, (circ.returned_at.astimezone(_IST).date() - circ.due_at).days)
        status_label, status_tone = _fine_status(fine, days_late)
        table_rows.append(
            LibraryFineManagementTableRow(
                fine_id=fine.fine_id,
                member_name=member_name,
                book_title=book_title,
                days_late_label=str(days_late),
                fine_label=f"₹{fine.balance:,.0f}" if fine.balance else f"₹{fine.amount:,.0f}",
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/library/fine-management?id={fine.fine_id}",
            )
        )

    total = len(table_rows)
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    total_pages = math.ceil(total / page_size) if total else 0
    start = (page - 1) * page_size
    paged_rows = table_rows[start : start + page_size]
    showing_end = min(total, start + len(paged_rows))
    showing_label = f"{showing_end:,} of {total:,}"

    return LibraryFineManagementPageRead(
        page_title="Fine Management",
        page_subtitle="Overdue fines and waivers",
        export_label="Export",
        kpis=kpis,
        fines_section_title="Fines",
        table_headers=_TABLE_HEADERS,
        fine_rows=paged_rows,
        empty_table_message="No fines recorded yet.",
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