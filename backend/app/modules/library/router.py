"""Library module — librarian portal (dashboard phase 1)."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.dashboard_schemas import (
    AcquisitionSummary,
    BranchInventorySummary,
    CatalogueStats,
    CirculationTodayStats,
    CopyInventoryStats,
    DigitalResourceStats,
    LibraryActivityItem,
    LibraryAlertItem,
    LibraryDashboardOverview,
    LibraryMemberStats,
    OutstandingFineSummary,
    UpcomingDueDateItem,
)
from app.modules.library.dashboard_service import (
    get_acquisition_stats,
    get_branch_inventory,
    get_catalogue_stats,
    get_circulation_today,
    get_copy_stats,
    get_dashboard_alerts,
    get_digital_stats,
    get_library_dashboard_overview,
    get_member_stats,
    get_outstanding_fines,
    get_pending_reservations,
    get_recent_activities,
    get_upcoming_due_dates,
)
from app.modules.library.deps import librarian_user
from app.modules.library.catalogue_router import router as catalogue_router
from app.modules.library.inventory_router import router as inventory_router
from app.modules.library.member_router import router as member_router
from app.modules.library.circulation_router import router as circulation_router
from app.modules.library.reservation_router import router as reservation_router
from app.modules.library.fine_router import router as fine_router
from app.modules.library.acquisition_router import router as acquisition_router
from app.modules.library.digital_router import router as digital_router
from app.modules.library.notification_router import router as notification_router
from app.modules.library.report_router import router as report_router
from app.modules.library.facility_router import router as facility_router
from app.modules.library.library_enums import LibraryCopyStatus, LibraryDashboardDateRange

router = APIRouter()
router.include_router(facility_router)
router.include_router(catalogue_router)
router.include_router(inventory_router)
router.include_router(member_router)
router.include_router(circulation_router)
router.include_router(reservation_router)
router.include_router(fine_router)
router.include_router(acquisition_router)
router.include_router(digital_router)
router.include_router(notification_router)
router.include_router(report_router)


@router.get("/me/dashboard", response_model=ApiResponse[LibraryDashboardOverview])
async def library_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query(description="Filter by library branch code")] = None,
    category: Annotated[str | None, Query(description="Filter catalogue/copy metrics by category")] = None,
    copy_status: Annotated[LibraryCopyStatus | None, Query(description="Filter physical copies by status")] = None,
    anchor_date: Annotated[date | None, Query(description="Dashboard anchor date (UTC calendar day)")] = None,
    date_range: Annotated[LibraryDashboardDateRange, Query(alias="range")] = LibraryDashboardDateRange.WEEK,
) -> ApiResponse[LibraryDashboardOverview]:
    data = await get_library_dashboard_overview(
        scope,
        user,
        branch_code=branch_code,
        category=category,
        copy_status=copy_status,
        anchor_date=anchor_date,
        date_range=date_range,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/catalogue", response_model=ApiResponse[CatalogueStats])
async def library_dashboard_catalogue_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[LibraryDashboardDateRange, Query(alias="range")] = LibraryDashboardDateRange.WEEK,
) -> ApiResponse[CatalogueStats]:
    data = await get_catalogue_stats(scope, branch_code=branch_code, category=category, anchor_date=anchor_date, date_range=date_range)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/copies", response_model=ApiResponse[CopyInventoryStats])
async def library_dashboard_copies_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    copy_status: Annotated[LibraryCopyStatus | None, Query()] = None,
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[LibraryDashboardDateRange, Query(alias="range")] = LibraryDashboardDateRange.WEEK,
) -> ApiResponse[CopyInventoryStats]:
    data = await get_copy_stats(
        scope,
        branch_code=branch_code,
        category=category,
        copy_status=copy_status,
        anchor_date=anchor_date,
        date_range=date_range,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/members", response_model=ApiResponse[LibraryMemberStats])
async def library_dashboard_members_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[LibraryDashboardDateRange, Query(alias="range")] = LibraryDashboardDateRange.WEEK,
) -> ApiResponse[LibraryMemberStats]:
    data = await get_member_stats(scope, branch_code=branch_code, anchor_date=anchor_date, date_range=date_range)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/circulation/today", response_model=ApiResponse[CirculationTodayStats])
async def library_dashboard_circulation_today_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    activity_date: Annotated[date | None, Query(description="UTC calendar day for issue/return counts")] = None,
) -> ApiResponse[CirculationTodayStats]:
    data = await get_circulation_today(scope, branch_code=branch_code, category=category, activity_date=activity_date)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/reservations/pending", response_model=ApiResponse[dict])
async def library_dashboard_pending_reservations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    count = await get_pending_reservations(scope, branch_code=branch_code, category=category)
    return success_response({"pending_reservations": count}, request_id=get_request_id())


@router.get("/me/dashboard/fines/outstanding", response_model=ApiResponse[OutstandingFineSummary])
async def library_dashboard_fines_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[OutstandingFineSummary]:
    data = await get_outstanding_fines(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/acquisitions", response_model=ApiResponse[AcquisitionSummary])
async def library_dashboard_acquisitions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[LibraryDashboardDateRange, Query(alias="range")] = LibraryDashboardDateRange.MONTH,
) -> ApiResponse[AcquisitionSummary]:
    data = await get_acquisition_stats(scope, branch_code=branch_code, anchor_date=anchor_date, date_range=date_range)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/digital", response_model=ApiResponse[DigitalResourceStats])
async def library_dashboard_digital_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[DigitalResourceStats]:
    data = await get_digital_stats(scope)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/branches/inventory", response_model=ApiResponse[list[BranchInventorySummary]])
async def library_dashboard_branch_inventory_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[BranchInventorySummary]]:
    data = await get_branch_inventory(scope, branch_code=branch_code)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/due-dates", response_model=ApiResponse[Page[UpcomingDueDateItem]])
async def library_dashboard_due_dates_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[UpcomingDueDateItem]]:
    data = await get_upcoming_due_dates(scope, pagination, branch_code=branch_code, category=category)
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/activities", response_model=ApiResponse[Page[LibraryActivityItem]])
async def library_dashboard_activities_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str | None, Query()] = None,
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[LibraryDashboardDateRange, Query(alias="range")] = LibraryDashboardDateRange.WEEK,
) -> ApiResponse[Page[LibraryActivityItem]]:
    data = await get_recent_activities(
        scope,
        pagination,
        branch_code=branch_code,
        anchor_date=anchor_date,
        date_range=date_range,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/me/dashboard/alerts", response_model=ApiResponse[list[LibraryAlertItem]])
async def library_dashboard_alerts_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    branch_code: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    copy_status: Annotated[LibraryCopyStatus | None, Query()] = None,
) -> ApiResponse[list[LibraryAlertItem]]:
    data = await get_dashboard_alerts(scope, branch_code=branch_code, category=category, copy_status=copy_status)
    return success_response(data, request_id=get_request_id())