"""Refunds, reversals and refund dashboard."""

from datetime import date, datetime
from typing import Any
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.ledger_posting_service import post_ledger_entry
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.payment_core import verified_payments_total
from app.modules.accounts_finance.phase4_enums import LedgerEntryType
from app.modules.accounts_finance.phase7_enums import RefundWorkflowStatus, ReversalRequestStatus
from app.modules.accounts_finance.phase7_models import (
    StudentPaymentReversalHistory,
    StudentPaymentReversalRequest,
    StudentRefundApprovalHistory,
    StudentRefundRequest,
    StudentRefundTransaction,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_refund_approve,
    authorize_finance_refund_manage,
    authorize_finance_refund_read,
    require_finance_tenant_scope,
)
from app.modules.accounts_finance.period_lock_service import assert_period_open_for_date
from app.modules.college_admin.finance_admin_models import RefundRequest
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus, RefundStatus
from app.modules.finance.finance_models import PaymentReceipt, PaymentTransaction, RefundRecord, StudentFeeDemand


def _verified_tx(tx: PaymentTransaction) -> bool:
    return tx.status == PaymentTransactionStatus.SUCCESS and (tx.payment_mode == "offline" or tx.webhook_verified)


async def refundable_amount(tenant_id, transaction_id: str) -> dict[str, Any]:
    tx = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.transaction_id, transaction_id),
    )
    if tx is None:
        raise AppError(code="NOT_FOUND", message="Payment transaction not found", status_code=404)
    if not _verified_tx(tx):
        return {"transaction_id": transaction_id, "eligible": False, "reason": "Payment not verified", "refundable": 0.0}
    already = round_money(tx.refunded_total + tx.reversed_total)
    refundable = round_money(max(0.0, tx.amount - already))
    return {
        "transaction_id": transaction_id,
        "eligible": refundable > 0,
        "payment_amount": tx.amount,
        "refunded_total": tx.refunded_total,
        "reversed_total": tx.reversed_total,
        "refundable": refundable,
    }


