"""Phase 7 refund and reversal routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.refund_service import (
    approve_payment_reversal,
    approve_refund_request,
    complete_refund,
    create_payment_reversal,
    create_refund_request,
    list_refund_requests,
    refundable_amount,
    refund_dashboard,
    reject_refund_request,
)
from app.modules.auth.models import User


class RefundRequestInput(BaseModel):
    student_user_id: str
    transaction_id: str
    requested_amount: float = Field(gt=0)
    category: str = "other"
    reason: str = Field(min_length=3)
    invoice_id: str | None = None
    document_refs: list[str] = Field(default_factory=list)
    expected_refund_method: str | None = None


class RefundApproveInput(BaseModel):
    approved_amount: float | None = Field(default=None, gt=0)


class RefundCompleteInput(BaseModel):
    payout_reference: str = Field(min_length=3)


class ReversalInput(BaseModel):
    student_user_id: str
    transaction_id: str
    amount: float = Field(gt=0)
    reason: str = Field(min_length=3)
    receipt_id: str | None = None


router = APIRouter(prefix="/refunds", tags=["accounts-finance-refunds"])


@router.get("/dashboard", response_model=ApiResponse[dict])
async def dashboard(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await refund_dashboard(scope), request_id=get_request_id())


@router.get("/requests", response_model=ApiResponse[Page[dict]])
async def requests_list(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    student_user_id: str | None = None,
    transaction_id: str | None = None,
    status: str | None = None,
) -> ApiResponse[Page[dict]]:
    return success_response(
        await list_refund_requests(
            scope, pagination, student_user_id=student_user_id, transaction_id=transaction_id, status=status
        ),
        request_id=get_request_id(),
    )


@router.get("/eligibility/{transaction_id}", response_model=ApiResponse[dict])
async def eligibility(
    transaction_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    from app.modules.accounts_finance.policy import authorize_finance_refund_read, require_finance_tenant_scope

    authorize_finance_refund_read(scope)
    return success_response(
        await refundable_amount(require_finance_tenant_scope(scope), transaction_id),
        request_id=get_request_id(),
    )


@router.post("/requests", response_model=ApiResponse[dict])
async def requests_create(
    payload: RefundRequestInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await create_refund_request(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/requests/{refund_request_id}/approve", response_model=ApiResponse[dict])
async def requests_approve(
    refund_request_id: str,
    payload: RefundApproveInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await approve_refund_request(scope, refund_request_id, approved_amount=payload.approved_amount),
        request_id=get_request_id(),
    )


@router.post("/requests/{refund_request_id}/complete", response_model=ApiResponse[dict])
async def requests_complete(
    refund_request_id: str,
    payload: RefundCompleteInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await complete_refund(scope, refund_request_id, payload.payout_reference), request_id=get_request_id())


@router.post("/requests/{refund_request_id}/reject", response_model=ApiResponse[dict])
async def requests_reject(
    refund_request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    reason: Annotated[str, Query(min_length=3)],
) -> ApiResponse[dict]:
    return success_response(await reject_refund_request(scope, refund_request_id, reason), request_id=get_request_id())


@router.post("/reversals", response_model=ApiResponse[dict])
async def reversals_create(
    payload: ReversalInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await create_payment_reversal(scope, payload.model_dump()), request_id=get_request_id())


@router.post("/reversals/{reversal_request_id}/approve", response_model=ApiResponse[dict])
async def reversals_approve(
    reversal_request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await approve_payment_reversal(scope, reversal_request_id), request_id=get_request_id())