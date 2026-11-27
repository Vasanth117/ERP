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
from app.modules.college_admin.reports_dashboard_page_service import get_reports_dashboard_page
from app.modules.college_admin.reports_section_sub_nav_service import get_reports_section_sub_nav
from app.modules.college_admin.reports_academic_page_service import get_reports_academic_module_page
from app.modules.college_admin.reports_people_page_service import get_reports_people_module_page
from app.modules.college_admin.reports_operations_page_service import get_reports_operations_module_page
from app.modules.college_admin.reports_custom_scheduled_page_service import (
    get_reports_custom_builder_page,
    get_reports_export_history_page,
    get_reports_scheduled_page,
    save_reports_custom_builder,
)
from app.modules.college_admin.schemas import (
    ReportsAcademicModulePageRead,
    ReportsCustomBuilderPageRead,
    ReportsCustomBuilderSave,
    ReportsDashboardPageRead,
    ReportsExportHistoryPageRead,
    ReportsScheduledPageRead,
    ReportsSectionSubNavRead,
)
from app.modules.college_admin.reports_admin_schemas import ReportGenerateRequest

router = APIRouter()


@router.get("/navigation/section-sub-nav", response_model=ApiResponse[ReportsSectionSubNavRead])
async def reports_section_sub_nav_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    path: Annotated[str, Query(min_length=1)],
):
    return success_response(
        await get_reports_section_sub_nav(scope, path=path),
        request_id=get_request_id(),
    )


@router.get("/people/{page_key}/management/page", response_model=ApiResponse[ReportsAcademicModulePageRead])
async def reports_people_module_page_route(
    page_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
    academic_year: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_reports_people_module_page(
            scope,
            page_key=page_key,
            page=page,
            page_size=page_size,
            academic_year=academic_year,
            department_id=department_id,
        ),
        request_id=get_request_id(),
    )


@router.post("/people/{page_key}/run", response_model=ApiResponse[dict])
async def reports_people_run_report_route(
    page_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
):
    from app.modules.college_admin.reports_people_catalog import page_meta as people_meta

    meta = people_meta(page_key)
    if meta is None:
        from app.core.exceptions import AppError

        raise AppError(code="NOT_FOUND", message="Unknown reports page", status_code=404)
    job = await generate_report(
        scope,
        user,
        ReportGenerateRequest(report_key=meta.run_report_key),
    )
    return success_response(
        {"job_id": job.job_id, "report_key": job.report_key, "status": job.status.value},
        request_id=get_request_id(),
    )


@router.get("/operations/{page_key}/management/page", response_model=ApiResponse[ReportsAcademicModulePageRead])
async def reports_operations_module_page_route(
    page_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
    academic_year: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_reports_operations_module_page(
            scope,
            page_key=page_key,
            page=page,
            page_size=page_size,
            academic_year=academic_year,
            department_id=department_id,
        ),
        request_id=get_request_id(),
    )


@router.post("/operations/{page_key}/run", response_model=ApiResponse[dict])
async def reports_operations_run_report_route(
    page_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
):
    from app.modules.college_admin.reports_operations_catalog import page_meta as operations_meta

    meta = operations_meta(page_key)
    if meta is None:
        from app.core.exceptions import AppError

        raise AppError(code="NOT_FOUND", message="Unknown reports page", status_code=404)
    job = await generate_report(
        scope,
        user,
        ReportGenerateRequest(report_key=meta.run_report_key),
    )
    return success_response(
        {"job_id": job.job_id, "report_key": job.report_key, "status": job.status.value},
        request_id=get_request_id(),
    )


@router.get("/academic/{page_key}/management/page", response_model=ApiResponse[ReportsAcademicModulePageRead])
async def reports_academic_module_page_route(
    page_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
    academic_year: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_reports_academic_module_page(
            scope,
            page_key=page_key,
            page=page,
            page_size=page_size,
            academic_year=academic_year,
            department_id=department_id,
        ),
        request_id=get_request_id(),
    )


@router.post("/academic/{page_key}/run", response_model=ApiResponse[dict])
async def reports_academic_run_report_route(
    page_key: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
):
    from app.modules.college_admin.reports_academic_catalog import page_meta

    meta = page_meta(page_key)
    if meta is None:
        from app.core.exceptions import AppError

        raise AppError(code="NOT_FOUND", message="Unknown reports page", status_code=404)
    job = await generate_report(
        scope,
        user,
        ReportGenerateRequest(report_key=meta.run_report_key),
    )
    return success_response(
        {"job_id": job.job_id, "report_key": job.report_key, "status": job.status.value},
        request_id=get_request_id(),
    )


@router.get("/custom-scheduled/scheduled/management/page", response_model=ApiResponse[ReportsScheduledPageRead])
async def reports_scheduled_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
):
    return success_response(
        await get_reports_scheduled_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/custom-scheduled/exports/management/page", response_model=ApiResponse[ReportsExportHistoryPageRead])
async def reports_export_history_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_reports_export_history_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/custom-scheduled/builder/management/page", response_model=ApiResponse[ReportsCustomBuilderPageRead])
async def reports_custom_builder_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    data_source: Annotated[str | None, Query()] = None,
    filter_id: Annotated[str | None, Query()] = None,
    active_step: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_reports_custom_builder_page(
            scope,
            user,
            data_source=data_source,
            filter_id=filter_id,
            active_step_key=active_step,
        ),
        request_id=get_request_id(),
    )


@router.put("/custom-scheduled/builder/management/page", response_model=ApiResponse[ReportsCustomBuilderPageRead])
async def reports_custom_builder_save_route(
    payload: ReportsCustomBuilderSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
):
    return success_response(
        await save_reports_custom_builder(scope, user, payload),
        request_id=get_request_id(),
    )


@router.get("/dashboard/management/page", response_model=ApiResponse[ReportsDashboardPageRead])
async def reports_dashboard_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
):
    return success_response(
        await get_reports_dashboard_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


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