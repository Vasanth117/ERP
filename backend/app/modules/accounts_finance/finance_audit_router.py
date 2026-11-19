"""Finance audit and transaction trace API."""

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
from app.modules.accounts_finance.finance_audit_service import (
    audit_dashboard,
    export_finance_audit_csv,
    search_finance_audit,
    trace_transaction,
)
from app.modules.auth.models import User

router = APIRouter(prefix="/audit", tags=["accounts-finance-audit"])


class AuditExportBody(BaseModel):
    filters: dict[str, Any] = Field(default_factory=dict)


@router.get("/dashboard")
async def audit_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await audit_dashboard(scope), request_id=get_request_id())


@router.get("/search")
async def audit_search_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    action: Annotated[str | None, Query()] = None,
    resource_type: Annotated[str | None, Query()] = None,
    resource_id: Annotated[str | None, Query()] = None,
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> ApiResponse[list]:
    rows = await search_finance_audit(
        scope,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return success_response(rows, request_id=get_request_id())


@router.get("/trace/{root_type}/{root_id}")
async def audit_trace_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    root_type: str,
    root_id: str,
) -> ApiResponse[dict]:
    return success_response(await trace_transaction(scope, root_type, root_id), request_id=get_request_id())


@router.post("/export")
async def audit_export_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: AuditExportBody,
) -> PlainTextResponse:
    filename, csv_text = await export_finance_audit_csv(scope, body.filters)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return PlainTextResponse(csv_text, media_type="text/csv", headers=headers)