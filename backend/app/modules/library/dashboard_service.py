"""Library dashboard service layer."""

from datetime import date

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.dashboard_filters import build_dashboard_context
from app.modules.library.dashboard_repository import LibraryDashboardRepository
from app.modules.library.dashboard_schemas import (
    AcquisitionSummary,
    BranchInventorySummary,
    CatalogueStats,
    CirculationTodayStats,
    CopyInventoryStats,
    DigitalResourceStats,
    LibraryActivityItem,
    LibraryAlertItem,
    LibraryDashboardDependencyNote,
    LibraryDashboardFilters,
    LibraryDashboardOverview,
    LibraryMemberStats,
    OutstandingFineSummary,
    UpcomingDueDateItem,
)
from app.modules.library.library_enums import LibraryCopyStatus, LibraryDashboardDateRange
from app.modules.library.policy import require_library_tenant_scope

_repo = LibraryDashboardRepository()


def _dependency_notes() -> list[LibraryDashboardDependencyNote]:
    return [
        LibraryDashboardDependencyNote(
            code="librarian_branch_assignment",
            message="Per-librarian branch assignment is not yet implemented; branch filters validate branch existence only.",
        ),
        LibraryDashboardDependencyNote(
            code="damaged_copies",
            message="Damaged copy counts use LibraryCopyStatus.MAINTENANCE until a dedicated damaged status exists.",
        ),
    ]


async def _context(
    scope: AccessScope,
    *,
    branch_code: str | None,
    category: str | None,
    copy_status: LibraryCopyStatus | None,
    anchor_date: date | None,
    date_range: LibraryDashboardDateRange,
):
    tenant_id = require_library_tenant_scope(scope)
    anchor = anchor_date or date.today()
    return await build_dashboard_context(
        tenant_id,
        branch_code=branch_code,
        category=category,
        copy_status=copy_status,
        anchor_date=anchor,
        date_range=date_range,
    )


def _filters_from_ctx(ctx) -> LibraryDashboardFilters:
    return LibraryDashboardFilters(
        branch_code=ctx.branch_code,
        category=ctx.category,
        copy_status=ctx.copy_status,
        anchor_date=ctx.anchor_date,
        date_range=ctx.date_range,
    )


async def get_library_dashboard_overview(
    scope: AccessScope,
    user: User,
    *,
    branch_code: str | None = None,
    category: str | None = None,
    copy_status: LibraryCopyStatus | None = None,
    anchor_date: date | None = None,
    date_range: LibraryDashboardDateRange = LibraryDashboardDateRange.WEEK,
) -> LibraryDashboardOverview:
    _ = user
    ctx = await _context(
        scope,
        branch_code=branch_code,
        category=category,
        copy_status=copy_status,
        anchor_date=anchor_date,
        date_range=date_range,
    )
    today = date.today()
    return LibraryDashboardOverview(
        filters=_filters_from_ctx(ctx),
        catalogue=await _repo.catalogue_stats(ctx),
        copies=await _repo.copy_inventory(ctx),
        members=await _repo.member_stats(ctx),
        circulation_today=await _repo.circulation_today(ctx, activity_day=today),
        pending_reservations=await _repo.pending_reservations(ctx),
        outstanding_fines=await _repo.outstanding_fines(ctx),
        acquisitions=await _repo.acquisition_summary(ctx),
        digital=await _repo.digital_stats(ctx),
        branch_inventory=await _repo.branch_inventory(ctx),
        alerts=await _repo.alerts(ctx),
        dependency_notes=_dependency_notes(),
    )


async def get_catalogue_stats(
    scope: AccessScope,
    *,
    branch_code: str | None = None,
    category: str | None = None,
    anchor_date: date | None = None,
    date_range: LibraryDashboardDateRange = LibraryDashboardDateRange.WEEK,
) -> CatalogueStats:
    ctx = await _context(scope, branch_code=branch_code, category=category, copy_status=None, anchor_date=anchor_date, date_range=date_range)
    return await _repo.catalogue_stats(ctx)


async def get_copy_stats(
    scope: AccessScope,
    *,
    branch_code: str | None = None,
    category: str | None = None,
    copy_status: LibraryCopyStatus | None = None,
    anchor_date: date | None = None,
    date_range: LibraryDashboardDateRange = LibraryDashboardDateRange.WEEK,
) -> CopyInventoryStats:
    ctx = await _context(
        scope,
        branch_code=branch_code,
        category=category,
        copy_status=copy_status,
        anchor_date=anchor_date,
        date_range=date_range,
    )
    return await _repo.copy_inventory(ctx)


async def get_member_stats(
    scope: AccessScope,
    *,
    branch_code: str | None = None,
    anchor_date: date | None = None,
    date_range: LibraryDashboardDateRange = LibraryDashboardDateRange.WEEK,
) -> LibraryMemberStats:
    ctx = await _context(scope, branch_code=branch_code, category=None, copy_status=None, anchor_date=anchor_date, date_range=date_range)
    return await _repo.member_stats(ctx)


async def get_circulation_today(
    scope: AccessScope,
    *,
    branch_code: str | None = None,
    category: str | None = None,
    activity_date: date | None = None,
) -> CirculationTodayStats:
    ctx = await _context(
        scope,
        branch_code=branch_code,
        category=category,
        copy_status=None,
        anchor_date=activity_date or date.today(),
        date_range=LibraryDashboardDateRange.TODAY,
    )
    return await _repo.circulation_today(ctx, activity_day=activity_date or date.today())


async def get_pending_reservations(scope: AccessScope, *, branch_code: str | None = None, category: str | None = None) -> int:
    ctx = await _context(
        scope,
        branch_code=branch_code,
        category=category,
        copy_status=None,
        anchor_date=date.today(),
        date_range=LibraryDashboardDateRange.WEEK,
    )
    return await _repo.pending_reservations(ctx)


async def get_outstanding_fines(scope: AccessScope) -> OutstandingFineSummary:
    ctx = await _context(scope, branch_code=None, category=None, copy_status=None, anchor_date=date.today(), date_range=LibraryDashboardDateRange.WEEK)
    return await _repo.outstanding_fines(ctx)


async def get_acquisition_stats(
    scope: AccessScope,
    *,
    branch_code: str | None = None,
    anchor_date: date | None = None,
    date_range: LibraryDashboardDateRange = LibraryDashboardDateRange.MONTH,
) -> AcquisitionSummary:
    ctx = await _context(scope, branch_code=branch_code, category=None, copy_status=None, anchor_date=anchor_date, date_range=date_range)
    return await _repo.acquisition_summary(ctx)


async def get_digital_stats(scope: AccessScope) -> DigitalResourceStats:
    ctx = await _context(scope, branch_code=None, category=None, copy_status=None, anchor_date=date.today(), date_range=LibraryDashboardDateRange.WEEK)
    return await _repo.digital_stats(ctx)


async def get_branch_inventory(scope: AccessScope, *, branch_code: str | None = None) -> list[BranchInventorySummary]:
    ctx = await _context(scope, branch_code=branch_code, category=None, copy_status=None, anchor_date=date.today(), date_range=LibraryDashboardDateRange.WEEK)
    return await _repo.branch_inventory(ctx)


async def get_upcoming_due_dates(
    scope: AccessScope,
    pagination: Pagination,
    *,
    branch_code: str | None = None,
    category: str | None = None,
) -> Page[UpcomingDueDateItem]:
    ctx = await _context(
        scope,
        branch_code=branch_code,
        category=category,
        copy_status=None,
        anchor_date=date.today(),
        date_range=LibraryDashboardDateRange.WEEK,
    )
    items, total = await _repo.upcoming_due_dates(ctx, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_recent_activities(
    scope: AccessScope,
    pagination: Pagination,
    *,
    branch_code: str | None = None,
    anchor_date: date | None = None,
    date_range: LibraryDashboardDateRange = LibraryDashboardDateRange.WEEK,
) -> Page[LibraryActivityItem]:
    ctx = await _context(
        scope,
        branch_code=branch_code,
        category=None,
        copy_status=None,
        anchor_date=anchor_date,
        date_range=date_range,
    )
    items, total = await _repo.recent_activities(ctx, limit=pagination.limit, offset=pagination.offset)
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def get_dashboard_alerts(
    scope: AccessScope,
    *,
    branch_code: str | None = None,
    category: str | None = None,
    copy_status: LibraryCopyStatus | None = None,
) -> list[LibraryAlertItem]:
    ctx = await _context(
        scope,
        branch_code=branch_code,
        category=category,
        copy_status=copy_status,
        anchor_date=date.today(),
        date_range=LibraryDashboardDateRange.WEEK,
    )
    return await _repo.alerts(ctx)