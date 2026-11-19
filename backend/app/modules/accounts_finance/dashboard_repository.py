"""Finance dashboard aggregations over authoritative finance collections."""

from collections import defaultdict
from datetime import date

from beanie.odm.operators.find.comparison import Eq, GTE, In

from app.modules.accounts_finance.dashboard_filters import FinanceDashboardContext
from app.modules.accounts_finance.dashboard_schemas import (
    AccountingOverviewSection,
    DashboardMetric,
    FinancialOverviewSection,
    InvoiceOverviewSection,
    MetricAvailability,
    PaymentOverviewSection,
    RefundOverviewSection,
    ScholarshipConcessionSection,
    StudentFeeOverviewSection,
)
from app.modules.accounts_finance.money import round_money
from app.modules.college_admin.finance_admin_models import FinancialPeriod, PaymentReconciliationRecord, RefundRequest, StudentFeeAssessment
from app.modules.college_admin.finance_ext_models import ExpenseStatus, InstitutionExpenseRecord, InstitutionVendorInvoice, InvoicePaymentStatus
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus, RefundStatus, ScholarshipApplicationStatus
from app.modules.finance.finance_models import (
    FeeConcession,
    FeeInstallmentSchedule,
    OfficialScholarshipApplication,
    PaymentTransaction,
    RefundRecord,
    StudentFeeDemand,
    StudentFeeInvoice,
    StudentFinancialLedgerEntry,
)
from app.modules.students.models import StudentProfile


def _metric(value: float | int, *, available: bool = True, reason: str | None = None) -> DashboardMetric:
    if isinstance(value, float):
        value = round_money(value)
    return DashboardMetric(value=value, availability=MetricAvailability(available=available, reason=reason))


async def _student_ids_for_scope(ctx: FinanceDashboardContext) -> set | None:
    if not ctx.department_id and not ctx.programme_code and not ctx.campus_id:
        return None
    query = StudentProfile.find(Eq(StudentProfile.tenant_id, ctx.tenant_id))
    if ctx.programme_code:
        query = query.find(Eq(StudentProfile.programme_code, ctx.programme_code))
    if ctx.department_id:
        query = query.find(Eq(StudentProfile.department_id, ctx.department_id))
    profiles = await query.to_list()
    if not profiles:
        return set()
    return {p.user_id for p in profiles}


def _matches_student(scope_ids: set | None, student_id) -> bool:
    if scope_ids is None:
        return True
    return student_id in scope_ids


def _in_date_range(created_at, ctx: FinanceDashboardContext) -> bool:
    if created_at.tzinfo is None:
        if ctx.date_from and ctx.date_from.tzinfo:
            from datetime import timezone

            created_at = created_at.replace(tzinfo=timezone.utc)
    if ctx.date_from and created_at < ctx.date_from:
        return False
    if ctx.date_to and created_at > ctx.date_to:
        return False
    return True


def _demand_matches(ctx: FinanceDashboardContext, demand: StudentFeeDemand) -> bool:
    if ctx.academic_year_label and demand.academic_year_label != ctx.academic_year_label:
        return False
    if ctx.semester_label and demand.semester_label != ctx.semester_label:
        return False
    return True


def _verified_payment(tx: PaymentTransaction) -> bool:
    if tx.status != PaymentTransactionStatus.SUCCESS:
        return False
    if tx.payment_mode == "offline":
        return True
    return tx.webhook_verified


