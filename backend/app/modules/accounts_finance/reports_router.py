"""Phase 8 financial reports and analytics workspace."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.finance_report_service import (
    export_report_csv,
    get_report_workspace,
    list_report_categories,
    list_saved_reports,
    preview_report,
    run_saved_report,
    save_report,
)
from app.modules.accounts_finance.phase8_schemas import ReportPreviewResponse, SavedReportInput, SavedReportRead
from app.modules.auth.models import User

router = APIRouter(prefix="/reports", tags=["accounts-finance-reports"])


class ReportPreviewBody(BaseModel):
    category: str
    filters: dict[str, Any] = Field(default_factory=dict)


@router.get("/workspace")
async def report_workspace_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    department_id: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(
        await get_report_workspace(
            scope,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
            programme_code=programme_code,
            department_id=department_id,
            campus_id=campus_id,
            date_from=date_from,
            date_to=date_to,
        ),
        request_id=get_request_id(),
    )


@router.get("/categories")
async def report_categories_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[list]:
    return success_response(await list_report_categories(scope), request_id=get_request_id())


@router.post("/preview", response_model=ApiResponse[ReportPreviewResponse])
async def report_preview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: ReportPreviewBody,
) -> ApiResponse[ReportPreviewResponse]:
    return success_response(await preview_report(scope, body.category, body.filters), request_id=get_request_id())


@router.post("/saved", response_model=ApiResponse[SavedReportRead])
async def save_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: SavedReportInput,
) -> ApiResponse[SavedReportRead]:
    return success_response(await save_report(scope, body.model_dump()), request_id=get_request_id())


@router.get("/saved", response_model=ApiResponse[list[SavedReportRead]])
async def list_saved_reports_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[list[SavedReportRead]]:
    return success_response(await list_saved_reports(scope), request_id=get_request_id())


@router.post("/saved/{report_id}/run", response_model=ApiResponse[ReportPreviewResponse])
async def run_saved_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    report_id: str,
) -> ApiResponse[ReportPreviewResponse]:
    return success_response(await run_saved_report(scope, report_id), request_id=get_request_id())


@router.post("/export/csv")
async def export_report_csv_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: ReportPreviewBody,
) -> PlainTextResponse:
    filename, content = await export_report_csv(scope, body.category, body.filters)
    return PlainTextResponse(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )