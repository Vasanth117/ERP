"""Student financial ledger reads, statements, adjustments, advances, reconciliation."""

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
from app.modules.accounts_finance.phase4_enums import LedgerAdjustmentStatus, LedgerEntryType
from app.modules.accounts_finance.phase4_models import (
    StudentAdvanceAllocation,
    StudentAdvancePayment,
    StudentFinancialAccount,
    StudentLedgerAdjustment,
    StudentLedgerReconciliationRecord,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_ledger_manage,
    authorize_finance_ledger_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import (
    PaymentReceipt,
    PaymentTransaction,
    StudentFeeDemand,
    StudentFeeInvoice,
    StudentFinancialLedgerEntry,
)
from app.modules.students.models import StudentProfile

_CHARGE_TYPES = frozenset(
    {
        LedgerEntryType.FEE_ASSESSMENT.value,
        LedgerEntryType.FEE_INVOICE.value,
        LedgerEntryType.DEBIT_NOTE.value,
        LedgerEntryType.LATE_FEE.value,
        LedgerEntryType.PAYMENT_REVERSAL.value,
        "fee_invoice",
        "fee_assessment",
        "payment",
    }
)


def _entry_filters(query: dict[str, Any], **kwargs) -> dict[str, Any]:
    if kwargs.get("academic_year_label"):
        query["academic_year_label"] = kwargs["academic_year_label"]
    if kwargs.get("semester_label"):
        query["semester_label"] = kwargs["semester_label"]
    if kwargs.get("entry_type"):
        query["entry_type"] = kwargs["entry_type"]
    if kwargs.get("transaction_status"):
        query["transaction_status"] = kwargs["transaction_status"]
    if kwargs.get("issued_from") or kwargs.get("issued_to"):
        posted: dict[str, Any] = {}
        if kwargs.get("issued_from"):
            posted["$gte"] = datetime.combine(kwargs["issued_from"], datetime.min.time())
        if kwargs.get("issued_to"):
            posted["$lte"] = datetime.combine(kwargs["issued_to"], datetime.max.time())
        query["posted_at"] = posted
    return query


async def _overdue_balance(tenant_id, student_user_id) -> float:
    demands = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        Eq(StudentFeeDemand.student_user_id, student_user_id),
    ).to_list()
    total = 0.0
    today = date.today()
    for d in demands:
        if d.status in (FeeDemandStatus.PAID, FeeDemandStatus.WAIVED):
            continue
        if d.due_date and d.due_date < today:
            from app.modules.accounts_finance.payment_core import demand_outstanding

            total += await demand_outstanding(tenant_id, d)
    return round_money(total)


def _ledger_row(entry: StudentFinancialLedgerEntry) -> dict[str, Any]:
    return {
        "entry_id": entry.entry_id,
        "entry_type": entry.entry_type,
        "description": entry.description,
        "debit": entry.debit,
        "credit": entry.credit,
        "balance_after": entry.balance_after,
        "reference_id": entry.reference_id,
        "invoice_id": entry.invoice_id,
        "payment_transaction_id": entry.payment_transaction_id,
        "receipt_id": entry.receipt_id,
        "academic_year_label": entry.academic_year_label,
        "semester_label": entry.semester_label,
        "transaction_status": entry.transaction_status,
        "narration": entry.narration,
        "posted_at": entry.posted_at,
        "transaction_date": entry.transaction_date,
    }


