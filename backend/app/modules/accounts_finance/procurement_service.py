"""Procurement, vendor invoices, payables and payments."""

import uuid
from datetime import date
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.budget_service import record_commitment
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.period_lock_service import assert_period_open_for_date
from app.modules.accounts_finance.phase10_enums import VendorInvoiceVerificationStatus, VendorVerificationStatus
from app.modules.accounts_finance.phase10_models import (
    PurchaseOrderHistory,
    PurchaseOrderItem,
    PurchaseRequestApprovalHistory,
    VendorInvoiceVerificationHistory,
    VendorPayable,
    VendorPayment,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_procurement_approve,
    authorize_finance_procurement_manage,
    authorize_finance_procurement_pay,
    authorize_finance_procurement_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.finance_ext_models import (
    InstitutionPurchaseOrder,
    InstitutionPurchaseRequest,
    InstitutionVendorInvoice,
    InstitutionVendorRecord,
    InvoicePaymentStatus,
    PurchaseOrderStatus,
    PurchaseRequestStatus,
)
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.accounts_finance.phase9_enums import FinanceBudgetStatus
from app.modules.accounts_finance.phase9_models import FinanceBudget


async def _approved_vendor(tenant_id, vendor_id: str) -> InstitutionVendorRecord:
    vendor = await InstitutionVendorRecord.find_one(
        Eq(InstitutionVendorRecord.tenant_id, tenant_id),
        Eq(InstitutionVendorRecord.vendor_id, vendor_id),
    )
    if vendor is None or vendor.verification_status != VendorVerificationStatus.APPROVED.value:
        raise AppError(code="VALIDATION_ERROR", message="Approved vendor required", status_code=422)
    return vendor


async def create_purchase_request(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_procurement_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    request_id = payload["request_id"].strip()
    if await InstitutionPurchaseRequest.find_one(Eq(InstitutionPurchaseRequest.tenant_id, tenant_id), Eq(InstitutionPurchaseRequest.request_id, request_id)):
        raise AppError(code="CONFLICT", message="Purchase request exists", status_code=409)
    dept = to_object_id(payload.get("department_id"), "department_id") if payload.get("department_id") else None
    amount = round_money(payload["estimated_amount"])
    fb = payload.get("finance_budget_id")
    if fb:
        budget = await FinanceBudget.find_one(Eq(FinanceBudget.tenant_id, tenant_id), Eq(FinanceBudget.budget_id, fb))
        if budget is None or budget.status != FinanceBudgetStatus.ACTIVE:
            raise AppError(code="BUDGET_LIMIT", message="Active finance budget required", status_code=409)
    qty = float(payload.get("quantity") or 1)
    unit = payload.get("estimated_unit_cost")
    if unit is not None:
        amount = round_money(qty * float(unit))
    status = PurchaseRequestStatus.SUBMITTED if payload.get("submit") else PurchaseRequestStatus.DRAFT
    await InstitutionPurchaseRequest(
        tenant_id=tenant_id,
        request_id=request_id,
        request_number=payload.get("request_number") or request_id,
        department_id=dept,
        budget_id=payload.get("budget_id"),
        finance_budget_id=fb,
        cost_centre_code=payload.get("cost_centre_code"),
        description=payload["description"],
        quantity=qty,
        estimated_unit_cost=unit,
        estimated_amount=amount,
        required_date=payload.get("required_date"),
        priority=payload.get("priority") or "normal",
        reason=payload.get("reason"),
        document_refs=payload.get("document_refs") or [],
        requested_by=scope.user_id,
        status=status,
        actor_id=scope.user_id,
    ).insert()
    return {"request_id": request_id, "status": status.value}


async def approve_purchase_request(scope: AccessScope, request_id: str, *, approved: bool, note: str | None = None) -> dict:
    authorize_finance_procurement_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    doc = await InstitutionPurchaseRequest.find_one(
        Eq(InstitutionPurchaseRequest.tenant_id, tenant_id),
        Eq(InstitutionPurchaseRequest.request_id, request_id),
    )
    if doc is None or doc.status != PurchaseRequestStatus.SUBMITTED:
        raise AppError(code="CONFLICT", message="Request not submitted", status_code=409)
    if doc.requested_by == scope.user_id:
        raise AppError(code="FORBIDDEN", message="Cannot approve own purchase request", status_code=403)
    doc.status = PurchaseRequestStatus.APPROVED if approved else PurchaseRequestStatus.REJECTED
    doc.updated_at = utcnow()
    await doc.save()
    await PurchaseRequestApprovalHistory(
        tenant_id=tenant_id,
        history_id=f"prah_{uuid.uuid4().hex[:12]}",
        request_id=request_id,
        decision="approved" if approved else "rejected",
        actor_id=scope.user_id,
        note=note,
    ).insert()
    return {"request_id": request_id, "status": doc.status.value}


async def create_purchase_order(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_procurement_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    order_id = payload["order_id"].strip()
    vendor_id = payload["vendor_id"]
    await _approved_vendor(tenant_id, vendor_id)
    if await InstitutionPurchaseOrder.find_one(Eq(InstitutionPurchaseOrder.tenant_id, tenant_id), Eq(InstitutionPurchaseOrder.order_id, order_id)):
        raise AppError(code="CONFLICT", message="Purchase order exists", status_code=409)
    request_id = payload.get("request_id")
    fb = payload.get("finance_budget_id")
    if request_id:
        pr = await InstitutionPurchaseRequest.find_one(
            Eq(InstitutionPurchaseRequest.tenant_id, tenant_id),
            Eq(InstitutionPurchaseRequest.request_id, request_id),
        )
        if pr is None or pr.status != PurchaseRequestStatus.APPROVED:
            raise AppError(code="VALIDATION_ERROR", message="Approved purchase request required", status_code=422)
        fb = fb or pr.finance_budget_id
        pr.status = PurchaseRequestStatus.ORDERED
        await pr.save()
    total = 0.0
    for item in payload.get("items") or []:
        line = round_money(float(item["quantity"]) * float(item["unit_price"]))
        total += line
        await PurchaseOrderItem(
            tenant_id=tenant_id,
            item_id=f"poi_{uuid.uuid4().hex[:10]}",
            order_id=order_id,
            description=item["description"],
            quantity=float(item["quantity"]),
            unit_price=float(item["unit_price"]),
            line_total=line,
        ).insert()
    tax = round_money(float(payload.get("tax_amount") or 0))
    total = round_money(total + tax)
    if fb:
        await record_commitment(
            scope,
            fb,
            {
                "reference_type": "purchase_order",
                "reference_id": order_id,
                "amount": total,
                "note": payload.get("note"),
            },
        )
    po = InstitutionPurchaseOrder(
        tenant_id=tenant_id,
        order_id=order_id,
        request_id=request_id,
        vendor_id=vendor_id,
        finance_budget_id=fb,
        cost_centre_code=payload.get("cost_centre_code"),
        total_amount=total,
        tax_amount=tax,
        payment_terms=payload.get("payment_terms"),
        delivery_terms=payload.get("delivery_terms"),
        expected_delivery=payload.get("expected_delivery"),
        published=True,
        status=PurchaseOrderStatus.ISSUED,
        actor_id=scope.user_id,
    )
    await po.insert()
    await PurchaseOrderHistory(
        tenant_id=tenant_id,
        history_id=f"poh_{uuid.uuid4().hex[:12]}",
        order_id=order_id,
        action="issued",
        actor_id=scope.user_id,
    ).insert()
    return {"order_id": order_id, "total_amount": total, "status": po.status.value}


async def record_vendor_invoice(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_procurement_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    invoice_id = payload["invoice_id"].strip()
    vendor_invoice_number = payload.get("vendor_invoice_number")
    if vendor_invoice_number:
        dup = await InstitutionVendorInvoice.find_one(
            Eq(InstitutionVendorInvoice.tenant_id, tenant_id),
            Eq(InstitutionVendorInvoice.vendor_invoice_number, vendor_invoice_number),
            Eq(InstitutionVendorInvoice.vendor_id, payload["vendor_id"]),
        )
        if dup:
            raise AppError(code="CONFLICT", message="Duplicate vendor invoice number", status_code=409)
    total_payable = round_money(float(payload["amount"]) + float(payload.get("tax_amount") or 0) - float(payload.get("discount_amount") or 0))
    inv = InstitutionVendorInvoice(
        tenant_id=tenant_id,
        invoice_id=invoice_id,
        vendor_invoice_number=vendor_invoice_number,
        vendor_id=payload["vendor_id"],
        order_id=payload.get("order_id"),
        invoice_date=payload.get("invoice_date"),
        amount=round_money(payload["amount"]),
        tax_amount=round_money(payload.get("tax_amount") or 0),
        discount_amount=round_money(payload.get("discount_amount") or 0),
        total_payable=total_payable,
        due_date=payload.get("due_date"),
        document_refs=payload.get("document_refs") or [],
        actor_id=scope.user_id,
    )
    await inv.insert()
    await VendorPayable(
        tenant_id=tenant_id,
        payable_id=f"vpy_{uuid.uuid4().hex[:10]}",
        invoice_id=invoice_id,
        vendor_id=inv.vendor_id,
        invoice_amount=total_payable,
        outstanding=total_payable,
        due_date=inv.due_date,
    ).insert()
    return {"invoice_id": invoice_id, "total_payable": total_payable, "verification_status": inv.verification_status}


async def verify_vendor_invoice(scope: AccessScope, invoice_id: str) -> dict:
    authorize_finance_procurement_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    inv = await InstitutionVendorInvoice.find_one(
        Eq(InstitutionVendorInvoice.tenant_id, tenant_id),
        Eq(InstitutionVendorInvoice.invoice_id, invoice_id),
    )
    if inv is None:
        raise AppError(code="NOT_FOUND", message="Invoice not found", status_code=404)
    discrepancies: list[dict] = []
    if inv.order_id:
        po = await InstitutionPurchaseOrder.find_one(
            Eq(InstitutionPurchaseOrder.tenant_id, tenant_id),
            Eq(InstitutionPurchaseOrder.order_id, inv.order_id),
        )
        if po and inv.total_payable and inv.total_payable > po.total_amount:
            discrepancies.append({"type": "amount_over_po", "po_total": po.total_amount, "invoice_total": inv.total_payable})
    status = VendorInvoiceVerificationStatus.VERIFIED.value if not discrepancies else VendorInvoiceVerificationStatus.MISMATCH.value
    inv.verification_status = status
    inv.updated_at = utcnow()
    await inv.save()
    await VendorInvoiceVerificationHistory(
        tenant_id=tenant_id,
        history_id=f"vih_{uuid.uuid4().hex[:12]}",
        invoice_id=invoice_id,
        status=status,
        discrepancies=discrepancies,
        actor_id=scope.user_id,
    ).insert()
    if status == VendorInvoiceVerificationStatus.VERIFIED.value:
        await _post_vendor_liability_gl(tenant_id, inv, scope.user_id)
        from app.modules.accounts_finance.phase11_enums import FinanceTaxCategory
        from app.modules.accounts_finance.tax_service import capture_tax_transaction

        await capture_tax_transaction(
            tenant_id,
            source_type="vendor_invoice",
            source_id=invoice_id,
            tax_category=FinanceTaxCategory.INDIRECT.value,
            taxable_amount=inv.amount,
            transaction_date=inv.invoice_date or date.today(),
            document_tax_amount=inv.tax_amount,
        )
    return {"invoice_id": invoice_id, "verification_status": status, "discrepancies": discrepancies}


async def _post_vendor_liability_gl(tenant_id, inv: InstitutionVendorInvoice, actor_id) -> None:
    from app.modules.accounts_finance.gl_posting_service import post_mapped_event

    amount = inv.total_payable or inv.amount
    await post_mapped_event(
        tenant_id=tenant_id,
        event_type="vendor_invoice",
        source_reference=inv.invoice_id,
        amount=amount,
        journal_date=inv.invoice_date or date.today(),
        narration=f"Vendor invoice {inv.vendor_invoice_number or inv.invoice_id}",
        posted_by=actor_id,
    )


async def confirm_vendor_payment(scope: AccessScope, payload: dict[str, Any]) -> dict:
    authorize_finance_procurement_pay(scope)
    tenant_id = require_finance_tenant_scope(scope)
    pay_date = payload.get("payment_date") or date.today()
    await assert_period_open_for_date(tenant_id, pay_date)
    invoice_id = payload["invoice_id"]
    inv = await InstitutionVendorInvoice.find_one(
        Eq(InstitutionVendorInvoice.tenant_id, tenant_id),
        Eq(InstitutionVendorInvoice.invoice_id, invoice_id),
    )
    if inv is None:
        raise AppError(code="NOT_FOUND", message="Invoice not found", status_code=404)
    if inv.verification_status != VendorInvoiceVerificationStatus.VERIFIED.value:
        raise AppError(code="CONFLICT", message="Invoice not verified", status_code=409)
    if not payload.get("payment_reference"):
        raise AppError(code="VALIDATION_ERROR", message="Verified payment reference required", status_code=400)
    amount = round_money(payload["amount"])
    payable = await VendorPayable.find_one(Eq(VendorPayable.tenant_id, tenant_id), Eq(VendorPayable.invoice_id, invoice_id))
    if payable is None or payable.outstanding < amount:
        raise AppError(code="VALIDATION_ERROR", message="Payment exceeds outstanding payable", status_code=422)
    payment_id = f"vpay_{uuid.uuid4().hex[:10]}"
    await VendorPayment(
        tenant_id=tenant_id,
        payment_id=payment_id,
        vendor_id=inv.vendor_id,
        invoice_id=invoice_id,
        amount=amount,
        payment_reference=payload["payment_reference"],
        initiated_by=scope.user_id,
        approved_by=scope.user_id,
    ).insert()
    payable.amount_paid = round_money(payable.amount_paid + amount)
    payable.outstanding = round_money(payable.invoice_amount + payable.adjustments - payable.amount_paid)
    payable.payment_status = "paid" if payable.outstanding <= 0 else "partial"
    payable.updated_at = utcnow()
    await payable.save()
    inv.paid_amount = round_money(inv.paid_amount + amount)
    inv.payment_status = InvoicePaymentStatus.PAID if inv.paid_amount >= (inv.total_payable or inv.amount) else InvoicePaymentStatus.PARTIAL
    inv.updated_at = utcnow()
    await inv.save()
    from app.modules.accounts_finance.gl_posting_service import post_mapped_event

    await post_mapped_event(
        tenant_id=tenant_id,
        event_type="vendor_payment",
        source_reference=payment_id,
        amount=amount,
        journal_date=pay_date,
        narration=f"Vendor payment {payload['payment_reference']}",
        posted_by=scope.user_id,
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="finance.vendor.payment",
        module="accounts_finance",
        resource_type="vendor_payment",
        resource_id=payment_id,
    )
    return {"payment_id": payment_id, "outstanding": payable.outstanding}


async def procurement_reports(scope: AccessScope) -> dict:
    authorize_finance_procurement_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    requests = await InstitutionPurchaseRequest.find(Eq(InstitutionPurchaseRequest.tenant_id, tenant_id)).to_list()
    orders = await InstitutionPurchaseOrder.find(Eq(InstitutionPurchaseOrder.tenant_id, tenant_id)).to_list()
    invoices = await InstitutionVendorInvoice.find(Eq(InstitutionVendorInvoice.tenant_id, tenant_id)).to_list()
    payables = await VendorPayable.find(Eq(VendorPayable.tenant_id, tenant_id)).to_list()
    return {
        "purchase_requests_by_status": {s.value: sum(1 for r in requests if r.status == s) for s in PurchaseRequestStatus},
        "purchase_orders": len(orders),
        "vendor_invoices": len(invoices),
        "outstanding_payables": round_money(sum(p.outstanding for p in payables)),
        "overdue_invoices": sum(
            1 for i in invoices if i.due_date and i.due_date < date.today() and i.payment_status != InvoicePaymentStatus.PAID
        ),
    }