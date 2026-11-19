"""Post-payment ledger and demand updates (idempotent)."""

from beanie.odm.operators.find.comparison import Eq

from app.modules.accounts_finance.ledger_posting_service import post_verified_payment
from app.modules.accounts_finance.money import round_money
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import (
    PaymentReceipt,
    PaymentTransaction,
    StudentFeeDemand,
    StudentFeeInvoice,
)


async def _verified_paid_on_demand(tenant_id, demand_id: str) -> float:
    txs = await PaymentTransaction.find(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.demand_id, demand_id),
        Eq(PaymentTransaction.status, PaymentTransactionStatus.SUCCESS),
    ).to_list()
    total = 0.0
    for row in txs:
        if row.payment_mode == "offline" or row.webhook_verified:
            total += row.amount
    return round_money(total)


async def reconcile_successful_payment(tx: PaymentTransaction) -> PaymentTransaction:
    if tx.status != PaymentTransactionStatus.SUCCESS:
        return tx
    if tx.payment_mode != "offline" and not tx.webhook_verified:
        return tx

    existing_receipt = await PaymentReceipt.find_one(
        Eq(PaymentReceipt.tenant_id, tx.tenant_id),
        Eq(PaymentReceipt.transaction_id, tx.transaction_id),
    )

    demand: StudentFeeDemand | None = None
    if tx.demand_id:
        demand = await StudentFeeDemand.find_one(
            Eq(StudentFeeDemand.tenant_id, tx.tenant_id),
            Eq(StudentFeeDemand.demand_id, tx.demand_id),
        )
        if demand is not None:
            paid = await _verified_paid_on_demand(tx.tenant_id, tx.demand_id)
            due = round_money(demand.amount + demand.late_fee)
            if paid >= due:
                demand.status = FeeDemandStatus.PAID
            elif paid > 0:
                demand.status = FeeDemandStatus.PARTIALLY_PAID
            await demand.save()

    invoice: StudentFeeInvoice | None = None
    if tx.demand_id:
        invoice = await StudentFeeInvoice.find_one(
            Eq(StudentFeeInvoice.tenant_id, tx.tenant_id),
            Eq(StudentFeeInvoice.demand_id, tx.demand_id),
        )

    await post_verified_payment(
        tenant_id=tx.tenant_id,
        student_user_id=tx.student_user_id,
        transaction_id=tx.transaction_id,
        amount=tx.amount,
        academic_year_label=demand.academic_year_label if demand else None,
        semester_label=demand.semester_label if demand else None,
        invoice_id=invoice.invoice_id if invoice else None,
        demand_id=tx.demand_id,
    )

    if existing_receipt is None:
        from app.modules.accounts_finance.receipt_service import issue_receipt_from_payment

        await issue_receipt_from_payment(tx)

    try:
        from app.modules.accounts_finance.installment_service import apply_payment_to_installments

        await apply_payment_to_installments(
            tx.tenant_id,
            student_user_id=tx.student_user_id,
            transaction_id=tx.transaction_id,
            amount=tx.amount,
            demand_id=tx.demand_id,
        )
    except Exception:
        pass
    try:
        from app.modules.library.fine_integration import on_demand_paid

        await on_demand_paid(tx.tenant_id, tx.demand_id, tx.transaction_id)
    except Exception:
        pass
    return tx