"""Idempotent student financial ledger posting."""

from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase4_enums import LedgerEntryType
from app.modules.accounts_finance.phase4_models import (
    StudentFinancialAccount,
    StudentLedgerPostingHistory,
)
from app.modules.finance.finance_models import StudentFinancialLedgerEntry


async def _ensure_account(tenant_id, student_user_id) -> StudentFinancialAccount:
    acct = await StudentFinancialAccount.find_one(
        Eq(StudentFinancialAccount.tenant_id, tenant_id),
        Eq(StudentFinancialAccount.student_user_id, student_user_id),
    )
    if acct is not None:
        return acct
    acct = StudentFinancialAccount(tenant_id=tenant_id, student_user_id=student_user_id)
    await acct.insert()
    return acct


async def _last_balance(tenant_id, student_user_id: object) -> float:
    last = (
        await StudentFinancialLedgerEntry.find(
            {"tenant_id": tenant_id, "student_user_id": student_user_id}
        )
        .sort("-posted_at")
        .limit(1)
        .to_list()
    )
    return round_money(last[0].balance_after if last else 0.0)


async def post_ledger_entry(
    *,
    tenant_id,
    student_user_id,
    entry_type: str,
    description: str,
    debit: float = 0.0,
    credit: float = 0.0,
    source_reference: str,
    posting_key: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    invoice_id: str | None = None,
    payment_transaction_id: str | None = None,
    receipt_id: str | None = None,
    narration: str | None = None,
    posted_by=None,
    transaction_date=None,
) -> StudentFinancialLedgerEntry:
    debit = round_money(debit)
    credit = round_money(credit)
    key = posting_key or f"{entry_type}:{source_reference}"

    history = await StudentLedgerPostingHistory.find_one(
        Eq(StudentLedgerPostingHistory.tenant_id, tenant_id),
        Eq(StudentLedgerPostingHistory.posting_key, key),
    )
    if history is not None:
        existing = await StudentFinancialLedgerEntry.find_one(
            Eq(StudentFinancialLedgerEntry.tenant_id, tenant_id),
            Eq(StudentFinancialLedgerEntry.entry_id, history.ledger_entry_id),
        )
        if existing is not None:
            return existing

    balance = await _last_balance(tenant_id, student_user_id)
    balance_after = round_money(balance + debit - credit)
    entry_id = f"led_{uuid4().hex[:16]}"
    entry = await StudentFinancialLedgerEntry(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        entry_id=entry_id,
        entry_type=entry_type,
        description=description,
        debit=debit,
        credit=credit,
        balance_after=balance_after,
        reference_id=source_reference,
        posting_key=key,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        invoice_id=invoice_id,
        payment_transaction_id=payment_transaction_id,
        receipt_id=receipt_id,
        transaction_status="posted",
        narration=narration or description,
        posted_by=posted_by,
        transaction_date=transaction_date,
        posted_at=utcnow(),
    ).insert()

    await StudentLedgerPostingHistory(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        ledger_entry_id=entry_id,
        posting_key=key,
        entry_type=entry_type,
        source_reference=source_reference,
        actor_id=posted_by,
    ).insert()

    acct = await _ensure_account(tenant_id, student_user_id)
    acct.total_charges = round_money(acct.total_charges + debit)
    acct.total_credits = round_money(acct.total_credits + credit)
    acct.outstanding_balance = balance_after
    acct.updated_at = utcnow()
    await acct.save()
    from app.modules.accounts_finance.gl_integration import mirror_student_ledger_to_gl

    await mirror_student_ledger_to_gl(entry)
    return entry


async def post_verified_payment(
    *,
    tenant_id,
    student_user_id,
    transaction_id: str,
    amount: float,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    invoice_id: str | None = None,
    demand_id: str | None = None,
    posted_by=None,
) -> StudentFinancialLedgerEntry:
    legacy = await StudentFinancialLedgerEntry.find_one(
        Eq(StudentFinancialLedgerEntry.tenant_id, tenant_id),
        Eq(StudentFinancialLedgerEntry.reference_id, transaction_id),
    )
    if legacy is not None and legacy.entry_type in ("payment", LedgerEntryType.VERIFIED_PAYMENT.value, "verified_payment"):
        if not legacy.posting_key:
            legacy.posting_key = f"{LedgerEntryType.VERIFIED_PAYMENT.value}:{transaction_id}"
            legacy.entry_type = LedgerEntryType.VERIFIED_PAYMENT.value
            legacy.payment_transaction_id = transaction_id
            await legacy.save()
        return legacy

    desc = f"Verified payment {transaction_id}"
    if demand_id:
        desc = f"Fee payment {transaction_id} (demand {demand_id})"
    return await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        entry_type=LedgerEntryType.VERIFIED_PAYMENT.value,
        description=desc,
        debit=0,
        credit=amount,
        source_reference=transaction_id,
        posting_key=f"{LedgerEntryType.VERIFIED_PAYMENT.value}:{transaction_id}",
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        invoice_id=invoice_id,
        payment_transaction_id=transaction_id,
        posted_by=posted_by,
    )


async def post_fee_invoice(
    *,
    tenant_id,
    student_user_id,
    invoice_id: str,
    invoice_number: str,
    amount: float,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    posted_by=None,
) -> StudentFinancialLedgerEntry:
    return await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        entry_type=LedgerEntryType.FEE_INVOICE.value,
        description=f"Invoice {invoice_number}",
        debit=amount,
        credit=0,
        source_reference=invoice_id,
        posting_key=f"{LedgerEntryType.FEE_INVOICE.value}:{invoice_id}",
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        invoice_id=invoice_id,
        posted_by=posted_by,
    )