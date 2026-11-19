"""Phase 4 student financial ledger routes."""

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
from app.modules.accounts_finance.ledger_service import (
    allocate_advance,
    approve_ledger_adjustment,
    create_ledger_adjustment,
    get_student_account,
    list_ledger_entries,
    run_ledger_reconciliation,
    student_statement,
)
from app.modules.auth.models import User


class LedgerAdjustmentCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    debit: float = Field(default=0, ge=0)
    credit: float = Field(default=0, ge=0)
    original_entry_id: str | None = None


class AdvanceAllocateInput(BaseModel):
    invoice_id: str
    amount: float = Field(gt=0)


router = APIRouter(prefix="/ledger", tags=["accounts-finance-ledger"])


@router.get("/students/{student_user_id}/account", response_model=ApiResponse[dict])
async def student_account_route(
    student_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await get_student_account(scope, student_user_id), request_id=get_request_id())


@router.get("/students/{student_user_id}/statement", response_model=ApiResponse[dict])
async def student_statement_route(
    student_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    issued_from: date | None = None,
    issued_to: date | None = None,
    entry_type: str | None = None,
    transaction_status: str | None = None,
) -> ApiResponse[dict]:
    return success_response(
        await student_statement(
            scope,
            student_user_id,
            pagination,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
            issued_from=issued_from,
            issued_to=issued_to,
            entry_type=entry_type,
            transaction_status=transaction_status,
        ),
        request_id=get_request_id(),
    )


@router.get("/entries", response_model=ApiResponse[Page[dict]])
async def ledger_entries_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    student_user_id: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    entry_type: str | None = None,
    issued_from: date | None = None,
    issued_to: date | None = None,
) -> ApiResponse[Page[dict]]:
    return success_response(
        await list_ledger_entries(
            scope,
            pagination,
            student_user_id=student_user_id,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
            entry_type=entry_type,
            issued_from=issued_from,
            issued_to=issued_to,
        ),
        request_id=get_request_id(),
    )


@router.post("/adjustments", response_model=ApiResponse[dict])
async def ledger_adjustment_create(
    student_user_id: Annotated[str, Query()],
    payload: LedgerAdjustmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await create_ledger_adjustment(
            scope,
            student_user_id,
            reason=payload.reason,
            debit=payload.debit,
            credit=payload.credit,
            original_entry_id=payload.original_entry_id,
        ),
        request_id=get_request_id(),
    )


@router.post("/adjustments/{adjustment_id}/approve", response_model=ApiResponse[dict])
async def ledger_adjustment_approve(
    adjustment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await approve_ledger_adjustment(scope, adjustment_id), request_id=get_request_id())


@router.post("/advances/{advance_id}/allocate", response_model=ApiResponse[dict])
async def advance_allocate_route(
    advance_id: str,
    payload: AdvanceAllocateInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(
        await allocate_advance(scope, advance_id, payload.invoice_id, payload.amount),
        request_id=get_request_id(),
    )


@router.post("/reconciliation/scan", response_model=ApiResponse[dict])
async def reconciliation_scan_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _user: Annotated[User, Depends(finance_staff_user)],
    student_user_id: str | None = None,
) -> ApiResponse[dict]:
    return success_response(await run_ledger_reconciliation(scope, student_user_id), request_id=get_request_id())