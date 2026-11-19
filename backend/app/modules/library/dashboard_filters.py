"""Shared filter resolution for library dashboard queries."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.core.exceptions import AppError
from app.modules.college_admin.library_admin_models import LibraryBookCopyRecord, LibraryBranch
from app.modules.library.library_enums import LibraryCopyStatus, LibraryDashboardDateRange
from app.modules.library.library_models import LibraryCatalogItem


@dataclass(frozen=True)
class LibraryDashboardContext:
    tenant_id: PydanticObjectId
    branch_code: str | None
    category: str | None
    copy_status: LibraryCopyStatus | None
    anchor_date: date
    date_range: LibraryDashboardDateRange
    window_start: datetime
    window_end: datetime
    scoped_copy_ids: frozenset[str] | None
    scoped_book_ids: frozenset[str] | None


def dashboard_date_window(anchor: date, range_key: LibraryDashboardDateRange) -> tuple[datetime, datetime]:
    anchor_dt = datetime.combine(anchor, datetime.min.time(), tzinfo=timezone.utc)
    if range_key == LibraryDashboardDateRange.TODAY:
        return anchor_dt, anchor_dt + timedelta(days=1)
    if range_key == LibraryDashboardDateRange.WEEK:
        start = anchor_dt - timedelta(days=anchor.weekday())
        return start, start + timedelta(days=7)
    if range_key == LibraryDashboardDateRange.MONTH:
        start = anchor_dt.replace(day=1)
        if start.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        return start, end
    return anchor_dt - timedelta(days=120), anchor_dt + timedelta(days=1)


def calendar_day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


async def assert_branch(tenant_id: PydanticObjectId, branch_code: str | None) -> str | None:
    if not branch_code:
        return None
    normalized = branch_code.strip().upper()
    branch = await LibraryBranch.find_one(Eq(LibraryBranch.tenant_id, tenant_id), Eq(LibraryBranch.branch_code, normalized))
    if branch is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown library branch", status_code=422)
    return normalized


async def build_dashboard_context(
    tenant_id: PydanticObjectId,
    *,
    branch_code: str | None,
    category: str | None,
    copy_status: LibraryCopyStatus | None,
    anchor_date: date,
    date_range: LibraryDashboardDateRange,
) -> LibraryDashboardContext:
    normalized_branch = await assert_branch(tenant_id, branch_code)
    window_start, window_end = dashboard_date_window(anchor_date, date_range)

    scoped_copy_ids: frozenset[str] | None = None
    if normalized_branch:
        rows = await LibraryBookCopyRecord.find(
            Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
            Eq(LibraryBookCopyRecord.branch_code, normalized_branch),
        ).to_list()
        scoped_copy_ids = frozenset(r.copy_id for r in rows)

    scoped_book_ids: frozenset[str] | None = None
    if category:
        cat = category.strip()
        items = await LibraryCatalogItem.find(
            Eq(LibraryCatalogItem.tenant_id, tenant_id),
            Eq(LibraryCatalogItem.category, cat),
        ).to_list()
        scoped_book_ids = frozenset(i.book_id for i in items)

    return LibraryDashboardContext(
        tenant_id=tenant_id,
        branch_code=normalized_branch,
        category=category.strip() if category else None,
        copy_status=copy_status,
        anchor_date=anchor_date,
        date_range=date_range,
        window_start=window_start,
        window_end=window_end,
        scoped_copy_ids=scoped_copy_ids,
        scoped_book_ids=scoped_book_ids,
    )


def copy_match_filters(ctx: LibraryDashboardContext) -> dict:
    match: dict = {"tenant_id": ctx.tenant_id}
    if ctx.scoped_copy_ids is not None:
        match["copy_id"] = {"$in": list(ctx.scoped_copy_ids)}
    if ctx.scoped_book_ids is not None:
        match["book_id"] = {"$in": list(ctx.scoped_book_ids)}
    if ctx.copy_status is not None:
        match["status"] = ctx.copy_status.value
    return match


def catalogue_match_filters(ctx: LibraryDashboardContext) -> dict:
    match: dict = {"tenant_id": ctx.tenant_id, "archived": False}
    if ctx.category:
        match["category"] = ctx.category
    if ctx.scoped_book_ids is not None:
        match["book_id"] = {"$in": list(ctx.scoped_book_ids)}
    return match