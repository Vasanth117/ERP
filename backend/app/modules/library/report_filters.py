"""Library report filter resolution."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.core.exceptions import AppError
from app.modules.college_admin.library_admin_models import LibraryBookCopyRecord
from app.modules.library.dashboard_filters import assert_branch
from app.modules.library.library_models import LibraryCatalogItem


@dataclass(frozen=True)
class LibraryReportContext:
    tenant_id: PydanticObjectId
    branch_code: str | None
    category: str | None
    member_category: str | None
    status: str | None
    date_from: date
    date_to: date
    window_start: datetime
    window_end: datetime
    scoped_copy_ids: frozenset[str] | None
    scoped_book_ids: frozenset[str] | None


def _date_bounds(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    if date_to < date_from:
        raise AppError(code="VALIDATION_ERROR", message="date_to must be on or after date_from", status_code=422)
    start = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    return start, end


async def build_report_context(
    tenant_id: PydanticObjectId,
    *,
    branch_code: str | None,
    category: str | None,
    member_category: str | None,
    status: str | None,
    date_from: date | None,
    date_to: date | None,
) -> LibraryReportContext:
    normalized_branch = await assert_branch(tenant_id, branch_code)
    df = date_from or date.today() - timedelta(days=30)
    dt = date_to or date.today()
    window_start, window_end = _date_bounds(df, dt)

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

    return LibraryReportContext(
        tenant_id=tenant_id,
        branch_code=normalized_branch,
        category=category.strip() if category else None,
        member_category=member_category.strip() if member_category else None,
        status=status.strip() if status else None,
        date_from=df,
        date_to=dt,
        window_start=window_start,
        window_end=window_end,
        scoped_copy_ids=scoped_copy_ids,
        scoped_book_ids=scoped_book_ids,
    )


def circulation_match(ctx: LibraryReportContext) -> dict:
    match: dict = {"tenant_id": ctx.tenant_id}
    if ctx.scoped_copy_ids is not None:
        match["copy_id"] = {"$in": list(ctx.scoped_copy_ids)}
    if ctx.scoped_book_ids is not None:
        match["book_id"] = {"$in": list(ctx.scoped_book_ids)}
    if ctx.branch_code:
        match["branch_code"] = ctx.branch_code
    return match


def copy_match(ctx: LibraryReportContext) -> dict:
    match: dict = {"tenant_id": ctx.tenant_id}
    if ctx.scoped_copy_ids is not None:
        match["copy_id"] = {"$in": list(ctx.scoped_copy_ids)}
    if ctx.scoped_book_ids is not None:
        match["book_id"] = {"$in": list(ctx.scoped_book_ids)}
    if ctx.status:
        match["status"] = ctx.status
    return match