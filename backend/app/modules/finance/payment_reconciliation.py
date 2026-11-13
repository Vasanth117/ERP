"""Post-payment ledger and demand updates (idempotent)."""

from uuid import uuid4

from app.common.time import utcnow
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import (
    PaymentReceipt,
    PaymentTransaction,
    StudentFeeDemand,
    StudentFinancialLedgerEntry,
)


async def reconcile_successful_payment(tx: PaymentTransaction) -> PaymentTransaction:
    if tx.status != PaymentTransactionStatus.SUCCESS or not tx.webhook_verified:
        return tx
    existing_receipt = await PaymentReceipt.find_one({"tenant_id": tx.tenant_id, "transaction_id": tx.transaction_id})
    if existing_receipt is not None:
        return tx
    demand: StudentFeeDemand | None = None
    if tx.demand_id:
        demand = await StudentFeeDemand.find_one({"tenant_id": tx.tenant_id, "demand_id": tx.demand_id})
        if demand is not None and demand.status != FeeDemandStatus.PAID:
            demand.status = FeeDemandStatus.PAID
            await demand.save()
    last = (
        await StudentFinancialLedgerEntry.find(
            {"tenant_id": tx.tenant_id, "student_user_id": tx.student_user_id}
        )
        .sort("-posted_at")
        .limit(1)
        .to_list()
    )
    balance = last[0].balance_after if last else 0.0
    balance_after = balance - tx.amount
    await StudentFinancialLedgerEntry(
        tenant_id=tx.tenant_id,
        student_user_id=tx.student_user_id,
        entry_id=f"led_{uuid4().hex}",
        entry_type="payment",
        description=f"Fee payment {tx.transaction_id}",
        debit=0,
        credit=tx.amount,
        balance_after=balance_after,
        reference_id=tx.transaction_id,
        posted_at=utcnow(),
    ).insert()
    token = uuid4().hex
    await PaymentReceipt(
        tenant_id=tx.tenant_id,
        student_user_id=tx.student_user_id,
        receipt_id=f"rcpt_{uuid4().hex}",
        transaction_id=tx.transaction_id,
        amount=tx.amount,
        issued_at=utcnow(),
        storage_token=token,
    ).insert()
    return tx
