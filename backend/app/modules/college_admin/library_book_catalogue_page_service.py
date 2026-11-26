"""Book catalogue management (CA 12.03)."""

from __future__ import annotations

import math

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.schemas import Pagination
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.hr_dashboard_page_service import _page_numbers
from app.modules.college_admin.library_admin_models import LibraryBookCopyRecord, LibraryBranch
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LibraryBookCataloguePageRead,
    LibraryBookCatalogueTableRow,
    PoliciesPagination,
    UserListFilterOption,
)
from app.modules.library.catalogue_enums import CatalogueSortField, CatalogueSortOrder
from app.modules.library.catalogue_service import search_catalogue_records
from app.modules.library.library_enums import LibraryCopyStatus
from app.modules.library.library_models import LibraryCopy

_PAGE_SIZE = 4
_TABLE_HEADERS = ["Title", "ISBN", "Author", "Category", "Copies", "Available"]


def _isbn_label(isbn: str | None, isbn13: str | None) -> str:
    if isbn13:
        return isbn13
    if isbn:
        return isbn
    return "—"


def _author_label(authors: list[str]) -> str:
    if not authors:
        return "—"
    return ", ".join(authors[:3]) + ("…" if len(authors) > 3 else "")


async def _copy_counts(
    tenant_id: PydanticObjectId,
    book_ids: list[str],
    *,
    branch_code: str | None,
) -> dict[str, tuple[int, int]]:
    if not book_ids:
        return {}
    allowed_copy_ids: set[str] | None = None
    if branch_code:
        records = await LibraryBookCopyRecord.find(
            Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
            Eq(LibraryBookCopyRecord.branch_code, branch_code.upper()),
        ).to_list()
        allowed_copy_ids = {r.copy_id for r in records}
        if not allowed_copy_ids:
            return {bid: (0, 0) for bid in book_ids}
    copies = await LibraryCopy.find({"tenant_id": tenant_id, "book_id": {"$in": book_ids}}).to_list()
    totals: dict[str, int] = {}
    available: dict[str, int] = {}
    for copy in copies:
        if allowed_copy_ids is not None and copy.copy_id not in allowed_copy_ids:
            continue
        totals[copy.book_id] = totals.get(copy.book_id, 0) + 1
        if copy.status == LibraryCopyStatus.AVAILABLE:
            available[copy.book_id] = available.get(copy.book_id, 0) + 1
    return {bid: (totals.get(bid, 0), available.get(bid, 0)) for bid in book_ids}


async def get_library_book_catalogue_page(
    scope: AccessScope,
    user: User,
    *,
    page: int = 1,
    page_size: int = _PAGE_SIZE,
    search: str | None = None,
    category: str | None = None,
    branch_code: str | None = None,
) -> LibraryBookCataloguePageRead:
    _ = user
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    page = max(1, page)
    page_size = max(1, min(page_size, 50))
    offset = (page - 1) * page_size

    branches = await LibraryBranch.find(Eq(LibraryBranch.tenant_id, tenant_id), Eq(LibraryBranch.is_active, True)).sort("name").to_list()
    branch_options = [UserListFilterOption(value="", label="All branches")]
    for branch in branches:
        branch_options.append(UserListFilterOption(value=branch.branch_code, label=branch.name))

    from app.modules.library.library_models import LibraryCatalogItem

    category_options = [UserListFilterOption(value="", label="All categories")]
    cat_rows = await LibraryCatalogItem.find(
        Eq(LibraryCatalogItem.tenant_id, tenant_id),
        Eq(LibraryCatalogItem.archived, False),
    ).to_list()
    for cat in sorted({r.category.strip() for r in cat_rows if r.category and r.category.strip()}):
        category_options.append(UserListFilterOption(value=cat, label=cat))

    search_q = (search or "").strip() or None
    category_q = (category or "").strip() or None
    branch_q = (branch_code or "").strip().upper() or None

    allowed_books: set[str] | None = None
    if branch_q:
        records = await LibraryBookCopyRecord.find(
            Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
            Eq(LibraryBookCopyRecord.branch_code, branch_q),
        ).to_list()
        allowed_books = {r.book_id for r in records}

    fetch_limit = 5000 if allowed_books is not None else page_size
    fetch_offset = 0 if allowed_books is not None else offset
    result = await search_catalogue_records(
        scope,
        Pagination(limit=fetch_limit, offset=fetch_offset),
        q=search_q,
        category=category_q,
        include_archived=False,
        sort_by=CatalogueSortField.TITLE,
        sort_order=CatalogueSortOrder.ASC,
    )

    catalogue_items = list(result.items)
    if allowed_books is not None:
        catalogue_items = [row for row in catalogue_items if row.book_id in allowed_books]
    total_rows = len(catalogue_items) if allowed_books is not None else result.total
    paged_items = catalogue_items[offset : offset + page_size] if allowed_books is not None else catalogue_items

    book_ids = [row.book_id for row in paged_items]
    copy_map = await _copy_counts(tenant_id, book_ids, branch_code=branch_q)

    table_rows: list[LibraryBookCatalogueTableRow] = []
    for row in paged_items:
        total, avail = copy_map.get(row.book_id, (0, 0))
        table_rows.append(
            LibraryBookCatalogueTableRow(
                book_id=row.book_id,
                title=row.title,
                isbn_label=_isbn_label(row.isbn, row.isbn13),
                author_label=_author_label(row.authors),
                category_label=row.category or "—",
                copies_label=f"{total:,}",
                available_label=f"{avail:,}",
                detail_href=f"/college-admin/library/book-catalogue?book_id={row.book_id}",
            )
        )

    total_pages = math.ceil(total_rows / page_size) if total_rows else 0
    showing_end = min(total_rows, offset + len(table_rows))
    catalogue_total = result.total if allowed_books is None else total_rows
    showing_label = f"Showing {showing_end:,} of {catalogue_total:,}"

    return LibraryBookCataloguePageRead(
        page_title="Book Catalogue",
        page_subtitle="Titles, authors and categories",
        export_label="Export",
        add_title_label="Add title",
        add_title_href="/college-admin/library/book-catalogue?action=create",
        search_placeholder="Search title, author or ISBN",
        category_filter_label="Category",
        branch_filter_label="Branch",
        category_options=category_options,
        branch_options=branch_options,
        catalogue_section_title="Book catalogue",
        table_headers=_TABLE_HEADERS,
        catalogue_rows=table_rows,
        empty_table_message="No catalogue titles match your filters.",
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