async def create_refund_request(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_refund_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    await assert_period_open_for_date(tenant_id)
    student_user_id = to_object_id(payload["student_user_id"], "student_user_id")
    transaction_id = payload["transaction_id"]
    eligibility = await refundable_amount(tenant_id, transaction_id)
    if not eligibility["eligible"]:
        raise AppError(code="FORBIDDEN", message=eligibility.get("reason", "Not eligible for refund"), status_code=403)
    amount = round_money(payload["requested_amount"])
    if amount > eligibility["refundable"]:
        raise AppError(code="VALIDATION_ERROR", message="Requested amount exceeds refundable balance", status_code=422)
    tx = await PaymentTransaction.find_one(Eq(PaymentTransaction.tenant_id, tenant_id), Eq(PaymentTransaction.transaction_id, transaction_id))
    if tx is None or tx.student_user_id != student_user_id:
        raise AppError(code="NOT_FOUND", message="Transaction not found for student", status_code=404)

    refund_request_id = f"rfd_req_{uuid4().hex[:12]}"
    receipt = await PaymentReceipt.find_one(Eq(PaymentReceipt.tenant_id, tenant_id), Eq(PaymentReceipt.transaction_id, transaction_id))
    row = await StudentRefundRequest(
        tenant_id=tenant_id,
        refund_request_id=refund_request_id,
        student_user_id=student_user_id,
        transaction_id=transaction_id,
        invoice_id=payload.get("invoice_id") or tx.invoice_id,
        receipt_id=receipt.receipt_id if receipt else None,
        category=payload.get("category", "other"),
        requested_amount=amount,
        reason=payload["reason"],
        document_refs=payload.get("document_refs") or [],
        expected_refund_method=payload.get("expected_refund_method"),
        status=RefundWorkflowStatus.PENDING_APPROVAL,
        requested_by=scope.user_id,
    ).insert()
    await StudentRefundApprovalHistory(
        tenant_id=tenant_id,
        history_id=f"rfh_{uuid4().hex[:10]}",
        refund_request_id=refund_request_id,
        action="submit",
        actor_id=scope.user_id,
        note=payload["reason"],
    ).insert()
    return {"refund_request_id": refund_request_id, "status": row.status.value, "requested_amount": amount}


async def approve_refund_request(scope: AccessScope, refund_request_id: str, approved_amount: float | None = None) -> dict[str, Any]:
    authorize_finance_refund_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    req = await StudentRefundRequest.find_one(
        Eq(StudentRefundRequest.tenant_id, tenant_id),
        Eq(StudentRefundRequest.refund_request_id, refund_request_id),
    )
    if req is None:
        raise AppError(code="NOT_FOUND", message="Refund request not found", status_code=404)
    if req.status not in (RefundWorkflowStatus.PENDING_APPROVAL, RefundWorkflowStatus.UNDER_REVIEW):
        raise AppError(code="CONFLICT", message="Refund cannot be approved", status_code=409)
    amount = round_money(approved_amount if approved_amount is not None else req.requested_amount)
    eligibility = await refundable_amount(tenant_id, req.transaction_id)
    if amount > eligibility["refundable"]:
        raise AppError(code="VALIDATION_ERROR", message="Approved amount exceeds refundable balance", status_code=422)
    req.approved_amount = amount
    req.status = RefundWorkflowStatus.APPROVED
    req.approved_by = scope.user_id
    req.updated_at = utcnow()
    await req.save()
    await StudentRefundApprovalHistory(
        tenant_id=tenant_id,
        history_id=f"rfh_{uuid4().hex[:10]}",
        refund_request_id=refund_request_id,
        action="approve",
        actor_id=scope.user_id,
    ).insert()
    return {"refund_request_id": refund_request_id, "status": req.status.value, "approved_amount": amount}


async def complete_refund(scope: AccessScope, refund_request_id: str, payout_reference: str) -> dict[str, Any]:
    authorize_finance_refund_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    req = await StudentRefundRequest.find_one(
        Eq(StudentRefundRequest.tenant_id, tenant_id),
        Eq(StudentRefundRequest.refund_request_id, refund_request_id),
    )
    if req is None:
        raise AppError(code="NOT_FOUND", message="Refund request not found", status_code=404)
    if req.status != RefundWorkflowStatus.APPROVED:
        raise AppError(code="CONFLICT", message="Refund must be approved before completion", status_code=409)
    amount = round_money(req.approved_amount or req.requested_amount)
    eligibility = await refundable_amount(tenant_id, req.transaction_id)
    if amount > eligibility["refundable"]:
        raise AppError(code="CONFLICT", message="Refund exceeds eligible amount", status_code=409)

    existing_tx = await StudentRefundTransaction.find_one(
        Eq(StudentRefundTransaction.tenant_id, tenant_id),
        Eq(StudentRefundTransaction.refund_request_id, refund_request_id),
    )
    if existing_tx and existing_tx.status == "successful":
        raise AppError(code="CONFLICT", message="Refund already completed", status_code=409)

    posting_key = f"refund:{refund_request_id}"
    entry = await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=req.student_user_id,
        entry_type=LedgerEntryType.REFUND.value,
        description=f"Refund {refund_request_id}",
        debit=amount,
        credit=0,
        source_reference=refund_request_id,
        posting_key=posting_key,
        payment_transaction_id=req.transaction_id,
        posted_by=scope.user_id,
        narration=f"payout={payout_reference}",
    )

    refund_tx_id = f"rfd_tx_{uuid4().hex[:10]}"
    if existing_tx is None:
        await StudentRefundTransaction(
            tenant_id=tenant_id,
            refund_tx_id=refund_tx_id,
            refund_request_id=refund_request_id,
            transaction_id=req.transaction_id,
            amount=amount,
            payout_reference=payout_reference,
            ledger_entry_id=entry.entry_id,
            posting_key=posting_key,
            status="successful",
        ).insert()
    else:
        existing_tx.status = "successful"
        existing_tx.payout_reference = payout_reference
        existing_tx.ledger_entry_id = entry.entry_id
        await existing_tx.save()

    tx = await PaymentTransaction.find_one(Eq(PaymentTransaction.tenant_id, tenant_id), Eq(PaymentTransaction.transaction_id, req.transaction_id))
    if tx:
        tx.refunded_total = round_money(tx.refunded_total + amount)
        if round_money(tx.refunded_total + tx.reversed_total) >= tx.amount:
            tx.status = PaymentTransactionStatus.REFUNDED
        tx.updated_at = utcnow()
        await tx.save()
        if tx.demand_id:
            demand = await StudentFeeDemand.find_one(Eq(StudentFeeDemand.tenant_id, tenant_id), Eq(StudentFeeDemand.demand_id, tx.demand_id))
            if demand and demand.status == FeeDemandStatus.PAID:
                paid = await verified_payments_total(tenant_id, tx.demand_id)
                net_paid = round_money(paid - tx.refunded_total)
                if net_paid < demand.amount:
                    demand.status = FeeDemandStatus.PARTIALLY_PAID if net_paid > 0 else FeeDemandStatus.OPEN
                    await demand.save()

    legacy_id = f"rfd_{uuid4().hex[:12]}"
    await RefundRecord(
        tenant_id=tenant_id,
        student_user_id=req.student_user_id,
        refund_id=legacy_id,
        transaction_id=req.transaction_id,
        refund_request_id=refund_request_id,
        invoice_id=req.invoice_id,
        receipt_id=req.receipt_id,
        amount=amount,
        category=req.category,
        status=RefundStatus.PROCESSED,
        updated_at=utcnow(),
    ).insert()
    await RefundRequest(
        tenant_id=tenant_id,
        student_user_id=req.student_user_id,
        refund_id=legacy_id,
        amount=amount,
        status=RefundStatus.PROCESSED,
        requires_approval=False,
        actor_id=scope.user_id,
    ).insert()

    req.status = RefundWorkflowStatus.SUCCESSFUL
    req.payout_reference = payout_reference
    req.updated_at = utcnow()
    await req.save()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="refund_completed",
        module="accounts_finance",
        resource_type="student_refund_request",
        resource_id=refund_request_id,
        metadata={"amount": amount, "payout_reference": payout_reference},
    )
    return {"refund_request_id": refund_request_id, "status": req.status.value, "ledger_entry_id": entry.entry_id}


