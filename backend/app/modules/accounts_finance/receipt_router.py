"""Phase 4 payment receipt routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.receipt_service import (
    cancel_receipt,
    daily_receipt_register,
    generate_receipt_for_transaction,
    get_receipt,
    get_receipt_by_number,
    reissue_receipt,
    search_receipts,
)
from app.modules.auth.models import User


class ReceiptCancelInput(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class ReceiptReissueInput(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


router = APIRouter(prefix="/receipts", tags=["accounts-finance-receipts"])


@router.get("", response_model=ApiResponse[Page[dict]])
async def list_receipts(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    student_user_id: str | None = None,
    transaction_id: str | None = None,
    academic_year_label: str | None = None,
    payment_mode: str | None = None,
    receipt_status: str | None = None,
    issued_from: date | None = None,
    issued_to: date | None = None,
) -> ApiResponse[Page[dict]]:
    return success_response(
        await search_receipts(
            scope,
            pagination,
            student_user_id=student_user_id,
            transaction_id=transaction_id,
            academic_year_label=academic_year_label,
            payment_mode=payment_mode,
            receipt_status=receipt_status,
            issued_from=issued_from,
            issued_to=issued_to,
        ),
        request_id=get_request_id(),
    )


@router.get("/register/daily", response_model=ApiResponse[dict])
async def daily_register(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    day: Annotated[date, Query()],
) -> ApiResponse[dict]:
    return success_response(await daily_receipt_register(scope, day), request_id=get_request_id())


@router.get("/by-number/{receipt_number}", response_model=ApiResponse[dict])
async def receipt_by_number(
    receipt_number: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await get_receipt_by_number(scope, receipt_number), request_id=get_request_id())


@router.get("/{receipt_id}", response_model=ApiResponse[dict])
async def receipt_detail(
    receipt_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await get_receipt(scope, receipt_id), request_id=get_request_id())


@router.post("/generate/{transaction_id}", response_model=ApiResponse[dict])
async def generate_receipt(
    transaction_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await generate_receipt_for_transaction(scope, transaction_id), request_id=get_request_id())


@router.post("/{receipt_id}/cancel", response_model=ApiResponse[dict])
async def receipt_cancel(
    receipt_id: str,
    payload: ReceiptCancelInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await cancel_receipt(scope, receipt_id, payload.reason), request_id=get_request_id())


@router.post("/{receipt_id}/reissue", response_model=ApiResponse[dict])
async def receipt_reissue(
    receipt_id: str,
    payload: ReceiptReissueInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await reissue_receipt(scope, receipt_id, payload.reason), request_id=get_request_id())