async def get_student_account(scope: AccessScope, student_user_id: str) -> dict[str, Any]:
    authorize_finance_ledger_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    sid = to_object_id(student_user_id, "student_user_id")
    acct = await StudentFinancialAccount.find_one(
        Eq(StudentFinancialAccount.tenant_id, tenant_id),
        Eq(StudentFinancialAccount.student_user_id, sid),
    )
    entries = await StudentFinancialLedgerEntry.find(
        {"tenant_id": tenant_id, "student_user_id": sid}
    ).to_list()

    total_invoices = round_money(
        sum(e.debit for e in entries if e.entry_type in (LedgerEntryType.FEE_INVOICE.value, "fee_invoice"))
    )
    total_payments = round_money(
        sum(
            e.credit
            for e in entries
            if e.entry_type in (LedgerEntryType.VERIFIED_PAYMENT.value, "payment", "verified_payment")
        )
    )
    total_scholarships = round_money(sum(e.credit for e in entries if e.entry_type == LedgerEntryType.SCHOLARSHIP_CREDIT.value))
    total_concessions = round_money(
        sum(e.credit for e in entries if e.entry_type in (LedgerEntryType.CONCESSION_CREDIT.value, LedgerEntryType.FEE_WAIVER.value))
    )
    total_refunds = round_money(sum(e.debit for e in entries if e.entry_type == LedgerEntryType.REFUND.value))
    total_reversals = round_money(sum(e.debit for e in entries if e.entry_type == LedgerEntryType.PAYMENT_REVERSAL.value))

    opening = acct.opening_balance if acct else 0.0
    outstanding = acct.outstanding_balance if acct else await _last_balance_only(tenant_id, sid)
    overdue = await _overdue_balance(tenant_id, sid)
    advance_unallocated = acct.advance_unallocated if acct else 0.0

    profile = await StudentProfile.find_one({"tenant_id": tenant_id, "user_id": sid})

    return {
        "student_user_id": student_user_id,
        "opening_balance": opening,
        "total_charges": acct.total_charges if acct else round_money(sum(e.debit for e in entries)),
        "total_assessed_fees": total_invoices,
        "total_invoices_issued": total_invoices,
        "total_verified_payments": total_payments,
        "total_scholarships": total_scholarships,
        "total_concessions": total_concessions,
        "total_credit_adjustments": round_money(sum(e.credit for e in entries if e.entry_type == LedgerEntryType.ADJUSTMENT.value)),
        "total_debit_adjustments": round_money(sum(e.debit for e in entries if e.entry_type == LedgerEntryType.ADJUSTMENT.value)),
        "total_refunds": total_refunds,
        "total_reversals": total_reversals,
        "outstanding_balance": outstanding,
        "overdue_balance": overdue,
        "advance_unallocated": advance_unallocated,
        "programme_code": profile.programme_code if profile else None,
        "department_id": str(profile.department_id) if profile and profile.department_id else None,
    }


async def _last_balance_only(tenant_id, student_user_id) -> float:
    last = (
        await StudentFinancialLedgerEntry.find({"tenant_id": tenant_id, "student_user_id": student_user_id})
        .sort("-posted_at")
        .limit(1)
        .to_list()
    )
    return round_money(last[0].balance_after if last else 0.0)


