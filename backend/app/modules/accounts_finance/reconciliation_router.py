"""Phase 7 payment reconciliation routes."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.reconciliation_service import (
    auto_match_batch,
    confirm_batch,
    confirm_match,
    create_batch,
    create_reconciliation_period,
    import_statement,
    list_exceptions,
    record_settlement,
    reconciliation_dashboard,
    unmatch,
)
from app.modules.auth.models import User


class PeriodInput(BaseModel):
    label: str
    period_start: date
    period_end: date


class BatchInput(BaseModel):
    source_type: str = "bank"


class ImportInput(BaseModel):
    file_name: str
    content: str
    format: str = "csv"


class MatchRemarkInput(BaseModel):
    remark: str | None = None


class UnmatchInput(BaseModel):
    reason: str = Field(min_length=3)


class SettlementInput(BaseModel):
    settlement_reference: str
    gross_amount: float = Field(ge=0)
    provider_fee: float = 0
    tax_on_fee: float = 0
    net_amount: float | None = None
    settlement_date: date | None = None


router = APIRouter(prefix="/reconciliation", tags=["accounts-finance-reconciliation"])


@router.get("/dashboard", response_model=ApiResponse[dict])
async def dashboard(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await reconciliation_dashboard(scope), request_id=get_request_id())


@router.post("/periods", response_model=ApiResponse[dict])
async def periods_create(
    payload: PeriodInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await create_reconciliation_period(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/periods/{period_id}/batches", response_model=ApiResponse[dict])
async def batches_create(
    period_id: str,
    payload: BatchInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await create_batch(scope, period_id, payload.source_type), request_id=get_request_id())


@router.post("/batches/{batch_id}/import", response_model=ApiResponse[dict])
async def batches_import(
    batch_id: str,
    payload: ImportInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await import_statement(scope, batch_id, file_name=payload.file_name, content=payload.content, file_format=payload.format),
        request_id=get_request_id(),
    )


@router.post("/batches/{batch_id}/auto-match", response_model=ApiResponse[dict])
async def batches_match(
    batch_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await auto_match_batch(scope, batch_id), request_id=get_request_id())


@router.post("/matches/{match_id}/confirm", response_model=ApiResponse[dict])
async def matches_confirm(
    match_id: str,
    payload: MatchRemarkInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await confirm_match(scope, match_id, payload.remark), request_id=get_request_id())


@router.post("/matches/{match_id}/unmatch", response_model=ApiResponse[dict])
async def matches_unmatch(
    match_id: str,
    payload: UnmatchInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await unmatch(scope, match_id, payload.reason), request_id=get_request_id())


@router.post("/batches/{batch_id}/confirm", response_model=ApiResponse[dict])
async def batches_confirm(
    batch_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await confirm_batch(scope, batch_id), request_id=get_request_id())


@router.post("/batches/{batch_id}/settlements", response_model=ApiResponse[dict])
async def settlements_record(
    batch_id: str,
    payload: SettlementInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await record_settlement(scope, batch_id, payload.model_dump()), request_id=get_request_id())


@router.get("/exceptions", response_model=ApiResponse[Page[dict]])
async def exceptions_list(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    batch_id: str | None = None,
) -> ApiResponse[Page[dict]]:
    return success_response(await list_exceptions(scope, pagination, batch_id), request_id=get_request_id())