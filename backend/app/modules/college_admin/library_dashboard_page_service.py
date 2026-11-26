"""Library administration overview dashboard (CA 12.01)."""

from __future__ import annotations

import math
from datetime import date
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.library_admin_models import LibraryAcquisition, LibraryBranch
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LibraryDashboardIssueReturnRow,
    LibraryDashboardPageRead,
    PoliciesPagination,
    StudentAdminWorkQueueItem,
    UserDashboardKpi,
)
from app.modules.library.acquisition_enums import LibraryAcquisitionStatus
from app.modules.library.dashboard_service import get_library_dashboard_overview
from app.modules.library.library_enums import (
    LibraryCirculationStatus,
    LibraryCopyStatus,
    LibraryDashboardDateRange,
    LibraryFineStatus,
    LibraryReservationStatus,
)
from app.modules.library.library_models import LibraryCirculation, LibraryCopy, LibraryFine, LibraryReservation

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3
_TABLE_HEADERS = ["Member", "Book", "Issued", "Due", "Fine", "Status"]
_ACTIVE_LOAN = frozenset({LibraryCirculationStatus.ACTIVE, LibraryCirculationStatus.OVERDUE})


def _short_day(d: date) -> str:
    return d.strftime("%d %b")


def _circulation_status(circ: LibraryCirculation, today: date) -> tuple[str, str]:
    if circ.status == LibraryCirculationStatus.OVERDUE or circ.due_at < today:
        return "Overdue", "error"
    if circ.due_at == today:
        return "Due today", "warning"
    if circ.status == LibraryCirculationStatus.ACTIVE:
        return "Issued", "success"
    return circ.status.value.replace("_", " ").title(), "muted"


def _loan_sort_key(circ: LibraryCirculation, today: date) -> tuple[int, date]:
    label, _ = _circulation_status(circ, today)
    priority = {"Overdue": 0, "Due today": 1, "Issued": 2}.get(label, 3)
    return priority, circ.due_at