async def build_financial_overview(ctx: FinanceDashboardContext) -> FinancialOverviewSection:
    scope_ids = await _student_ids_for_scope(ctx)
    assessments = await StudentFeeAssessment.find(Eq(StudentFeeAssessment.tenant_id, ctx.tenant_id)).to_list()
    total_assessed = 0.0
    for row in assessments:
        if not _matches_student(scope_ids, row.student_user_id):
            continue
        if ctx.academic_year_label and row.academic_year_label != ctx.academic_year_label:
            continue
        if ctx.semester_label and row.semester_label != ctx.semester_label:
            continue
        total_assessed += row.assessed_amount

    invoices = await StudentFeeInvoice.find(Eq(StudentFeeInvoice.tenant_id, ctx.tenant_id)).to_list()
    invoice_count = 0
    billed = 0.0
    for inv in invoices:
        if not _matches_student(scope_ids, inv.student_user_id):
            continue
        invoice_count += 1
        billed += inv.amount

    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, ctx.tenant_id)).to_list()
    outstanding = 0.0
    overdue = 0.0
    upcoming = 0
    for d in demands:
        if not _matches_student(scope_ids, d.student_user_id):
            continue
        if not _demand_matches(ctx, d):
            continue
        if d.status in (FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE):
            outstanding += d.amount
        if d.status == FeeDemandStatus.OVERDUE:
            overdue += d.amount
        if d.status == FeeDemandStatus.OPEN and d.due_date >= date.today():
            upcoming += 1

    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, ctx.tenant_id)).to_list()
    verified_sum = 0.0
    pending_count = 0
    failed_count = 0
    reversed_count = 0
    for tx in txs:
        if not _matches_student(scope_ids, tx.student_user_id):
            continue
        if not _in_date_range(tx.created_at, ctx):
            continue
        if ctx.payment_method and tx.payment_mode != ctx.payment_method:
            continue
        if ctx.payment_status and tx.status.value != ctx.payment_status:
            continue
        if _verified_payment(tx):
            verified_sum += tx.amount
        elif tx.status in (PaymentTransactionStatus.PENDING, PaymentTransactionStatus.INITIATED):
            pending_count += 1
        elif tx.status == PaymentTransactionStatus.FAILED:
            failed_count += 1
        elif tx.status == PaymentTransactionStatus.REFUNDED:
            reversed_count += 1

    refunds = await RefundRecord.find(Eq(RefundRecord.tenant_id, ctx.tenant_id)).to_list()
    refund_initiated = sum(1 for r in refunds if r.status == RefundStatus.REQUESTED)
    refund_completed = sum(1 for r in refunds if r.status == RefundStatus.PROCESSED)

    scholarships = await OfficialScholarshipApplication.find(Eq(OfficialScholarshipApplication.tenant_id, ctx.tenant_id)).to_list()
    scholarship_awards = sum(1 for s in scholarships if s.status == ScholarshipApplicationStatus.APPROVED)

    concessions = await FeeConcession.find(Eq(FeeConcession.tenant_id, ctx.tenant_id)).to_list()
    concession_total = sum(c.amount for c in concessions if c.published)

    net_collection = verified_sum
    collection_pct = round_money((verified_sum / billed * 100) if billed > 0 else 0.0)

    return FinancialOverviewSection(
        total_fees_assessed=_metric(total_assessed),
        total_invoices_generated=_metric(invoice_count),
        total_billed_amount=_metric(billed),
        total_verified_collections=_metric(verified_sum),
        total_outstanding_amount=_metric(outstanding),
        total_overdue_amount=_metric(overdue),
        total_pending_payments=_metric(pending_count),
        total_failed_payments=_metric(failed_count),
        total_reversed_payments=_metric(reversed_count),
        total_refunds_initiated=_metric(refund_initiated),
        total_refunds_completed=_metric(refund_completed),
        total_scholarship_awards=_metric(scholarship_awards),
        total_concessions_and_waivers=_metric(concession_total),
        net_fee_collection=_metric(net_collection),
        collection_percentage=_metric(collection_pct),
    )


async def build_student_fee_overview(ctx: FinanceDashboardContext) -> StudentFeeOverviewSection:
    scope_ids = await _student_ids_for_scope(ctx)
    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, ctx.tenant_id)).to_list()
    by_student: dict = defaultdict(list)
    for d in demands:
        if not _matches_student(scope_ids, d.student_user_id):
            continue
        if not _demand_matches(ctx, d):
            continue
        by_student[d.student_user_id].append(d)

    fully_paid = partial = outstanding = overdue = 0
    for _, rows in by_student.items():
        statuses = {r.status for r in rows}
        if statuses == {FeeDemandStatus.PAID}:
            fully_paid += 1
        elif FeeDemandStatus.PARTIALLY_PAID in statuses:
            partial += 1
        if any(r.status in (FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID) for r in rows):
            outstanding += 1
        if FeeDemandStatus.OVERDUE in statuses:
            overdue += 1

    scholarships = await OfficialScholarshipApplication.find(Eq(OfficialScholarshipApplication.tenant_id, ctx.tenant_id)).to_list()
    students_scholarship = len({s.student_user_id for s in scholarships if s.status == ScholarshipApplicationStatus.APPROVED})

    concessions = await FeeConcession.find(Eq(FeeConcession.tenant_id, ctx.tenant_id)).to_list()
    students_concession = len({c.student_user_id for c in concessions if c.published})

    installments = await FeeInstallmentSchedule.find(Eq(FeeInstallmentSchedule.tenant_id, ctx.tenant_id)).to_list()
    students_installment = len({i.student_user_id for i in installments if i.published})

    pending_offline = await PaymentTransaction.find(
        Eq(PaymentTransaction.tenant_id, ctx.tenant_id),
        Eq(PaymentTransaction.status, PaymentTransactionStatus.PENDING),
    ).to_list()
    arrangement_students = len({t.student_user_id for t in pending_offline if t.payment_mode == "offline"})

    return StudentFeeOverviewSection(
        students_with_obligations=_metric(len(by_student)),
        students_fully_paid=_metric(fully_paid),
        students_partially_paid=_metric(partial),
        students_outstanding=_metric(outstanding),
        students_overdue_invoices=_metric(overdue),
        students_scholarships=_metric(students_scholarship),
        students_concessions=_metric(students_concession),
        students_installment_plans=_metric(students_installment),
        students_payment_arrangements=_metric(arrangement_students),
    )


