"""Phase 3 payment routes (gateway, online oversight, offline collection)."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.gateway_config_service import list_gateway_configs, upsert_gateway_config
from app.modules.accounts_finance.offline_payment_service import (
    create_collection_batch,
    handover_batch,
    list_offline_payments,
    offline_daily_report,
    payment_history,
    record_offline_payment,
    reverse_offline_payment,
    verify_offline_payment,
)
from app.modules.auth.models import User
from pydantic import BaseModel, Field


class GatewayConfigUpsert(BaseModel):
    config_id: str | None = None
    gateway_name: str
    provider_code: str = "stub"
    environment: str = "sandbox"
    merchant_reference: str | None = None
    currency: str = "INR"
    supported_methods: list[str] = Field(default_factory=list)
    webhook_url: str | None = None
    api_key_secret_ref: str | None = None
    webhook_secret_ref: str | None = None
    active: bool = False
    connection_status: str = "unknown"
    metadata: dict[str, Any] = Field(default_factory=dict)


class OfflinePaymentRecordInput(BaseModel):
    student_user_id: str
    demand_id: str
    amount: float = Field(ge=0)
    payment_method: str
    idempotency_key: str = Field(min_length=8, max_length=64)
    invoice_id: str | None = None
    instrument_reference: str | None = None
    bank_name: str | None = None
    branch: str | None = None
    collection_location: str | None = None
    remarks: str | None = None
    document_ref: str | None = None
    batch_id: str | None = None
    payment_date: date | None = None
    issue_date: date | None = None


class OfflineVerifyInput(BaseModel):
    note: str | None = None
    cheque_cleared: bool = True


class HandoverInput(BaseModel):
    to_user_id: str
    amount: float = Field(ge=0)
    note: str | None = None


router = APIRouter(prefix="/payments", tags=["accounts-finance-payments"])


@router.put("/gateway-config", response_model=ApiResponse[dict])
async def gateway_config_upsert_route(
    payload: GatewayConfigUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_gateway_config(scope, payload.model_dump()), request_id=get_request_id())


@router.get("/gateway-config", response_model=ApiResponse[list[dict]])
async def gateway_config_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[list[dict]]:
    return success_response(await list_gateway_configs(scope), request_id=get_request_id())


@router.get("/transactions", response_model=ApiResponse[Page[dict]])
async def payment_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    student_user_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[dict]]:
    return success_response(await payment_history(scope, pagination, student_user_id=student_user_id), request_id=get_request_id())


@router.post("/offline", response_model=ApiResponse[dict])
async def offline_record_route(
    payload: OfflinePaymentRecordInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await record_offline_payment(scope, payload.model_dump()), request_id=get_request_id())


@router.get("/offline", response_model=ApiResponse[Page[dict]])
async def offline_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[dict]]:
    return success_response(await list_offline_payments(scope, pagination, status=status), request_id=get_request_id())


@router.post("/offline/{record_id}/verify", response_model=ApiResponse[dict])
async def offline_verify_route(
    record_id: str,
    payload: OfflineVerifyInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await verify_offline_payment(scope, record_id, note=payload.note, cheque_cleared=payload.cheque_cleared),
        request_id=get_request_id(),
    )


@router.post("/offline/{record_id}/reverse", response_model=ApiResponse[dict])
async def offline_reverse_route(
    record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    reason: Annotated[str, Query(min_length=3)],
) -> ApiResponse[dict]:
    return success_response(await reverse_offline_payment(scope, record_id, reason), request_id=get_request_id())


@router.post("/offline/batches", response_model=ApiResponse[dict])
async def offline_batch_create_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    batch_date: Annotated[date | None, Query()] = None,
    counter_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(
        await create_collection_batch(scope, batch_date=batch_date or date.today(), counter_code=counter_code),
        request_id=get_request_id(),
    )


@router.post("/offline/batches/{batch_id}/handover", response_model=ApiResponse[dict])
async def offline_handover_route(
    batch_id: str,
    payload: HandoverInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await handover_batch(scope, batch_id, to_user_id=payload.to_user_id, amount=payload.amount, note=payload.note), request_id=get_request_id())


@router.get("/offline/reports/daily", response_model=ApiResponse[dict])
async def offline_daily_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    batch_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await offline_daily_report(scope, batch_date or date.today()), request_id=get_request_id())