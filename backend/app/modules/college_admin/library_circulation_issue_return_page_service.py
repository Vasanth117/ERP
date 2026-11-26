"""Book issue and return management (CA 12.06)."""

from __future__ import annotations

import math
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.library_dashboard_page_service import (
    _ACTIVE_LOAN,
    _TABLE_HEADERS,
    _circulation_status,
    _loan_sort_key,
    _short_day,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LibraryCirculationIssueReturnPageRead,
    LibraryDashboardIssueReturnRow,
    PoliciesPagination,
)
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryFineStatus
from app.modules.library.library_models import LibraryCirculation, LibraryFine

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 3
_SECTION_TITLE = "Issue and return"


async def get_library_circulation_issue_return_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LibraryCirculationIssueReturnPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

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
            In(
                LibraryFine.status,
                [LibraryFineStatus.OPEN, LibraryFineStatus.PENDING_WAIVER, LibraryFineStatus.PENDING_WRITEOFF],
            ),
        ).to_list()
        if circ_ids
        else []
    )
    fine_by_circ: dict[str, float] = {}
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
    showing_label = f"Showing {showing_end:,} of {total_rows:,}"

    return LibraryCirculationIssueReturnPageRead(
        page_title="Book Issue & Return Management",
        page_subtitle="Issue, renew and return",
        issue_book_label="Issue book",
        issue_book_href="/college-admin/library/book-issue-return-management?action=issue",
        issue_return_section_title=_SECTION_TITLE,
        table_headers=list(_TABLE_HEADERS),
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
        generated_at=now,
    )