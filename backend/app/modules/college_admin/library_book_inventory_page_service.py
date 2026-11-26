"""Book inventory overview (CA 12.04)."""

from __future__ import annotations

import math

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.library_admin_models import LibraryBookCopyRecord, LibraryBranch
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LibraryBookInventoryCopyRow,
    LibraryBookInventoryPageRead,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.library.library_enums import LibraryCopyCondition, LibraryCopyStatus
from app.modules.library.library_models import LibraryCatalogItem, LibraryCopy

_PAGE_SIZE = 3
_TABLE_HEADERS = ["Accession no.", "Title", "Branch", "Shelf", "Condition", "Status"]
_ISSUED = frozenset({LibraryCopyStatus.ISSUED, LibraryCopyStatus.RESERVED})
_LOST_DAMAGED = frozenset(
    {LibraryCopyStatus.LOST, LibraryCopyStatus.DAMAGED, LibraryCopyStatus.MAINTENANCE},
)


def _condition_label(condition: LibraryCopyCondition) -> str:
    return condition.value.replace("_", " ").title()


def _status(copy: LibraryCopy) -> tuple[str, str]:
    if copy.status == LibraryCopyStatus.AVAILABLE:
        return "Available", "success"
    if copy.status in _ISSUED:
        return "On loan", "info"
    if copy.status in _LOST_DAMAGED:
        return "Repair" if copy.status == LibraryCopyStatus.MAINTENANCE else copy.status.value.replace("_", " ").title(), "warning"
    if copy.status == LibraryCopyStatus.WITHDRAWN:
        return "Withdrawn", "muted"
    return copy.status.value.replace("_", " ").title(), "muted"


async def get_library_book_inventory_page(
    scope: AccessScope,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
) -> LibraryBookInventoryPageRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    total = await LibraryCopy.find(Eq(LibraryCopy.tenant_id, tenant_id)).count()
    available = await LibraryCopy.find(
        Eq(LibraryCopy.tenant_id, tenant_id),
        Eq(LibraryCopy.status, LibraryCopyStatus.AVAILABLE),
    ).count()
    on_loan = await LibraryCopy.find(
        Eq(LibraryCopy.tenant_id, tenant_id),
        In(LibraryCopy.status, list(_ISSUED)),
    ).count()
    lost_damaged = await LibraryCopy.find(
        Eq(LibraryCopy.tenant_id, tenant_id),
        In(LibraryCopy.status, list(_LOST_DAMAGED)),
    ).count()
    available_pct = int(round((available / total) * 100)) if total else 0

    kpis = [
        UserDashboardKpi(
            key="copies",
            label="Copies",
            value=f"{total:,}",
            hint_line="Physical copies",
            hint_tone="neutral",
        ),
        UserDashboardKpi(
            key="available",
            label="Available",
            value=f"{available:,}",
            hint_line=f"{available_pct}%",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="on_loan",
            label="On loan",
            value=f"{on_loan:,}",
            hint_line="Issued copies",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="lost_damaged",
            label="Lost / damaged",
            value=f"{lost_damaged:,}",
            hint_line="Repair or write-off",
            hint_tone="warning" if lost_damaged else "success",
        ),
    ]

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size

    copies = (
        await LibraryCopy.find(Eq(LibraryCopy.tenant_id, tenant_id))
        .sort("-updated_at")
        .skip(offset)
        .limit(page_size)
        .to_list()
    )

    branches = await LibraryBranch.find(Eq(LibraryBranch.tenant_id, tenant_id)).to_list()
    branch_by_code = {b.branch_code.upper(): b.name for b in branches}

    book_ids = {c.book_id for c in copies}
    titles = await LibraryCatalogItem.find(
        Eq(LibraryCatalogItem.tenant_id, tenant_id),
        In(LibraryCatalogItem.book_id, list(book_ids)),
    ).to_list() if book_ids else []
    title_by_book = {t.book_id: t.title for t in titles}

    copy_ids = [c.copy_id for c in copies]
    admin_rows = (
        await LibraryBookCopyRecord.find(
            Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
            In(LibraryBookCopyRecord.copy_id, copy_ids),
        ).to_list()
        if copy_ids
        else []
    )
    admin_by_copy = {r.copy_id: r for r in admin_rows}

    table_rows: list[LibraryBookInventoryCopyRow] = []
    for copy in copies:
        admin = admin_by_copy.get(copy.copy_id)
        accession = admin.accession_number if admin and admin.accession_number else copy.barcode
        shelf = copy.shelf_location_code or (admin.shelf_location_code if admin else None) or "—"
        branch_code = (copy.branch_code or (admin.branch_code if admin else None) or "").upper()
        branch_label = branch_by_code.get(branch_code, branch_code or "—")
        status_label, status_tone = _status(copy)
        table_rows.append(
            LibraryBookInventoryCopyRow(
                copy_id=copy.copy_id,
                accession_label=accession,
                title=title_by_book.get(copy.book_id, copy.book_id),
                branch_label=branch_label,
                shelf_label=shelf,
                condition_label=_condition_label(copy.condition),
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/library/book-inventory?copy_id={copy.copy_id}",
            )
        )

    total_pages = math.ceil(total / page_size) if total else 0
    showing_end = min(total, offset + len(table_rows))
    showing_label = f"Showing {showing_end:,} of {total:,}"

    return LibraryBookInventoryPageRead(
        page_title="Book Inventory",
        page_subtitle="Copies, shelves and condition",
        stock_verification_label="Stock verification",
        stock_verification_href="/college-admin/library/book-inventory?action=stock-verification",
        kpis=kpis,
        copies_section_title="Copies",
        table_headers=_TABLE_HEADERS,
        copy_rows=table_rows,
        empty_table_message="No copies in inventory yet.",
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