async def build_payment_overview(ctx: FinanceDashboardContext) -> PaymentOverviewSection:
    scope_ids = await _student_ids_for_scope(ctx)
    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, ctx.tenant_id)).to_list()
    online = offline = verified = pending_verify = failed = 0
    gateway: dict[str, float] = defaultdict(float)
    daily: dict[str, float] = defaultdict(float)
    method_summary: dict[str, float] = defaultdict(float)
    ref_counts: dict[str, int] = defaultdict(int)

    for tx in txs:
        if not _matches_student(scope_ids, tx.student_user_id):
            continue
        if not _in_date_range(tx.created_at, ctx):
            continue
        if ctx.payment_method and tx.payment_mode != ctx.payment_method:
            continue
        if ctx.payment_status and tx.status.value != ctx.payment_status:
            continue
        if tx.payment_mode == "online":
            online += 1
        else:
            offline += 1
        if _verified_payment(tx):
            verified += 1
            gateway[tx.gateway] += tx.amount
            day_key = tx.created_at.date().isoformat()
            daily[day_key] += tx.amount
            method_summary[tx.payment_mode] += tx.amount
        elif tx.status == PaymentTransactionStatus.SUCCESS and not tx.webhook_verified:
            pending_verify += 1
        elif tx.status == PaymentTransactionStatus.FAILED:
            failed += 1
        if tx.gateway_reference:
            ref_counts[tx.gateway_reference] += 1

    suspicious = sum(1 for c in ref_counts.values() if c > 1)
    recon_pending = await PaymentReconciliationRecord.find(
        Eq(PaymentReconciliationRecord.tenant_id, ctx.tenant_id),
        Eq(PaymentReconciliationRecord.reconciled, False),
    ).count()

    daily_list = [{"date": k, "amount": round_money(v)} for k, v in sorted(daily.items())]
    return PaymentOverviewSection(
        online_payments=_metric(online),
        offline_payments=_metric(offline),
        verified_transactions=_metric(verified),
        pending_verification=_metric(pending_verify),
        failed_transactions=_metric(failed),
        suspicious_duplicates=_metric(suspicious),
        gateway_collections={k: round_money(v) for k, v in gateway.items()},
        daily_collections=daily_list,
        payment_method_summary={k: round_money(v) for k, v in method_summary.items()},
        reconciliation_pending=_metric(recon_pending),
    )


async def build_invoice_overview(ctx: FinanceDashboardContext) -> InvoiceOverviewSection:
    scope_ids = await _student_ids_for_scope(ctx)
    invoices = await StudentFeeInvoice.find(Eq(StudentFeeInvoice.tenant_id, ctx.tenant_id)).to_list()
    demands = {d.demand_id: d for d in await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, ctx.tenant_id)).to_list()}

    draft = issued = partial = paid = overdue = cancelled = 0
    for inv in invoices:
        if not _matches_student(scope_ids, inv.student_user_id):
            continue
        if not inv.published:
            draft += 1
            continue
        issued += 1
        demand = demands.get(inv.demand_id or "")
        if demand is None:
            continue
        if demand.status == FeeDemandStatus.PARTIALLY_PAID:
            partial += 1
        elif demand.status == FeeDemandStatus.PAID:
            paid += 1
        elif demand.status == FeeDemandStatus.OVERDUE:
            overdue += 1
        elif demand.status == FeeDemandStatus.WAIVED:
            cancelled += 1

    adjustments = await StudentFinancialLedgerEntry.find(Eq(StudentFinancialLedgerEntry.tenant_id, ctx.tenant_id)).to_list()
    adj_count = sum(1 for e in adjustments if e.entry_type in ("credit_note", "debit_note", "adjustment"))

    upcoming = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, ctx.tenant_id),
        Eq(StudentFeeDemand.status, FeeDemandStatus.OPEN),
        GTE(StudentFeeDemand.due_date, date.today()),
    ).count()

    return InvoiceOverviewSection(
        draft_invoices=_metric(draft),
        issued_invoices=_metric(issued),
        partially_paid_invoices=_metric(partial),
        fully_paid_invoices=_metric(paid),
        overdue_invoices=_metric(overdue),
        cancelled_invoices=_metric(
            cancelled,
            available=cancelled > 0 or True,
            reason=None if cancelled or True else "No cancelled invoice status; derived from waived demands",
        ),
        credit_debit_adjustments=_metric(adj_count),
        upcoming_fee_demands=_metric(upcoming),
    )