async def student_statement(
    scope: AccessScope,
    student_user_id: str,
    pagination: Pagination,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    issued_from: date | None = None,
    issued_to: date | None = None,
    entry_type: str | None = None,
    transaction_status: str | None = None,
) -> dict[str, Any]:
    authorize_finance_ledger_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    sid = to_object_id(student_user_id, "student_user_id")
    overview = await get_student_account(scope, student_user_id)
    query: dict[str, Any] = {"tenant_id": tenant_id, "student_user_id": sid}
    query = _entry_filters(
        query,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        issued_from=issued_from,
        issued_to=issued_to,
        entry_type=entry_type,
        transaction_status=transaction_status,
    )
    total = await StudentFinancialLedgerEntry.find(query).count()
    rows = (
        await StudentFinancialLedgerEntry.find(query)
        .sort("posted_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    return {
        "overview": overview,
        "entries": Page(items=[_ledger_row(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset),
        "closing_balance": overview["outstanding_balance"],
    }


async def list_ledger_entries(
    scope: AccessScope,
    pagination: Pagination,
    *,
    student_user_id: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    entry_type: str | None = None,
    issued_from: date | None = None,
    issued_to: date | None = None,
) -> Page[dict[str, Any]]:
    authorize_finance_ledger_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query: dict[str, Any] = {"tenant_id": tenant_id}
    if student_user_id:
        query["student_user_id"] = to_object_id(student_user_id, "student_user_id")
    query = _entry_filters(
        query,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        entry_type=entry_type,
        issued_from=issued_from,
        issued_to=issued_to,
    )
    total = await StudentFinancialLedgerEntry.find(query).count()
    rows = (
        await StudentFinancialLedgerEntry.find(query)
        .sort("-posted_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    return Page(items=[_ledger_row(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def create_ledger_adjustment(
    scope: AccessScope,
    student_user_id: str,
    *,
    reason: str,
    debit: float = 0.0,
    credit: float = 0.0,
    original_entry_id: str | None = None,
) -> dict[str, Any]:
    authorize_finance_ledger_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
  # One-sided adjustment only — cannot apply both debit and credit
    if debit > 0 and credit > 0:
        raise AppError(code="VALIDATION_ERROR", message="Specify either debit or credit adjustment", status_code=422)
    if debit <= 0 and credit <= 0:
        raise AppError(code="VALIDATION_ERROR", message="Adjustment amount required", status_code=422)
    adj_id = f"adj_{uuid4().hex[:12]}"
    row = await StudentLedgerAdjustment(
        tenant_id=tenant_id,
        adjustment_id=adj_id,
        student_user_id=to_object_id(student_user_id, "student_user_id"),
        original_entry_id=original_entry_id,
        status=LedgerAdjustmentStatus.SUBMITTED,
        reason=reason,
        debit=round_money(debit),
        credit=round_money(credit),
        requested_by=scope.user_id,
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="ledger_adjustment_submitted",
        module="accounts_finance",
        resource_type="student_ledger_adjustment",
        resource_id=adj_id,
        metadata={"reason": reason},
    )
    return {
        "adjustment_id": row.adjustment_id,
        "status": row.status.value,
        "debit": row.debit,
        "credit": row.credit,
        "reason": row.reason,
    }


async def approve_ledger_adjustment(scope: AccessScope, adjustment_id: str) -> dict[str, Any]:
    authorize_finance_ledger_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    adj = await StudentLedgerAdjustment.find_one(
        Eq(StudentLedgerAdjustment.tenant_id, tenant_id),
        Eq(StudentLedgerAdjustment.adjustment_id, adjustment_id),
    )
    if adj is None:
        raise AppError(code="NOT_FOUND", message="Adjustment not found", status_code=404)
    if adj.status not in (LedgerAdjustmentStatus.SUBMITTED, LedgerAdjustmentStatus.APPROVED):
        raise AppError(code="CONFLICT", message="Adjustment cannot be approved", status_code=409)

    reversal_entry_id = None
    if adj.original_entry_id:
        original = await StudentFinancialLedgerEntry.find_one(
            Eq(StudentFinancialLedgerEntry.tenant_id, tenant_id),
            Eq(StudentFinancialLedgerEntry.entry_id, adj.original_entry_id),
        )
        if original is None:
            raise AppError(code="NOT_FOUND", message="Original ledger entry not found", status_code=404)
        rev = await post_ledger_entry(
            tenant_id=tenant_id,
            student_user_id=adj.student_user_id,
            entry_type=LedgerEntryType.ADJUSTMENT.value,
            description=f"Reversal of {original.entry_id}",
            debit=original.credit,
            credit=original.debit,
            source_reference=f"rev_{adj.adjustment_id}",
            posting_key=f"reversal:{adj.adjustment_id}",
            posted_by=scope.user_id,
            narration=adj.reason,
        )
        reversal_entry_id = rev.entry_id

    correction = await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=adj.student_user_id,
        entry_type=LedgerEntryType.ADJUSTMENT.value,
        description=f"Approved adjustment {adj.adjustment_id}",
        debit=adj.debit,
        credit=adj.credit,
        source_reference=adj.adjustment_id,
        posting_key=f"adjustment:{adj.adjustment_id}",
        posted_by=scope.user_id,
        narration=adj.reason,
    )

    adj.status = LedgerAdjustmentStatus.POSTED
    adj.approved_by = scope.user_id
    adj.reversal_entry_id = reversal_entry_id
    adj.correction_entry_id = correction.entry_id
    adj.updated_at = utcnow()
    await adj.save()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="ledger_adjustment_posted",
        module="accounts_finance",
        resource_type="student_ledger_adjustment",
        resource_id=adjustment_id,
        metadata={"reason": adj.reason},
    )
    return {
        "adjustment_id": adj.adjustment_id,
        "status": adj.status.value,
        "reversal_entry_id": reversal_entry_id,
        "correction_entry_id": correction.entry_id,
    }


async def allocate_advance(
    scope: AccessScope,
    advance_id: str,
    invoice_id: str,
    amount: float,
) -> dict[str, Any]:
    authorize_finance_ledger_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    advance = await StudentAdvancePayment.find_one(
        Eq(StudentAdvancePayment.tenant_id, tenant_id),
        Eq(StudentAdvancePayment.advance_id, advance_id),
    )
    if advance is None:
        raise AppError(code="NOT_FOUND", message="Advance payment not found", status_code=404)
    amt = round_money(amount)
    if amt <= 0 or amt > advance.unallocated_amount:
        raise AppError(code="VALIDATION_ERROR", message="Invalid allocation amount", status_code=422)
    invoice = await StudentFeeInvoice.find_one(
        Eq(StudentFeeInvoice.tenant_id, tenant_id),
        Eq(StudentFeeInvoice.invoice_id, invoice_id),
    )
    if invoice is None or invoice.student_user_id != advance.student_user_id:
        raise AppError(code="NOT_FOUND", message="Invoice not found for student", status_code=404)

    allocation_id = f"adv_alloc_{uuid4().hex[:12]}"
    await StudentAdvanceAllocation(
        tenant_id=tenant_id,
        allocation_id=allocation_id,
        advance_id=advance_id,
        invoice_id=invoice_id,
        amount=amt,
        actor_id=scope.user_id,
    ).insert()
    advance.unallocated_amount = round_money(advance.unallocated_amount - amt)
    await advance.save()

    acct = await StudentFinancialAccount.find_one(
        Eq(StudentFinancialAccount.tenant_id, tenant_id),
        Eq(StudentFinancialAccount.student_user_id, advance.student_user_id),
    )
    if acct:
        acct.advance_unallocated = round_money(acct.advance_unallocated - amt)
        acct.updated_at = utcnow()
        await acct.save()

    entry = await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=advance.student_user_id,
        entry_type=LedgerEntryType.ADVANCE_ALLOCATION.value,
        description=f"Advance allocation to invoice {invoice_id}",
        debit=amt,
        credit=0,
        source_reference=allocation_id,
        posting_key=f"advance_alloc:{allocation_id}",
        invoice_id=invoice_id,
        posted_by=scope.user_id,
    )
    return {"allocation_id": allocation_id, "ledger_entry_id": entry.entry_id, "amount": amt}


async def run_ledger_reconciliation(scope: AccessScope, student_user_id: str | None = None) -> dict[str, Any]:
    authorize_finance_ledger_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    exceptions: list[dict[str, Any]] = []

    invoice_query: dict[str, Any] = {
        "tenant_id": tenant_id,
        "invoice_status": {"$in": ["issued", "partially_paid", "overdue", "paid"]},
    }
    if student_user_id:
        invoice_query["student_user_id"] = to_object_id(student_user_id, "student_user_id")
    invoices = await StudentFeeInvoice.find(invoice_query).to_list()
    for inv in invoices:
        if inv.invoice_status == "cancelled":
            continue
        posted = await StudentFinancialLedgerEntry.find_one(
            Eq(StudentFinancialLedgerEntry.tenant_id, tenant_id),
            Eq(StudentFinancialLedgerEntry.posting_key, f"fee_invoice:{inv.invoice_id}"),
        )
        if posted is None:
            rec_id = f"rec_{uuid4().hex[:12]}"
            await StudentLedgerReconciliationRecord(
                tenant_id=tenant_id,
                reconciliation_id=rec_id,
                student_user_id=inv.student_user_id,
                exception_type="invoice_not_posted",
                detail=f"Invoice {inv.invoice_id} missing ledger posting",
            ).insert()
            exceptions.append({"reconciliation_id": rec_id, "type": "invoice_not_posted", "invoice_id": inv.invoice_id})

    pay_query: dict[str, Any] = {
        "tenant_id": tenant_id,
        "status": PaymentTransactionStatus.SUCCESS,
    }
    if student_user_id:
        pay_query["student_user_id"] = to_object_id(student_user_id, "student_user_id")
    txs = await PaymentTransaction.find(pay_query).to_list()
    for tx in txs:
        if tx.payment_mode != "offline" and not tx.webhook_verified:
            continue
        key = f"verified_payment:{tx.transaction_id}"
        posted = await StudentFinancialLedgerEntry.find_one(
            Eq(StudentFinancialLedgerEntry.tenant_id, tenant_id),
            Eq(StudentFinancialLedgerEntry.posting_key, key),
        )
        if posted is None:
            rec_id = f"rec_{uuid4().hex[:12]}"
            await StudentLedgerReconciliationRecord(
                tenant_id=tenant_id,
                reconciliation_id=rec_id,
                student_user_id=tx.student_user_id,
                exception_type="payment_not_posted",
                detail=f"Transaction {tx.transaction_id} missing ledger posting",
            ).insert()
            exceptions.append({"reconciliation_id": rec_id, "type": "payment_not_posted", "transaction_id": tx.transaction_id})
            continue
        receipt = await PaymentReceipt.find_one(
            Eq(PaymentReceipt.tenant_id, tenant_id),
            Eq(PaymentReceipt.transaction_id, tx.transaction_id),
        )
        if receipt is None:
            rec_id = f"rec_{uuid4().hex[:12]}"
            await StudentLedgerReconciliationRecord(
                tenant_id=tenant_id,
                reconciliation_id=rec_id,
                student_user_id=tx.student_user_id,
                exception_type="receipt_missing",
                detail=f"Transaction {tx.transaction_id} missing receipt",
            ).insert()
            exceptions.append({"reconciliation_id": rec_id, "type": "receipt_missing", "transaction_id": tx.transaction_id})

    advances = await StudentAdvancePayment.find(
        Eq(StudentAdvancePayment.tenant_id, tenant_id),
    ).to_list()
    for adv in advances:
        if adv.unallocated_amount > 0:
            exceptions.append(
                {
                    "type": "unallocated_advance",
                    "advance_id": adv.advance_id,
                    "amount": adv.unallocated_amount,
                    "student_user_id": str(adv.student_user_id),
                }
            )

    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="ledger_reconciliation_scan",
        module="accounts_finance",
        resource_type="student_ledger",
        resource_id=student_user_id or "tenant",
        metadata={"exception_count": len(exceptions)},
    )
    return {"exception_count": len(exceptions), "exceptions": exceptions}