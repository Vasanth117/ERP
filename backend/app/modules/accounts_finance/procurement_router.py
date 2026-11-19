"""Procurement and vendor finance routes."""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.accounts_finance.deps import finance_staff_user
from app.modules.accounts_finance.procurement_service import (
    approve_purchase_request,
    confirm_vendor_payment,
    create_purchase_order,
    create_purchase_request,
    procurement_reports,
    record_vendor_invoice,
    verify_vendor_invoice,
)
from app.modules.accounts_finance.vendor_service import list_vendors, register_vendor, verify_vendor
from app.modules.auth.models import User

router = APIRouter(prefix="/procurement", tags=["accounts-finance-procurement"])


class VendorRegisterInput(BaseModel):
    vendor_id: str
    name: str
    vendor_code: str | None = None
    category: str | None = None
    gstin: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    authorized_representative: str | None = None
    document_refs: list[str] = Field(default_factory=list)


class PurchaseRequestInput(BaseModel):
    request_id: str
    description: str
    estimated_amount: float = Field(ge=0)
    department_id: str | None = None
    finance_budget_id: str | None = None
    quantity: float = 1
    submit: bool = False


class PurchaseOrderInput(BaseModel):
    order_id: str
    vendor_id: str
    request_id: str | None = None
    finance_budget_id: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
    tax_amount: float = 0


class VendorInvoiceInput(BaseModel):
    invoice_id: str
    vendor_id: str
    amount: float = Field(gt=0)
    vendor_invoice_number: str | None = None
    order_id: str | None = None
    invoice_date: date | None = None
    tax_amount: float = 0
    due_date: date | None = None


class VendorPaymentInput(BaseModel):
    invoice_id: str
    amount: float = Field(gt=0)
    payment_reference: str


@router.post("/vendors")
async def register_vendor_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: VendorRegisterInput,
) -> ApiResponse[dict]:
    return success_response(await register_vendor(scope, body.model_dump()), request_id=get_request_id())


@router.get("/vendors")
async def list_vendors_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[list]:
    return success_response(await list_vendors(scope), request_id=get_request_id())


@router.post("/vendors/{vendor_id}/verify")
async def verify_vendor_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    vendor_id: str,
    approved: bool = True,
) -> ApiResponse[dict]:
    return success_response(await verify_vendor(scope, vendor_id, approved=approved), request_id=get_request_id())


@router.post("/purchase-requests")
async def create_pr_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: PurchaseRequestInput,
) -> ApiResponse[dict]:
    return success_response(await create_purchase_request(scope, body.model_dump()), request_id=get_request_id())


@router.post("/purchase-requests/{request_id}/approve")
async def approve_pr_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    request_id: str,
    approved: bool = True,
) -> ApiResponse[dict]:
    return success_response(await approve_purchase_request(scope, request_id, approved=approved), request_id=get_request_id())


@router.post("/purchase-orders")
async def create_po_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: PurchaseOrderInput,
) -> ApiResponse[dict]:
    return success_response(await create_purchase_order(scope, body.model_dump()), request_id=get_request_id())


@router.post("/vendor-invoices")
async def vendor_invoice_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: VendorInvoiceInput,
) -> ApiResponse[dict]:
    return success_response(await record_vendor_invoice(scope, body.model_dump()), request_id=get_request_id())


@router.post("/vendor-invoices/{invoice_id}/verify")
async def verify_invoice_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    invoice_id: str,
) -> ApiResponse[dict]:
    return success_response(await verify_vendor_invoice(scope, invoice_id), request_id=get_request_id())


@router.post("/vendor-payments")
async def vendor_payment_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
    body: VendorPaymentInput,
) -> ApiResponse[dict]:
    return success_response(await confirm_vendor_payment(scope, body.model_dump()), request_id=get_request_id())


@router.get("/reports/summary")
async def procurement_reports_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(finance_staff_user)],
) -> ApiResponse[dict]:
    return success_response(await procurement_reports(scope), request_id=get_request_id())