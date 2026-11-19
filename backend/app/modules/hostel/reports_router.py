"""Hostel reports and analytics routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.reports_schemas import (
    HostelAnalyticsOverview,
    ReportCatalogItemRead,
    ReportDataRead,
    ReportExportRead,
    ReportExportRequest,
    ReportRunRequest,
    SavedReportRead,
    SavedReportUpsert,
    ScheduledReportRead,
    ScheduledReportUpsert,
)
from app.modules.hostel.reports_service import (
    analytics_overview,
    execute_scheduled_report,
    export_report,
    report_catalog,
    run_report,
    upsert_saved_report,
    upsert_scheduled_report,
)

router = APIRouter(prefix="/me", tags=["hostel-reports"])


@router.get("/reports/catalog", response_model=ApiResponse[list[ReportCatalogItemRead]])
async def report_catalog_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await report_catalog(scope), request_id=get_request_id())


@router.post("/reports/run", response_model=ApiResponse[ReportDataRead])
async def report_run_route(
    payload: ReportRunRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await run_report(scope, payload), request_id=get_request_id())


@router.post("/reports/export", response_model=ApiResponse[ReportExportRead])
async def report_export_route(
    payload: ReportExportRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await export_report(scope, payload), request_id=get_request_id())


@router.put("/reports/saved", response_model=ApiResponse[SavedReportRead])
async def saved_report_route(
    payload: SavedReportUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_saved_report(scope, payload), request_id=get_request_id())


@router.put("/reports/schedules", response_model=ApiResponse[ScheduledReportRead])
async def scheduled_report_route(
    payload: ScheduledReportUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await upsert_scheduled_report(scope, payload), request_id=get_request_id())


@router.post("/reports/schedules/{schedule_code}/execute", response_model=ApiResponse[ReportExportRead])
async def scheduled_execute_route(
    schedule_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await execute_scheduled_report(scope, schedule_code), request_id=get_request_id())


@router.get("/analytics/overview", response_model=ApiResponse[HostelAnalyticsOverview])
async def analytics_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await analytics_overview(scope), request_id=get_request_id())