async def build_scholarship_section(ctx: FinanceDashboardContext) -> ScholarshipConcessionSection:
    apps = await OfficialScholarshipApplication.find(Eq(OfficialScholarshipApplication.tenant_id, ctx.tenant_id)).to_list()
    awaiting = sum(1 for a in apps if a.status in (ScholarshipApplicationStatus.SUBMITTED, ScholarshipApplicationStatus.IN_REVIEW))
    approved = sum(1 for a in apps if a.status == ScholarshipApplicationStatus.APPROVED)
    rejected = sum(1 for a in apps if a.status == ScholarshipApplicationStatus.REJECTED)

    concessions = await FeeConcession.find(Eq(FeeConcession.tenant_id, ctx.tenant_id)).to_list()
    active = sum(1 for c in concessions if c.published)
    pending_waiver = sum(1 for c in concessions if not c.published)

    aid_total = sum(c.amount for c in concessions if c.published)
    return ScholarshipConcessionSection(
        applications_awaiting_review=_metric(awaiting),
        approved_scholarships=_metric(approved),
        rejected_applications=_metric(rejected),
        active_concessions=_metric(active),
        pending_waiver_approvals=_metric(pending_waiver),
        total_approved_financial_aid=_metric(aid_total),
        aid_utilization_amount=_metric(aid_total),
    )


async def build_refund_section(ctx: FinanceDashboardContext) -> RefundOverviewSection:
    records = await RefundRecord.find(Eq(RefundRecord.tenant_id, ctx.tenant_id)).to_list()
    requests = await RefundRequest.find(Eq(RefundRequest.tenant_id, ctx.tenant_id)).to_list()
    return RefundOverviewSection(
        refund_requests=_metric(len(requests)),
        pending_approval=_metric(sum(1 for r in records if r.status == RefundStatus.REQUESTED)),
        approved_refunds=_metric(sum(1 for r in records if r.status == RefundStatus.APPROVED)),
        processing_refunds=_metric(sum(1 for r in records if r.status == RefundStatus.APPROVED and r.updated_at)),
        completed_refunds=_metric(sum(1 for r in records if r.status == RefundStatus.PROCESSED)),
        failed_refunds=_metric(sum(1 for r in records if r.status == RefundStatus.REJECTED)),
        reversal_transactions=_metric(
            await PaymentTransaction.find(
                Eq(PaymentTransaction.tenant_id, ctx.tenant_id),
                Eq(PaymentTransaction.status, PaymentTransactionStatus.REFUNDED),
            ).count()
        ),
    )


async def build_accounting_section(ctx: FinanceDashboardContext) -> AccountingOverviewSection:
    expenses = await InstitutionExpenseRecord.find(Eq(InstitutionExpenseRecord.tenant_id, ctx.tenant_id)).to_list()
    total_expenses = sum(e.amount for e in expenses if e.status in (ExpenseStatus.APPROVED, ExpenseStatus.PAID))
    open_periods = await FinancialPeriod.find(Eq(FinancialPeriod.tenant_id, ctx.tenant_id)).to_list()
    period_status = open_periods[0].status.value if open_periods else "unknown"

    payables = await InstitutionVendorInvoice.find(
        Eq(InstitutionVendorInvoice.tenant_id, ctx.tenant_id),
        In(InstitutionVendorInvoice.payment_status, [InvoicePaymentStatus.PENDING, InvoicePaymentStatus.PARTIAL]),
    ).count()

    receivables = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, ctx.tenant_id),
        In(StudentFeeDemand.status, [FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE]),
    ).to_list()
    receivable_amount = sum(d.amount for d in receivables)

    reconciliation_exceptions = await PaymentReconciliationRecord.find(
        Eq(PaymentReconciliationRecord.tenant_id, ctx.tenant_id),
        Eq(PaymentReconciliationRecord.reconciled, False),
    ).count()

    return AccountingOverviewSection(
        total_income=_metric(
            0,
            available=False,
            reason="General ledger income not configured; use verified student collections in financial overview",
        ),
        total_expenses=_metric(total_expenses, available=bool(expenses)),
        outstanding_receivables=_metric(receivable_amount),
        payables=_metric(payables if payables else 0, available=payables > 0, reason="Vendor payables from finance extensions when invoices exist"),
        bank_cash_balances=_metric(0, available=False, reason="No general ledger cash/bank module in Phase 1"),
        journal_entries_pending=_metric(
            0,
            available=False,
            reason="Use General Ledger journals API for institution GL; student sub-ledger is separate",
        ),
        financial_period_status=_metric(0, available=bool(open_periods), reason=None if open_periods else "No financial periods configured"),
        reconciliation_exceptions=_metric(reconciliation_exceptions),
    )