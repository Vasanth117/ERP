"""Invoice and demand routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.invoice_service import (
    apply_invoice_adjustment,
    generate_invoices,
    get_invoice,
    issue_invoice,
    preview_invoice_generation,
    search_invoices,
)
from app.modules.accounts_finance.phase2_schemas import (
    InvoiceAdjustmentRequest,
    InvoiceGeneratePreview,
    InvoiceGenerateScope,
    InvoiceIssueRequest,
    InvoiceRead,
)
from app.modules.auth.models import User

router = APIRouter(prefix="/invoices", tags=["accounts-finance-invoices"])


@router.post("/preview", response_model=ApiResponse[InvoiceGeneratePreview])
async def invoice_preview_route(
    payload: InvoiceGenerateScope,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[InvoiceGeneratePreview]:
    return success_response(await preview_invoice_generation(scope, payload), request_id=get_request_id())


@router.post("/generate", response_model=ApiResponse[dict])
async def invoice_generate_route(
    payload: InvoiceGenerateScope,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await generate_invoices(scope, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[InvoiceRead]])
async def invoice_search_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    student_user_id: Annotated[str | None, Query()] = None,
    roll_number: Annotated[str | None, Query()] = None,
    invoice_number: Annotated[str | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    invoice_status: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[InvoiceRead]]:
    return success_response(
        await search_invoices(
            scope,
            pagination,
            student_user_id=student_user_id,
            roll_number=roll_number,
            invoice_number=invoice_number,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
            programme_code=programme_code,
            invoice_status=invoice_status,
        ),
        request_id=get_request_id(),
    )


@router.get("/{invoice_id}", response_model=ApiResponse[InvoiceRead])
async def invoice_get_route(
    invoice_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[InvoiceRead]:
    return success_response(await get_invoice(scope, invoice_id), request_id=get_request_id())


@router.post("/{invoice_id}/issue", response_model=ApiResponse[InvoiceRead])
async def invoice_issue_route(
    invoice_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    payload: InvoiceIssueRequest | None = None,
) -> ApiResponse[InvoiceRead]:
    note = payload.note if payload else None
    return success_response(await issue_invoice(scope, invoice_id, note=note), request_id=get_request_id())


@router.post("/{invoice_id}/adjustments", response_model=ApiResponse[InvoiceRead])
async def invoice_adjustment_route(
    invoice_id: str,
    payload: InvoiceAdjustmentRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[InvoiceRead]:
    return success_response(await apply_invoice_adjustment(scope, invoice_id, payload), request_id=get_request_id())