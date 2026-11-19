"""HR reports and analytics routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.hr_reports_schemas import (
    HrAnalyticsDashboard,
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
from app.modules.hr.hr_reports_service import (
    analytics_dashboard,
    execute_scheduled_report,
    export_report,
    get_export_download,
    list_report_catalog,
    list_saved_reports,
    run_report,
    save_report,
    schedule_report,
)

router = APIRouter(prefix="/reports", tags=["hr-reports"])


@router.get("/analytics-dashboard", response_model=ApiResponse[HrAnalyticsDashboard])
async def analytics_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await analytics_dashboard(scope), request_id=get_request_id())


@router.get("/catalog", response_model=ApiResponse[list[ReportCatalogItemRead]])
async def catalog_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_report_catalog(scope), request_id=get_request_id())


@router.post("/run", response_model=ApiResponse[ReportDataRead])
async def run_route(payload: ReportRunRequest, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await run_report(scope, payload), request_id=get_request_id())


@router.post("/export", response_model=ApiResponse[ReportExportRead])
async def export_route(payload: ReportExportRequest, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await export_report(scope, payload), request_id=get_request_id())


@router.get("/exports/{execution_id}/download", response_model=ApiResponse)
async def download_route(execution_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await get_export_download(scope, execution_id), request_id=get_request_id())


@router.post("/saved", response_model=ApiResponse[SavedReportRead])
async def saved_upsert_route(payload: SavedReportUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await save_report(scope, payload), request_id=get_request_id())


@router.get("/saved", response_model=ApiResponse[list[SavedReportRead]])
async def saved_list_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_saved_reports(scope), request_id=get_request_id())


@router.post("/scheduled", response_model=ApiResponse[ScheduledReportRead])
async def schedule_route(payload: ScheduledReportUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await schedule_report(scope, payload), request_id=get_request_id())


@router.post("/scheduled/{schedule_id}/execute", response_model=ApiResponse[ReportExportRead])
async def execute_schedule_route(schedule_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await execute_scheduled_report(scope, schedule_id), request_id=get_request_id())