async def reject_refund_request(scope: AccessScope, refund_request_id: str, reason: str) -> dict[str, Any]:
    authorize_finance_refund_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    req = await StudentRefundRequest.find_one(
        Eq(StudentRefundRequest.tenant_id, tenant_id),
        Eq(StudentRefundRequest.refund_request_id, refund_request_id),
    )
    if req is None:
        raise AppError(code="NOT_FOUND", message="Refund request not found", status_code=404)
    req.status = RefundWorkflowStatus.CANCELLED
    req.updated_at = utcnow()
    await req.save()
    await StudentRefundApprovalHistory(
        tenant_id=tenant_id,
        history_id=f"rfh_{uuid4().hex[:10]}",
        refund_request_id=refund_request_id,
        action="reject",
        actor_id=scope.user_id,
        note=reason,
    ).insert()
    return {"refund_request_id": refund_request_id, "status": req.status.value}


async def create_payment_reversal(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_refund_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    student_user_id = to_object_id(payload["student_user_id"], "student_user_id")
    transaction_id = payload["transaction_id"]
    tx = await PaymentTransaction.find_one(Eq(PaymentTransaction.tenant_id, tenant_id), Eq(PaymentTransaction.transaction_id, transaction_id))
    if tx is None or tx.student_user_id != student_user_id:
        raise AppError(code="NOT_FOUND", message="Transaction not found", status_code=404)
    if not _verified_tx(tx):
        raise AppError(code="FORBIDDEN", message="Only verified payments can be reversed", status_code=403)
    amount = round_money(payload["amount"])
    max_rev = round_money(tx.amount - tx.refunded_total - tx.reversed_total)
    if amount > max_rev:
        raise AppError(code="VALIDATION_ERROR", message="Reversal exceeds remaining posted amount", status_code=422)
    reversal_request_id = f"rev_req_{uuid4().hex[:12]}"
    row = await StudentPaymentReversalRequest(
        tenant_id=tenant_id,
        reversal_request_id=reversal_request_id,
        student_user_id=student_user_id,
        transaction_id=transaction_id,
        receipt_id=payload.get("receipt_id"),
        amount=amount,
        reason=payload["reason"],
        requested_by=scope.user_id,
    ).insert()
    return {"reversal_request_id": reversal_request_id, "status": row.status.value}


async def approve_payment_reversal(scope: AccessScope, reversal_request_id: str) -> dict[str, Any]:
    authorize_finance_refund_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    req = await StudentPaymentReversalRequest.find_one(
        Eq(StudentPaymentReversalRequest.tenant_id, tenant_id),
        Eq(StudentPaymentReversalRequest.reversal_request_id, reversal_request_id),
    )
    if req is None:
        raise AppError(code="NOT_FOUND", message="Reversal request not found", status_code=404)
    if req.status != ReversalRequestStatus.SUBMITTED:
        raise AppError(code="CONFLICT", message="Reversal cannot be approved", status_code=409)
    posting_key = f"payment_reversal:{reversal_request_id}"
    entry = await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=req.student_user_id,
        entry_type=LedgerEntryType.PAYMENT_REVERSAL.value,
        description=f"Payment reversal {reversal_request_id}",
        debit=req.amount,
        credit=0,
        source_reference=reversal_request_id,
        posting_key=posting_key,
        payment_transaction_id=req.transaction_id,
        posted_by=scope.user_id,
        narration=req.reason,
    )
    tx = await PaymentTransaction.find_one(Eq(PaymentTransaction.tenant_id, tenant_id), Eq(PaymentTransaction.transaction_id, req.transaction_id))
    if tx:
        tx.reversed_total = round_money(tx.reversed_total + req.amount)
        tx.updated_at = utcnow()
        await tx.save()
    req.status = ReversalRequestStatus.POSTED
    req.approved_by = scope.user_id
    req.ledger_entry_id = entry.entry_id
    req.posting_key = posting_key
    req.updated_at = utcnow()
    await req.save()
    await StudentPaymentReversalHistory(
        tenant_id=tenant_id,
        history_id=f"rvh_{uuid4().hex[:10]}",
        reversal_request_id=reversal_request_id,
        action="approve_post",
        actor_id=scope.user_id,
        note=req.reason,
    ).insert()
    return {"reversal_request_id": reversal_request_id, "status": req.status.value, "ledger_entry_id": entry.entry_id}


