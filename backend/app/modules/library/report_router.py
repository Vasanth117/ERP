"""Library reports routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.library.deps import librarian_user
from app.modules.library.report_schemas import (
    LibraryReportCatalogItem,
    LibraryReportDataRead,
    LibraryReportDownloadRead,
    LibraryReportFilters,
    LibraryReportGenerateBody,
    LibraryReportJobRead,
)
from app.modules.library.report_service import (
    download_report_export,
    generate_report_export,
    get_report_snapshot,
    list_report_catalog,
)

router = APIRouter(prefix="/reports", tags=["library-reports"])


@router.get("/catalog", response_model=ApiResponse[list[LibraryReportCatalogItem]])
async def report_catalog_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[list[LibraryReportCatalogItem]]:
    return success_response(await list_report_catalog(scope), request_id=get_request_id())


@router.get("/{report_type}", response_model=ApiResponse[LibraryReportDataRead])
async def report_snapshot_route(
    report_type: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    date_from: Annotated[str | None, Query()] = None,
    date_to: Annotated[str | None, Query()] = None,
    branch_code: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    member_category: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
) -> ApiResponse[LibraryReportDataRead]:
    from datetime import date as date_type

    filters = LibraryReportFilters(
        date_from=date_type.fromisoformat(date_from) if date_from else None,
        date_to=date_type.fromisoformat(date_to) if date_to else None,
        branch_code=branch_code,
        category=category,
        member_category=member_category,
        status=status,
    )
    return success_response(await get_report_snapshot(scope, report_type, filters), request_id=get_request_id())


@router.post("/exports", response_model=ApiResponse[LibraryReportJobRead], status_code=status.HTTP_201_CREATED)
async def report_export_route(
    body: LibraryReportGenerateBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryReportJobRead]:
    return success_response(await generate_report_export(scope, user, body), request_id=get_request_id())


@router.get("/exports/{job_id}/download", response_model=ApiResponse[LibraryReportDownloadRead])
async def report_download_route(
    job_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryReportDownloadRead]:
    return success_response(await download_report_export(scope, user, job_id), request_id=get_request_id())