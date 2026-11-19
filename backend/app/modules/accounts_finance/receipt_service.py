"""Official payment receipt lifecycle."""

from datetime import date
from typing import Any
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq
from pymongo import ReturnDocument

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.config import get_settings
from app.core.database import get_database_client
from app.core.exceptions import AppError
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase4_enums import ReceiptStatus
from app.modules.accounts_finance.phase4_models import (
    PaymentReceiptCancellation,
    PaymentReceiptDocumentHistory,
    PaymentReceiptVersion,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_receipt_issue,
    authorize_finance_receipt_manage,
    authorize_finance_receipt_read,
    require_finance_tenant_scope,
)
from app.modules.auth.models import User
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import (
    PaymentReceipt,
    PaymentTransaction,
    StudentFeeDemand,
    StudentFeeInvoice,
    StudentFinancialLedgerEntry,
)
from app.modules.tenants.models import Tenant


async def _next_receipt_number(tenant_id, fiscal_year: str) -> str:
    client = get_database_client()
    db = client[get_settings().mongodb_db_name]
    coll = db["payment_receipt_number_sequences"]
    result = await coll.find_one_and_update(
        {"tenant_id": tenant_id, "fiscal_year": fiscal_year},
        {"$inc": {"last_value": 1}, "$set": {"updated_at": utcnow()}, "$setOnInsert": {"prefix": "RCT"}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    seq = result.get("last_value", 1)
    prefix = result.get("prefix", "RCT")
    return f"{prefix}-{fiscal_year}-{seq:06d}"


def _receipt_type_for_mode(payment_mode: str | None) -> str:
    mode = (payment_mode or "online").lower()
    mapping = {
        "online": "online_payment",
        "cash": "cash",
        "cheque": "cheque",
        "dd": "demand_draft",
        "demand_draft": "demand_draft",
        "bank_transfer": "bank_transfer",
        "neft": "bank_transfer",
        "rtgs": "bank_transfer",
        "upi": "online_payment",
    }
    return mapping.get(mode, "payment")


def _serialize_receipt(row: PaymentReceipt, student: User | None = None, tenant: Tenant | None = None) -> dict[str, Any]:
    return {
        "receipt_id": row.receipt_id,
        "receipt_number": row.receipt_number,
        "transaction_id": row.transaction_id,
        "student_user_id": str(row.student_user_id),
        "student_name": student.full_name if student else None,
        "invoice_id": row.invoice_id,
        "demand_id": row.demand_id,
        "amount": row.amount,
        "payment_mode": row.payment_mode,
        "receipt_type": row.receipt_type,
        "receipt_status": row.receipt_status,
        "remaining_balance": row.remaining_balance,
        "fee_breakdown": row.fee_breakdown,
        "academic_year_label": row.academic_year_label,
        "semester_label": row.semester_label,
        "issued_at": row.issued_at,
        "institution_name": tenant.name if tenant else None,
        "storage_token": row.storage_token,
        "published": row.published,
    }


async def _resolve_invoice_for_demand(tenant_id, demand_id: str | None) -> StudentFeeInvoice | None:
    if not demand_id:
        return None
    return await StudentFeeInvoice.find_one(
        Eq(StudentFeeInvoice.tenant_id, tenant_id),
        Eq(StudentFeeInvoice.demand_id, demand_id),
    )


async def issue_receipt_from_payment(
    tx: PaymentTransaction,
    *,
    issuer_user_id=None,
) -> PaymentReceipt | None:
    if tx.status != PaymentTransactionStatus.SUCCESS:
        return None
    if tx.payment_mode != "offline" and not tx.webhook_verified:
        return None

    existing = await PaymentReceipt.find_one(
        Eq(PaymentReceipt.tenant_id, tx.tenant_id),
        Eq(PaymentReceipt.transaction_id, tx.transaction_id),
    )
    if existing is not None:
        return existing

    ledger = await StudentFinancialLedgerEntry.find_one(
        Eq(StudentFinancialLedgerEntry.tenant_id, tx.tenant_id),
        Eq(StudentFinancialLedgerEntry.payment_transaction_id, tx.transaction_id),
    )
    if ledger is None:
        ledger = await StudentFinancialLedgerEntry.find_one(
            Eq(StudentFinancialLedgerEntry.tenant_id, tx.tenant_id),
            Eq(StudentFinancialLedgerEntry.reference_id, tx.transaction_id),
            Eq(StudentFinancialLedgerEntry.entry_type, "verified_payment"),
        )
    if ledger is None:
        return None

    demand: StudentFeeDemand | None = None
    if tx.demand_id:
        demand = await StudentFeeDemand.find_one(
            Eq(StudentFeeDemand.tenant_id, tx.tenant_id),
            Eq(StudentFeeDemand.demand_id, tx.demand_id),
        )
    invoice = await _resolve_invoice_for_demand(tx.tenant_id, tx.demand_id)
    remaining = None
    if demand is not None:
        from app.modules.accounts_finance.payment_core import demand_outstanding

        remaining = await demand_outstanding(tx.tenant_id, demand)

    fiscal_year = (demand.academic_year_label if demand else None) or str(utcnow().year)
    receipt_id = f"rcpt_{uuid4().hex[:16]}"
    receipt_number = await _next_receipt_number(tx.tenant_id, fiscal_year)
    token = uuid4().hex

    breakdown: list[dict] = []
    if demand is not None:
        breakdown.append(
            {
                "description": demand.description,
                "amount": round_money(tx.amount),
            }
        )

    row = await PaymentReceipt(
        tenant_id=tx.tenant_id,
        student_user_id=tx.student_user_id,
        receipt_id=receipt_id,
        receipt_number=receipt_number,
        transaction_id=tx.transaction_id,
        invoice_id=invoice.invoice_id if invoice else None,
        demand_id=tx.demand_id,
        amount=round_money(tx.amount),
        payment_mode=tx.payment_mode,
        receipt_type=_receipt_type_for_mode(tx.payment_mode),
        remaining_balance=remaining,
        fee_breakdown=breakdown,
        academic_year_label=demand.academic_year_label if demand else None,
        semester_label=demand.semester_label if demand else None,
        receipt_status=ReceiptStatus.ISSUED.value,
        published=True,
        issuer_user_id=issuer_user_id,
        issued_at=utcnow(),
        storage_token=token,
    ).insert()

    ledger.receipt_id = receipt_id
    await ledger.save()

    snapshot = _serialize_receipt(row)
    await PaymentReceiptVersion(
        tenant_id=tx.tenant_id,
        receipt_id=receipt_id,
        version=1,
        snapshot=snapshot,
    ).insert()
    await PaymentReceiptDocumentHistory(
        tenant_id=tx.tenant_id,
        receipt_id=receipt_id,
        action="issue",
        actor_id=issuer_user_id,
        note=f"linked_tx={tx.transaction_id}",
    ).insert()
    try:
        from app.modules.accounts_finance.finance_notify import enqueue_receipt_issued

        await enqueue_receipt_issued(tx.tenant_id, tx.student_user_id, receipt_id)
    except Exception:
        pass
    return row


async def get_receipt(scope: AccessScope, receipt_id: str) -> dict[str, Any]:
    authorize_finance_receipt_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    row = await PaymentReceipt.find_one(Eq(PaymentReceipt.tenant_id, tenant_id), Eq(PaymentReceipt.receipt_id, receipt_id))
    if row is None:
        raise AppError(code="NOT_FOUND", message="Receipt not found", status_code=404)
    student = await User.get(row.student_user_id)
    tenant = await Tenant.get(tenant_id)
    return _serialize_receipt(row, student, tenant)


async def get_receipt_by_number(scope: AccessScope, receipt_number: str) -> dict[str, Any]:
    authorize_finance_receipt_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    row = await PaymentReceipt.find_one(
        Eq(PaymentReceipt.tenant_id, tenant_id),
        Eq(PaymentReceipt.receipt_number, receipt_number),
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Receipt not found", status_code=404)
    student = await User.get(row.student_user_id)
    tenant = await Tenant.get(tenant_id)
    return _serialize_receipt(row, student, tenant)


async def search_receipts(
    scope: AccessScope,
    pagination: Pagination,
    *,
    student_user_id: str | None = None,
    transaction_id: str | None = None,
    academic_year_label: str | None = None,
    payment_mode: str | None = None,
    receipt_status: str | None = None,
    issued_from: date | None = None,
    issued_to: date | None = None,
) -> Page[dict[str, Any]]:
    authorize_finance_receipt_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query: dict[str, Any] = {"tenant_id": tenant_id}
    if student_user_id:
        from app.common.ids import to_object_id

        query["student_user_id"] = to_object_id(student_user_id, "student_user_id")
    if transaction_id:
        query["transaction_id"] = transaction_id
    if academic_year_label:
        query["academic_year_label"] = academic_year_label
    if payment_mode:
        query["payment_mode"] = payment_mode
    if receipt_status:
        query["receipt_status"] = receipt_status
    if issued_from or issued_to:
        from datetime import datetime

        issued: dict[str, Any] = {}
        if issued_from:
            issued["$gte"] = datetime.combine(issued_from, datetime.min.time())
        if issued_to:
            issued["$lte"] = datetime.combine(issued_to, datetime.max.time())
        query["issued_at"] = issued

    total = await PaymentReceipt.find(query).count()
    rows = (
        await PaymentReceipt.find(query)
        .sort("-issued_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    tenant = await Tenant.get(tenant_id)
    items = []
    for row in rows:
        student = await User.get(row.student_user_id)
        items.append(_serialize_receipt(row, student, tenant))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def generate_receipt_for_transaction(scope: AccessScope, transaction_id: str) -> dict[str, Any]:
    authorize_finance_receipt_issue(scope)
    tenant_id = require_finance_tenant_scope(scope)
    tx = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.transaction_id, transaction_id),
    )
    if tx is None:
        raise AppError(code="NOT_FOUND", message="Payment transaction not found", status_code=404)
    row = await issue_receipt_from_payment(tx, issuer_user_id=scope.user_id)
    if row is None:
        raise AppError(
            code="NOT_ELIGIBLE",
            message="Receipt requires a verified, ledger-posted payment",
            status_code=409,
        )
    student = await User.get(row.student_user_id)
    tenant = await Tenant.get(tenant_id)
    return _serialize_receipt(row, student, tenant)


async def cancel_receipt(scope: AccessScope, receipt_id: str, reason: str) -> dict[str, Any]:
    authorize_finance_receipt_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    row = await PaymentReceipt.find_one(Eq(PaymentReceipt.tenant_id, tenant_id), Eq(PaymentReceipt.receipt_id, receipt_id))
    if row is None:
        raise AppError(code="NOT_FOUND", message="Receipt not found", status_code=404)
    if row.receipt_status == ReceiptStatus.CANCELLED.value:
        raise AppError(code="CONFLICT", message="Receipt already cancelled", status_code=409)
    row.receipt_status = ReceiptStatus.CANCELLED.value
    row.published = False
    row.updated_at = utcnow()
    await row.save()
    cancel_id = f"rcn_{uuid4().hex[:12]}"
    await PaymentReceiptCancellation(
        tenant_id=tenant_id,
        cancellation_id=cancel_id,
        receipt_id=receipt_id,
        reason=reason,
        actor_id=scope.user_id,
    ).insert()
    await PaymentReceiptDocumentHistory(
        tenant_id=tenant_id,
        receipt_id=receipt_id,
        action="cancel",
        actor_id=scope.user_id,
        note=reason,
    ).insert()
    student = await User.get(row.student_user_id)
    tenant = await Tenant.get(tenant_id)
    return _serialize_receipt(row, student, tenant)


async def reissue_receipt(scope: AccessScope, receipt_id: str, reason: str) -> dict[str, Any]:
    authorize_finance_receipt_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    old = await PaymentReceipt.find_one(Eq(PaymentReceipt.tenant_id, tenant_id), Eq(PaymentReceipt.receipt_id, receipt_id))
    if old is None:
        raise AppError(code="NOT_FOUND", message="Receipt not found", status_code=404)
    if old.receipt_status not in (ReceiptStatus.ISSUED.value, ReceiptStatus.CANCELLED.value):
        raise AppError(code="CONFLICT", message="Receipt cannot be reissued", status_code=409)

    tx = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.transaction_id, old.transaction_id),
    )
    if tx is None or tx.status != PaymentTransactionStatus.SUCCESS:
        raise AppError(code="CONFLICT", message="Underlying payment is not successful", status_code=409)

    old.receipt_status = ReceiptStatus.SUPERSEDED.value
    old.published = False
    old.updated_at = utcnow()

    fiscal_year = old.academic_year_label or str(utcnow().year)
    new_receipt_id = f"rcpt_{uuid4().hex[:16]}"
    new_number = await _next_receipt_number(tenant_id, fiscal_year)
    token = uuid4().hex
    replacement = await PaymentReceipt(
        tenant_id=tenant_id,
        student_user_id=old.student_user_id,
        receipt_id=new_receipt_id,
        receipt_number=new_number,
        transaction_id=old.transaction_id,
        invoice_id=old.invoice_id,
        demand_id=old.demand_id,
        amount=old.amount,
        payment_mode=old.payment_mode,
        receipt_type=old.receipt_type,
        remaining_balance=old.remaining_balance,
        fee_breakdown=list(old.fee_breakdown),
        academic_year_label=old.academic_year_label,
        semester_label=old.semester_label,
        receipt_status=ReceiptStatus.REISSUED.value,
        published=True,
        issuer_user_id=scope.user_id,
        issued_at=utcnow(),
        storage_token=token,
    ).insert()
    old.superseded_by = new_receipt_id
    await old.save()

    await PaymentReceiptDocumentHistory(
        tenant_id=tenant_id,
        receipt_id=receipt_id,
        action="reissue",
        actor_id=scope.user_id,
        note=f"replacement={new_receipt_id}; {reason}",
    ).insert()
    student = await User.get(replacement.student_user_id)
    tenant = await Tenant.get(tenant_id)
    return _serialize_receipt(replacement, student, tenant)


async def daily_receipt_register(scope: AccessScope, day: date) -> dict[str, Any]:
    authorize_finance_receipt_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    from datetime import datetime

    start = datetime.combine(day, datetime.min.time())
    end = datetime.combine(day, datetime.max.time())
    rows = await PaymentReceipt.find(
        {
            "tenant_id": tenant_id,
            "issued_at": {"$gte": start, "$lte": end},
            "receipt_status": {"$in": [ReceiptStatus.ISSUED.value, ReceiptStatus.REISSUED.value]},
        }
    ).to_list()
    total = round_money(sum(r.amount for r in rows))
    by_mode: dict[str, float] = {}
    for r in rows:
        by_mode[r.payment_mode or "unknown"] = round_money(by_mode.get(r.payment_mode or "unknown", 0) + r.amount)
    return {"date": day.isoformat(), "count": len(rows), "total_amount": total, "by_payment_mode": by_mode}