async def get_library_dashboard_page(
    scope: AccessScope,
    user: User,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LibraryDashboardPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    overview = await get_library_dashboard_overview(
        scope,
        user,
        date_range=LibraryDashboardDateRange.WEEK,
    )

    branches = await LibraryBranch.find(Eq(LibraryBranch.tenant_id, tenant_id), Eq(LibraryBranch.is_active, True)).to_list()
    branch_count = len(branches)
    primary_label = "Central library"
    if branches:
        main = next((b for b in branches if "central" in (b.name or "").lower()), branches[0])
        primary_label = main.name.strip() if main.name else primary_label
        if branch_count > 1:
            branch_hint = f"Across {branch_count} branches"
        else:
            branch_hint = f"Across {branch_count} branch" if branch_count == 1 else "No branches configured"
    else:
        branch_hint = "No branches configured"

    circ_today = overview.circulation_today
    fines_total = overview.outstanding_fines.total_amount
    overdue_count = overview.copies.overdue_loans

    kpis = [
        UserDashboardKpi(
            key="titles",
            label="Titles",
            value=f"{overview.catalogue.total_titles:,}",
            hint_line=branch_hint,
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="issued_today",
            label="Issued today",
            value=f"{circ_today.issues:,}",
            hint_line=f"Returned {circ_today.returns:,}",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="overdue",
            label="Overdue",
            value=f"{overdue_count:,}",
            hint_line=f"Fines ₹{fines_total:,.0f}",
            hint_tone="error" if overdue_count else "success",
        ),
        UserDashboardKpi(
            key="active_members",
            label="Active members",
            value=f"{overview.members.active:,}",
            hint_line="Students and staff",
            hint_tone="info",
        ),
    ]

    loans = await LibraryCirculation.find(
        Eq(LibraryCirculation.tenant_id, tenant_id),
        In(LibraryCirculation.status, list(_ACTIVE_LOAN)),
    ).to_list()

    for row in loans:
        if row.status == LibraryCirculationStatus.ACTIVE and row.due_at < today:
            row.status = LibraryCirculationStatus.OVERDUE
    loans.sort(key=lambda c: _loan_sort_key(c, today))

    user_ids = {row.student_user_id for row in loans}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    circ_ids = {row.circulation_id for row in loans}
    fines = (
        await LibraryFine.find(
            Eq(LibraryFine.tenant_id, tenant_id),
            In(LibraryFine.circulation_id, list(circ_ids)),
            In(LibraryFine.status, [LibraryFineStatus.OPEN, LibraryFineStatus.PENDING_WAIVER, LibraryFineStatus.PENDING_WRITEOFF]),
        ).to_list()
        if circ_ids
        else []
    )
    fine_by_circ = {}
    for fine in fines:
        if fine.circulation_id:
            fine_by_circ[fine.circulation_id] = fine_by_circ.get(fine.circulation_id, 0.0) + fine.balance

    table_rows: list[LibraryDashboardIssueReturnRow] = []
    for circ in loans:
        member = user_by_id.get(circ.student_user_id)
        member_name = member.full_name if member else "—"
        balance = fine_by_circ.get(circ.circulation_id, 0.0)
        status_label, status_tone = _circulation_status(circ, today)
        issued = circ.issued_at.astimezone(_IST).date()
        table_rows.append(
            LibraryDashboardIssueReturnRow(
                circulation_id=circ.circulation_id,
                member_name=member_name,
                book_title=circ.title,
                issued_label=_short_day(issued),
                due_label=_short_day(circ.due_at),
                fine_label=f"₹{balance:,.0f}" if balance else "₹0",
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/library/book-issue-return-management?id={circ.circulation_id}",
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

    lost_damaged = await LibraryCopy.find(
        Eq(LibraryCopy.tenant_id, tenant_id),
        In(LibraryCopy.status, [LibraryCopyStatus.LOST, LibraryCopyStatus.DAMAGED, LibraryCopyStatus.MAINTENANCE]),
    ).count()

    reservations_ready = await LibraryReservation.find(
        Eq(LibraryReservation.tenant_id, tenant_id),
        Eq(LibraryReservation.status, LibraryReservationStatus.READY),
    ).count()

    acquisitions_pending = await LibraryAcquisition.find(
        Eq(LibraryAcquisition.tenant_id, tenant_id),
        Eq(LibraryAcquisition.approval_status, LibraryAcquisitionStatus.PENDING_APPROVAL.value),
    ).count()

    needs_attention = [
        StudentAdminWorkQueueItem(
            key="lost_damaged",
            title="Lost / damaged reports",
            subtitle="open",
            count=lost_damaged,
            href="/college-admin/library/lost-damaged-books",
            action_label="Review →",
            icon_slug="alert-circle",
        ),
        StudentAdminWorkQueueItem(
            key="reservations_ready",
            title="Reservations ready",
            subtitle="members",
            count=reservations_ready,
            href="/college-admin/library/reservation-management",
            action_label="Open →",
            icon_slug="clock",
        ),
        StudentAdminWorkQueueItem(
            key="acquisitions_approval",
            title="Acquisitions awaiting approval",
            subtitle="pending",
            count=acquisitions_pending,
            href="/college-admin/library/book-acquisition",
            action_label="View →",
            icon_slug="file-text",
        ),
    ]

    page_subtitle = f"{primary_label} • {today.strftime('%d %b %Y')}"

    return LibraryDashboardPageRead(
        page_title="Library Dashboard",
        page_subtitle=page_subtitle,
        export_label="Export",
        open_portal_label="Open Library portal",
        open_portal_href="/college-admin/library/book-issue-return-management",
        kpis=kpis,
        issue_return_section_title="Issue and return",
        issue_return_view_all_href="/college-admin/library/book-issue-return-management",
        issue_return_view_all_label="View all →",
        table_headers=_TABLE_HEADERS,
        issue_return_rows=paged_rows,
        empty_table_message="No active loans yet.",
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
        needs_attention_title="Needs attention",
        needs_attention_items=needs_attention,
        generated_at=now,
    )