"""Examination report routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_report_schemas import (
    ExamReportCatalogItem,
    ExamReportDataRead,
    ExamReportDownloadRead,
    ExamReportFilters,
    ExamReportGenerateBody,
    ExamReportJobRead,
)
from app.modules.examinations.exam_cell_report_service import (
    download_report_job,
    generate_report_export,
    get_report_job,
    get_report_snapshot,
    list_report_catalog,
)

router = APIRouter(tags=["examination-cell-reports"])


@router.get("/reports/catalog", response_model=ApiResponse[list[ExamReportCatalogItem]])
async def report_catalog_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamReportCatalogItem]]:
    _ = user
    return success_response(await list_report_catalog(scope), request_id=get_request_id())


@router.post("/reports/{report_type}/snapshot", response_model=ApiResponse[ExamReportDataRead])
async def report_snapshot_route(
    report_type: str,
    filters: ExamReportFilters,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamReportDataRead]:
    _ = user
    return success_response(await get_report_snapshot(scope, report_type, filters), request_id=get_request_id())


@router.post("/reports/exports", response_model=ApiResponse[ExamReportJobRead])
async def report_export_route(
    body: ExamReportGenerateBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamReportJobRead]:
    return success_response(await generate_report_export(scope, user, body), request_id=get_request_id())


@router.get("/reports/jobs/{job_id}", response_model=ApiResponse[ExamReportJobRead])
async def report_job_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamReportJobRead]:
    _ = user
    return success_response(await get_report_job(scope, job_id), request_id=get_request_id())


@router.get("/reports/jobs/{job_id}/download", response_model=ApiResponse[ExamReportDownloadRead])
async def report_download_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamReportDownloadRead]:
    _ = user
    return success_response(await download_report_job(scope, job_id), request_id=get_request_id())