"""Post approved scholarships, concessions and waivers to ledger and invoices."""

from beanie.odm.operators.find.comparison import Eq

from app.modules.accounts_finance.ledger_posting_service import post_ledger_entry
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase4_enums import LedgerEntryType
from app.modules.accounts_finance.phase5_models import FeeConcessionAdjustmentHistory
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand, StudentFeeInvoice


async def _sync_invoice_and_demand(tenant_id, invoice_id: str, credit_amount: float) -> None:
    invoice = await StudentFeeInvoice.find_one(
        Eq(StudentFeeInvoice.tenant_id, tenant_id),
        Eq(StudentFeeInvoice.invoice_id, invoice_id),
    )
    if invoice is None:
        return
    invoice.amount = max(0.0, round_money(invoice.amount - credit_amount))
    await invoice.save()
    if invoice.demand_id:
        demand = await StudentFeeDemand.find_one(
            Eq(StudentFeeDemand.tenant_id, tenant_id),
            Eq(StudentFeeDemand.demand_id, invoice.demand_id),
        )
        if demand:
            demand.amount = invoice.amount
            if invoice.amount <= 0:
                demand.status = FeeDemandStatus.WAIVED
            await demand.save()


async def post_scholarship_credit(
    *,
    tenant_id,
    student_user_id,
    amount: float,
    award_id: str,
    invoice_id: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    posted_by=None,
) -> str:
    amount = round_money(amount)
    entry = await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        entry_type=LedgerEntryType.SCHOLARSHIP_CREDIT.value,
        description=f"Scholarship award {award_id}",
        debit=0,
        credit=amount,
        source_reference=award_id,
        posting_key=f"scholarship:{award_id}",
        invoice_id=invoice_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        posted_by=posted_by,
        narration="Approved scholarship credit",
    )
    if invoice_id:
        await _sync_invoice_and_demand(tenant_id, invoice_id, amount)
    await FeeConcessionAdjustmentHistory(
        tenant_id=tenant_id,
        history_id=f"hist_{award_id}",
        student_user_id=student_user_id,
        source_type="scholarship",
        source_id=award_id,
        invoice_id=invoice_id,
        amount=amount,
        ledger_entry_id=entry.entry_id,
        actor_id=posted_by,
    ).insert()
    return entry.entry_id


async def post_concession_credit(
    *,
    tenant_id,
    student_user_id,
    amount: float,
    award_id: str,
    invoice_id: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    posted_by=None,
) -> str:
    amount = round_money(amount)
    entry = await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        entry_type=LedgerEntryType.CONCESSION_CREDIT.value,
        description=f"Fee concession {award_id}",
        debit=0,
        credit=amount,
        source_reference=award_id,
        posting_key=f"concession:{award_id}",
        invoice_id=invoice_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        posted_by=posted_by,
        narration="Approved concession credit",
    )
    if invoice_id:
        await _sync_invoice_and_demand(tenant_id, invoice_id, amount)
    await FeeConcessionAdjustmentHistory(
        tenant_id=tenant_id,
        history_id=f"hist_{award_id}",
        student_user_id=student_user_id,
        source_type="concession",
        source_id=award_id,
        invoice_id=invoice_id,
        amount=amount,
        ledger_entry_id=entry.entry_id,
        actor_id=posted_by,
    ).insert()
    return entry.entry_id


async def post_waiver_credit(
    *,
    tenant_id,
    student_user_id,
    amount: float,
    waiver_id: str,
    invoice_id: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    posted_by=None,
) -> str:
    amount = round_money(amount)
    entry = await post_ledger_entry(
        tenant_id=tenant_id,
        student_user_id=student_user_id,
        entry_type=LedgerEntryType.FEE_WAIVER.value,
        description=f"Fee waiver {waiver_id}",
        debit=0,
        credit=amount,
        source_reference=waiver_id,
        posting_key=f"waiver:{waiver_id}",
        invoice_id=invoice_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        posted_by=posted_by,
        narration="Approved fee waiver",
    )
    if invoice_id:
        await _sync_invoice_and_demand(tenant_id, invoice_id, amount)
    await FeeConcessionAdjustmentHistory(
        tenant_id=tenant_id,
        history_id=f"hist_{waiver_id}",
        student_user_id=student_user_id,
        source_type="waiver",
        source_id=waiver_id,
        invoice_id=invoice_id,
        amount=amount,
        ledger_entry_id=entry.entry_id,
        actor_id=posted_by,
    ).insert()
    return entry.entry_id