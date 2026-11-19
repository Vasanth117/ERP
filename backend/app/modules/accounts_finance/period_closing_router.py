"""Phase 8 financial period closing."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.period_closing_service import (
    approve_period_close,
    approve_period_reopen,
    create_financial_year,
    get_closing_run,
    initiate_closing_run,
    list_accounting_periods,
    request_period_reopen,
    upsert_accounting_period,
)
from app.modules.accounts_finance.phase8_schemas import FinancialPeriodInput, FinancialYearInput, ReopenRequestInput
from app.modules.auth.models import User

router = APIRouter(prefix="/periods", tags=["accounts-finance-periods"])


@router.post("/years")
async def create_financial_year_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: FinancialYearInput,
) -> ApiResponse[dict]:
    return success_response(await create_financial_year(scope, body.model_dump()), request_id=get_request_id())


@router.put("")
async def upsert_period_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: FinancialPeriodInput,
) -> ApiResponse[dict]:
    return success_response(await upsert_accounting_period(scope, body.model_dump()), request_id=get_request_id())


@router.get("")
async def list_periods_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[list]:
    return success_response(await list_accounting_periods(scope), request_id=get_request_id())


@router.post("/{period_code}/closing-runs")
async def initiate_closing_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    period_code: str,
) -> ApiResponse[dict]:
    return success_response(await initiate_closing_run(scope, period_code), request_id=get_request_id())


@router.post("/closing-runs/{closing_run_id}/approve")
async def approve_close_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    closing_run_id: str,
) -> ApiResponse[dict]:
    return success_response(await approve_period_close(scope, closing_run_id), request_id=get_request_id())


@router.get("/closing-runs/{closing_run_id}")
async def get_closing_run_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    closing_run_id: str,
) -> ApiResponse[dict]:
    return success_response(await get_closing_run(scope, closing_run_id), request_id=get_request_id())


@router.post("/{period_code}/reopen-requests")
async def reopen_request_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    period_code: str,
    body: ReopenRequestInput,
) -> ApiResponse[dict]:
    return success_response(
        await request_period_reopen(scope, period_code, body.reason, body.scope_note),
        request_id=get_request_id(),
    )


@router.post("/reopen-requests/{request_id}/approve")
async def approve_reopen_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    request_id: str,
) -> ApiResponse[dict]:
    return success_response(await approve_period_reopen(scope, request_id), request_id=get_request_id())