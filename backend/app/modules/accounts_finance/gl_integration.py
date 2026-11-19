"""Mirror student sub-ledger events to institutional GL via mapping rules."""

from app.modules.accounts_finance.phase4_enums import LedgerEntryType
from app.modules.accounts_finance.phase9_enums import MappingEventType
from app.modules.finance.finance_models import StudentFinancialLedgerEntry

ENTRY_TO_EVENT: dict[str, str] = {
    LedgerEntryType.FEE_INVOICE.value: MappingEventType.FEE_INVOICE.value,
    LedgerEntryType.VERIFIED_PAYMENT.value: MappingEventType.VERIFIED_PAYMENT.value,
    "payment": MappingEventType.VERIFIED_PAYMENT.value,
    LedgerEntryType.SCHOLARSHIP_CREDIT.value: MappingEventType.SCHOLARSHIP_CREDIT.value,
    LedgerEntryType.CONCESSION_CREDIT.value: MappingEventType.CONCESSION_CREDIT.value,
    LedgerEntryType.FEE_WAIVER.value: MappingEventType.FEE_WAIVER.value,
    LedgerEntryType.LATE_FEE.value: MappingEventType.LATE_FEE.value,
    LedgerEntryType.LATE_FEE_WAIVER.value: MappingEventType.LATE_FEE_WAIVER.value,
    LedgerEntryType.REFUND.value: MappingEventType.REFUND.value,
    LedgerEntryType.PAYMENT_REVERSAL.value: MappingEventType.PAYMENT_REVERSAL.value,
    LedgerEntryType.ADJUSTMENT.value: MappingEventType.ADJUSTMENT.value,
}


async def mirror_student_ledger_to_gl(entry: StudentFinancialLedgerEntry) -> None:
    event = ENTRY_TO_EVENT.get(entry.entry_type)
    if event is None:
        return
    amount = entry.debit or entry.credit
    if amount <= 0:
        return
    from app.modules.accounts_finance.gl_posting_service import post_mapped_event

    journal_date = entry.transaction_date or entry.posted_at.date()
    source_ref = entry.posting_key or entry.reference_id or entry.entry_id
    await post_mapped_event(
        tenant_id=entry.tenant_id,
        event_type=event,
        source_reference=source_ref,
        amount=amount,
        journal_date=journal_date,
        narration=entry.narration or entry.description,
        posted_by=entry.posted_by,
        financial_period_code=None,
    )