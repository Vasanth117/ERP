"""Reports and analytics routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.reports_admin_schemas import (
    AnalyticsSnapshotRead,
    DashboardAnalyticsRead,
    ReportDefinitionRead,
    ReportDefinitionUpsert,
    ReportExportCreate,
    ReportExportRead,
    ReportFilterCreate,
    ReportFilterRead,
    ReportGenerateRequest,
    ReportJobRead,
    ReportScheduleRequest,
)
from app.modules.college_admin.reports_admin_service import (
    create_report_export,
    download_report_export,
    generate_report,
    get_dashboard_analytics,
    get_report_job,
    get_report_snapshot,
    list_failed_report_jobs,
    list_report_definitions,
    list_report_jobs,
    save_report_filter,
    schedule_report,
    upsert_report_definition,
)

router = APIRouter()


@router.get("/dashboard", response_model=ApiResponse[DashboardAnalyticsRead])
async def reports_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    department_id: Annotated[str | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[DashboardAnalyticsRead]:
    data = await get_dashboard_analytics(scope, department_id=department_id, academic_year_label=academic_year_label)
    return success_response(data, request_id=get_request_id())


@router.get("/definitions", response_model=ApiResponse[list[ReportDefinitionRead]])
async def report_definitions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[ReportDefinitionRead]]:
    return success_response(await list_report_definitions(scope), request_id=get_request_id())


@router.put("/definitions", response_model=ApiResponse[ReportDefinitionRead])
async def report_definition_upsert_route(
    payload: ReportDefinitionUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ReportDefinitionRead]:
    return success_response(await upsert_report_definition(scope, payload), request_id=get_request_id())


@router.put("/filters", response_model=ApiResponse[ReportFilterRead])
async def report_filter_save_route(
    payload: ReportFilterCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ReportFilterRead]:
    return success_response(await save_report_filter(scope, user, payload), request_id=get_request_id())


@router.post("/generate", response_model=ApiResponse[ReportJobRead])
async def report_generate_route(
    payload: ReportGenerateRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ReportJobRead]:
    return success_response(await generate_report(scope, user, payload), request_id=get_request_id())


@router.get("/jobs", response_model=ApiResponse[Page[ReportJobRead]])
async def report_jobs_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ReportJobRead]]:
    return success_response(await list_report_jobs(scope, pagination), request_id=get_request_id())


@router.get("/jobs/{job_id}", response_model=ApiResponse[ReportJobRead])
async def report_job_detail_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ReportJobRead]:
    return success_response(await get_report_job(scope, job_id), request_id=get_request_id())


@router.get("/snapshots/{snapshot_id}", response_model=ApiResponse[AnalyticsSnapshotRead])
async def report_snapshot_route(
    snapshot_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AnalyticsSnapshotRead]:
    return success_response(await get_report_snapshot(scope, snapshot_id), request_id=get_request_id())


@router.post("/schedule", response_model=ApiResponse[ReportJobRead])
async def report_schedule_route(
    payload: ReportScheduleRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ReportJobRead]:
    return success_response(await schedule_report(scope, user, payload), request_id=get_request_id())


@router.post("/exports", response_model=ApiResponse[ReportExportRead])
async def report_export_create_route(
    payload: ReportExportCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ReportExportRead]:
    return success_response(await create_report_export(scope, user, payload), request_id=get_request_id())


@router.get("/exports/download", response_model=ApiResponse[dict])
async def report_export_download_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    token: Annotated[str, Query(min_length=8)],
) -> ApiResponse[dict]:
    return success_response(await download_report_export(scope, user, token), request_id=get_request_id())


@router.get("/failures", response_model=ApiResponse[list[ReportJobRead]])
async def report_failures_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[ReportJobRead]]:
    return success_response(await list_failed_report_jobs(scope), request_id=get_request_id())