async def refund_dashboard(scope: AccessScope) -> dict[str, Any]:
    authorize_finance_refund_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rows = await StudentRefundRequest.find(Eq(StudentRefundRequest.tenant_id, tenant_id)).to_list()
    by_status: dict[str, int] = {}
    requested_total = approved_total = completed_total = 0.0
    for r in rows:
        st = r.status.value
        by_status[st] = by_status.get(st, 0) + 1
        requested_total += r.requested_amount
        if r.approved_amount:
            approved_total += r.approved_amount
        if r.status == RefundWorkflowStatus.SUCCESSFUL:
            completed_total += r.approved_amount or r.requested_amount
    reversals = await StudentPaymentReversalRequest.find(Eq(StudentPaymentReversalRequest.tenant_id, tenant_id)).to_list()
    return {
        "total_requests": len(rows),
        "by_status": by_status,
        "pending_approval": by_status.get(RefundWorkflowStatus.PENDING_APPROVAL.value, 0),
        "approved": by_status.get(RefundWorkflowStatus.APPROVED.value, 0),
        "successful": by_status.get(RefundWorkflowStatus.SUCCESSFUL.value, 0),
        "total_requested_amount": round_money(requested_total),
        "total_approved_amount": round_money(approved_total),
        "total_completed_amount": round_money(completed_total),
        "reversal_requests": len(reversals),
        "reversal_exceptions": sum(1 for x in reversals if x.status == ReversalRequestStatus.SUBMITTED),
    }


async def list_refund_requests(scope: AccessScope, pagination: Pagination, **filters) -> Page[dict[str, Any]]:
    authorize_finance_refund_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query: dict[str, Any] = {"tenant_id": tenant_id}
    if filters.get("student_user_id"):
        query["student_user_id"] = to_object_id(filters["student_user_id"], "student_user_id")
    if filters.get("transaction_id"):
        query["transaction_id"] = filters["transaction_id"]
    if filters.get("status"):
        query["status"] = filters["status"]
    total = await StudentRefundRequest.find(query).count()
    rows = (
        await StudentRefundRequest.find(query).sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    )
    items = [
        {
            "refund_request_id": r.refund_request_id,
            "student_user_id": str(r.student_user_id),
            "transaction_id": r.transaction_id,
            "category": r.category,
            "requested_amount": r.requested_amount,
            "approved_amount": r.approved_amount,
            "status": r.status.value,
            "created_at": r.created_at,
        }
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)