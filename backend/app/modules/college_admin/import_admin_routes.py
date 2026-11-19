"""Data import and migration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.import_admin_schemas import (
    ImportApproveRequest,
    ImportErrorReportRead,
    ImportJobRead,
    ImportMappingRead,
    ImportMappingUpsert,
    ImportPreviewRead,
    ImportTemplateRead,
    ImportUploadRequest,
    ImportValidationReport,
    MigrationHistoryItem,
)
from app.modules.college_admin.import_admin_service import (
    approve_import,
    download_error_report,
    execute_import,
    get_import_job,
    issue_error_report,
    list_import_templates,
    list_migration_history,
    preview_import,
    retry_failed_import_rows,
    upload_import_file,
    upsert_import_mapping,
    validate_import_job,
)

router = APIRouter()


@router.get("/templates", response_model=ApiResponse[list[ImportTemplateRead]])
async def import_templates_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[ImportTemplateRead]]:
    return success_response(await list_import_templates(scope), request_id=get_request_id())


@router.put("/mappings", response_model=ApiResponse[ImportMappingRead])
async def import_mapping_route(
    payload: ImportMappingUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ImportMappingRead]:
    return success_response(await upsert_import_mapping(scope, user, payload), request_id=get_request_id())


@router.post("/jobs", response_model=ApiResponse[ImportJobRead])
async def import_upload_route(
    payload: ImportUploadRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ImportJobRead]:
    return success_response(await upload_import_file(scope, user, payload), request_id=get_request_id())


@router.get("/jobs/{job_id}", response_model=ApiResponse[ImportJobRead])
async def import_job_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ImportJobRead]:
    return success_response(await get_import_job(scope, job_id), request_id=get_request_id())


@router.post("/jobs/{job_id}/validate", response_model=ApiResponse[ImportValidationReport])
async def import_validate_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    mapping_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[ImportValidationReport]:
    return success_response(await validate_import_job(scope, user, job_id, mapping_id=mapping_id), request_id=get_request_id())


@router.get("/jobs/{job_id}/preview", response_model=ApiResponse[ImportPreviewRead])
async def import_preview_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ImportPreviewRead]:
    return success_response(await preview_import(scope, job_id), request_id=get_request_id())


@router.post("/jobs/{job_id}/approve", response_model=ApiResponse[ImportJobRead])
async def import_approve_route(
    job_id: str,
    payload: ImportApproveRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ImportJobRead]:
    return success_response(await approve_import(scope, user, job_id, payload), request_id=get_request_id())


@router.post("/jobs/{job_id}/execute", response_model=ApiResponse[ImportJobRead])
async def import_execute_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ImportJobRead]:
    return success_response(await execute_import(scope, user, job_id), request_id=get_request_id())


@router.post("/jobs/{job_id}/retry", response_model=ApiResponse[ImportJobRead])
async def import_retry_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ImportJobRead]:
    return success_response(await retry_failed_import_rows(scope, user, job_id), request_id=get_request_id())


@router.get("/migration-history", response_model=ApiResponse[Page[MigrationHistoryItem]])
async def migration_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[MigrationHistoryItem]]:
    return success_response(await list_migration_history(scope, pagination), request_id=get_request_id())


@router.post("/jobs/{job_id}/error-report", response_model=ApiResponse[ImportErrorReportRead])
async def import_error_report_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ImportErrorReportRead]:
    return success_response(await issue_error_report(scope, user, job_id), request_id=get_request_id())


@router.get("/error-reports/download", response_model=ApiResponse[dict])
async def import_error_download_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    token: Annotated[str, Query(min_length=8)],
) -> ApiResponse[dict]:
    return success_response(await download_error_report(scope, user, token), request_id=get_request_id())