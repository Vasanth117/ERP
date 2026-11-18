"""Department Admin phase 8 — reports, analytics, import/export."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.department_admin.deps import department_admin_user
from app.modules.department_admin.import_export_service import (
    download_export_job,
    execute_import_job,
    get_transfer_job,
    import_errors,
    list_export_datasets,
    list_import_templates,
    start_export,
    start_import,
    transfer_history,
    validate_import_job,
)
from app.modules.department_admin.phase8_schemas import (
    DataTransferJobRead,
    ExportDatasetRead,
    ExportRequestBody,
    ImportTemplateRead,
    ImportUploadBody,
    ReportCatalogItem,
    ReportDataRead,
    ReportDownloadRead,
    ReportFilters,
    ReportGenerateBody,
    ReportJobRead,
    ReportsOverviewRead,
)
from app.modules.department_admin.reports_service import (
    download_report_job,
    generate_report,
    get_report_job,
    get_report_snapshot,
    list_report_catalog,
    reports_overview,
)

phase8_router = APIRouter()


def _report_filters(
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    batch_label: Annotated[str | None, Query()] = None,
    section_code: Annotated[str | None, Query()] = None,
    course_code: Annotated[str | None, Query()] = None,
    faculty_user_id: Annotated[str | None, Query()] = None,
) -> ReportFilters:
    return ReportFilters(
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        programme_code=programme_code,
        batch_label=batch_label,
        section_code=section_code,
        course_code=course_code,
        faculty_user_id=faculty_user_id,
    )


@phase8_router.get("/reports", response_model=ApiResponse[list[ReportCatalogItem]])
async def department_reports_catalog_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[ReportCatalogItem]]:
    data = list_report_catalog(scope)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/reports/overview", response_model=ApiResponse[ReportsOverviewRead])
async def department_reports_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ReportsOverviewRead]:
    data = await reports_overview(scope, user)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/reports/faculty-workload", response_model=ApiResponse[ReportDataRead])
async def department_report_faculty_workload_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[ReportFilters, Depends(_report_filters)],
) -> ApiResponse[ReportDataRead]:
    data = await get_report_snapshot(scope, user, "faculty_workload", filters)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/reports/student-enrollment", response_model=ApiResponse[ReportDataRead])
async def department_report_student_enrollment_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[ReportFilters, Depends(_report_filters)],
) -> ApiResponse[ReportDataRead]:
    data = await get_report_snapshot(scope, user, "student_enrollment", filters)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/reports/attendance", response_model=ApiResponse[ReportDataRead])
async def department_report_attendance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[ReportFilters, Depends(_report_filters)],
) -> ApiResponse[ReportDataRead]:
    data = await get_report_snapshot(scope, user, "attendance", filters)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/reports/academic-performance", response_model=ApiResponse[ReportDataRead])
async def department_report_performance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[ReportFilters, Depends(_report_filters)],
) -> ApiResponse[ReportDataRead]:
    data = await get_report_snapshot(scope, user, "academic_performance", filters)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/reports/timetable", response_model=ApiResponse[ReportDataRead])
async def department_report_timetable_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[ReportFilters, Depends(_report_filters)],
) -> ApiResponse[ReportDataRead]:
    data = await get_report_snapshot(scope, user, "timetable", filters)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/reports/examination-readiness", response_model=ApiResponse[ReportDataRead])
async def department_report_examination_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[ReportFilters, Depends(_report_filters)],
) -> ApiResponse[ReportDataRead]:
    data = await get_report_snapshot(scope, user, "examination_readiness", filters)
    return success_response(data, request_id=get_request_id())


@phase8_router.post("/reports/generate", response_model=ApiResponse[ReportJobRead])
async def department_report_generate_route(
    payload: ReportGenerateBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ReportJobRead]:
    data = await generate_report(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/reports/jobs/{job_id}", response_model=ApiResponse[ReportJobRead])
async def department_report_job_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ReportJobRead]:
    data = await get_report_job(scope, user, job_id)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/reports/jobs/{job_id}/download", response_model=ApiResponse[ReportDownloadRead])
async def department_report_download_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ReportDownloadRead]:
    data = await download_report_job(scope, user, job_id)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/import-export/templates", response_model=ApiResponse[list[ImportTemplateRead]])
async def department_import_templates_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[ImportTemplateRead]]:
    data = list_import_templates(scope)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/import-export/datasets", response_model=ApiResponse[list[ExportDatasetRead]])
async def department_export_datasets_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[ExportDatasetRead]]:
    data = list_export_datasets(scope)
    return success_response(data, request_id=get_request_id())


@phase8_router.post("/import-export/import", response_model=ApiResponse[DataTransferJobRead])
async def department_import_upload_route(
    payload: ImportUploadBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DataTransferJobRead]:
    data = await start_import(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/import-export/imports/{job_id}", response_model=ApiResponse[DataTransferJobRead])
async def department_import_get_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DataTransferJobRead]:
    data = await get_transfer_job(scope, user, job_id)
    return success_response(data, request_id=get_request_id())


@phase8_router.post("/import-export/imports/{job_id}/validate", response_model=ApiResponse[DataTransferJobRead])
async def department_import_validate_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DataTransferJobRead]:
    data = await validate_import_job(scope, user, job_id)
    return success_response(data, request_id=get_request_id())


@phase8_router.post("/import-export/imports/{job_id}/execute", response_model=ApiResponse[DataTransferJobRead])
async def department_import_execute_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DataTransferJobRead]:
    data = await execute_import_job(scope, user, job_id)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/import-export/imports/{job_id}/errors", response_model=ApiResponse[list[dict]])
async def department_import_errors_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[dict]]:
    data = await import_errors(scope, user, job_id)
    return success_response(data, request_id=get_request_id())


@phase8_router.post("/import-export/exports", response_model=ApiResponse[DataTransferJobRead])
async def department_export_create_route(
    payload: ExportRequestBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DataTransferJobRead]:
    data = await start_export(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/import-export/exports/{job_id}", response_model=ApiResponse[DataTransferJobRead])
async def department_export_get_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[DataTransferJobRead]:
    data = await get_transfer_job(scope, user, job_id)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/import-export/exports/{job_id}/download", response_model=ApiResponse[ReportDownloadRead])
async def department_export_download_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[ReportDownloadRead]:
    data = await download_export_job(scope, user, job_id)
    return success_response(data, request_id=get_request_id())


@phase8_router.get("/import-export/history", response_model=ApiResponse[Page[DataTransferJobRead]])
async def department_transfer_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    operation: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[DataTransferJobRead]]:
    data = await transfer_history(scope, user, operation=operation, pagination=pagination)
    return success_response(data, request_id=get_request_id())