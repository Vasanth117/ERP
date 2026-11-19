"""Expense and reimbursement routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.expense_claim_service import (
    approve_expense_claim,
    create_advance,
    create_expense_claim,
    expense_reports,
    pay_expense_claim,
    seed_expense_categories,
    settle_advance,
)
from app.modules.auth.models import User

router = APIRouter(prefix="/expenses", tags=["accounts-finance-expenses"])


class ExpenseClaimInput(BaseModel):
    description: str
    category_code: str
    expense_date: date
    amount: float = Field(gt=0)
    document_refs: list[str] = Field(default_factory=list)
    submit: bool = False


class PaymentInput(BaseModel):
    payment_reference: str = Field(min_length=3)


@router.post("/categories/seed")
async def seed_categories_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await seed_expense_categories(scope), request_id=get_request_id())


@router.post("/claims")
async def create_claim_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: ExpenseClaimInput,
) -> ApiResponse[dict]:
    return success_response(await create_expense_claim(scope, body.model_dump()), request_id=get_request_id())


@router.post("/claims/{claim_id}/approve")
async def approve_claim_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    claim_id: str,
    approved: bool = True,
) -> ApiResponse[dict]:
    return success_response(await approve_expense_claim(scope, claim_id, approved=approved), request_id=get_request_id())


@router.post("/claims/{claim_id}/pay")
async def pay_claim_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    claim_id: str,
    body: PaymentInput,
) -> ApiResponse[dict]:
    return success_response(await pay_expense_claim(scope, claim_id, body.payment_reference), request_id=get_request_id())


@router.get("/reports/summary")
async def expense_reports_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await expense_reports(scope), request_id=get_request_id())


class AdvanceInput(BaseModel):
    employee_id: str
    amount: float = Field(gt=0)
    purpose: str = "Travel"


@router.post("/advances")
async def create_advance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: AdvanceInput,
) -> ApiResponse[dict]:
    return success_response(await create_advance(scope, body.model_dump()), request_id=get_request_id())


@router.post("/advances/{advance_id}/settle")
async def settle_advance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    advance_id: str,
    claim_id: str,
    actual_amount: float,
) -> ApiResponse[dict]:
    return success_response(await settle_advance(scope, advance_id, claim_id, actual_amount), request_id=get_request_id())