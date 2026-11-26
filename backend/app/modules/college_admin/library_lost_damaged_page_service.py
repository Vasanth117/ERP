"""Lost and damaged books reports (CA 12.10)."""

from __future__ import annotations

import math

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LibraryLostDamagedPageRead,
    LibraryLostDamagedTableRow,
    PoliciesPagination,
)
from app.modules.library.fine_enums import LibraryFineRecoveryStatus
from app.modules.library.fine_models import LibraryDamageReport
from app.modules.library.library_models import LibraryCatalogItem

_PAGE_SIZE = 3
_TABLE_HEADERS = ["Report", "Book", "Member", "Type", "Recovery", "Status"]


def _type_label(report_type: str) -> str:
    key = (report_type or "").lower()
    if key == "lost":
        return "Lost"
    if key == "damaged":
        return "Damaged"
    return report_type.replace("_", " ").title() if report_type else "—"


def _recovery_status(recovery_status: str) -> tuple[str, str]:
    key = (recovery_status or "").lower()
    if key in {LibraryFineRecoveryStatus.RECOVERED.value, "recovered", "paid"}:
        return "Recovered", "success"
    if key in {LibraryFineRecoveryStatus.WRITTEN_OFF.value, "closed"}:
        return "Recovered", "success"
    return "Open", "warning"


async def get_library_lost_damaged_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LibraryLostDamagedPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    query = LibraryDamageReport.find(Eq(LibraryDamageReport.tenant_id, tenant_id)).sort("-created_at")
    total = await query.count()
    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size
    reports = await query.skip(offset).limit(page_size).to_list()

    book_ids = {r.book_id for r in reports}
    titles = (
        await LibraryCatalogItem.find(
            Eq(LibraryCatalogItem.tenant_id, tenant_id),
            In(LibraryCatalogItem.book_id, list(book_ids)),
        ).to_list()
        if book_ids
        else []
    )
    title_by_book = {t.book_id: t.title for t in titles}

    user_ids = {r.member_user_id for r in reports}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users}

    table_rows: list[LibraryLostDamagedTableRow] = []
    for report in reports:
        member = user_by_id.get(report.member_user_id)
        member_name = member.full_name if member else "—"
        status_label, status_tone = _recovery_status(report.recovery_status)
        table_rows.append(
            LibraryLostDamagedTableRow(
                report_id=report.report_id,
                book_title=title_by_book.get(report.book_id, report.book_id),
                member_name=member_name,
                type_label=_type_label(report.report_type),
                recovery_label=f"₹{report.replacement_cost:,.0f}" if report.replacement_cost else "₹0",
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/library/lost-damaged-books?id={report.report_id}",
            )
        )

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(table_rows))
    showing_label = f"{showing_end:,} of {total:,}"

    return LibraryLostDamagedPageRead(
        page_title="Lost & Damaged Books",
        page_subtitle="Reports and recovery",
        report_loss_label="Report loss",
        report_loss_href="/college-admin/library/lost-damaged-books?action=report",
        lost_damaged_section_title="Lost and damaged",
        table_headers=_TABLE_HEADERS,
        report_rows=table_rows,
        empty_table_message="No loss or damage reports yet.",
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