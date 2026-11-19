"""Phase 8 report aggregations (authoritative finance collections only)."""

from collections import defaultdict
from datetime import date

from beanie.odm.operators.find.comparison import Eq, In

from app.modules.accounts_finance.dashboard_filters import FinanceDashboardContext, build_dashboard_context
from app.modules.accounts_finance.dashboard_repository import (
    _demand_matches,
    _in_date_range,
    _matches_student,
    _student_ids_for_scope,
    _verified_payment,
    build_accounting_section,
    build_financial_overview,
)
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase2_enums import StudentInvoiceStatus
from app.modules.accounts_finance.phase7_enums import RefundWorkflowStatus
from app.modules.accounts_finance.phase7_models import PaymentReconciliationException, StudentRefundRequest
from app.modules.college_admin.finance_admin_models import PaymentReconciliationRecord
from app.modules.college_admin.finance_ext_models import ExpenseStatus, InstitutionExpenseRecord
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus, RefundStatus, ScholarshipApplicationStatus
from app.modules.finance.finance_models import (
    FeeConcession,
    OfficialScholarshipApplication,
    PaymentTransaction,
    RefundRecord,
    StudentFeeDemand,
    StudentFeeInvoice,
    StudentFinancialLedgerEntry,
)
from app.modules.students.models import StudentProfile


def _ctx_from_filters(tenant_id, filters: dict) -> FinanceDashboardContext:
    return build_dashboard_context(
        tenant_id,
        academic_year_label=filters.get("academic_year_label"),
        semester_label=filters.get("semester_label"),
        programme_code=filters.get("programme_code"),
        department_id=filters.get("department_id"),
        campus_id=filters.get("campus_id"),
        date_from=filters.get("date_from"),
        date_to=filters.get("date_to"),
        payment_status=filters.get("payment_status"),
        payment_method=filters.get("payment_method"),
    )


async def workspace_net_position(tenant_id, filters: dict) -> dict:
    ctx = _ctx_from_filters(tenant_id, filters)
    financial = await build_financial_overview(ctx)
    accounting = await build_accounting_section(ctx)
    expenses = accounting.total_expenses.value if accounting.total_expenses.availability.available else 0.0
    collections = financial.total_verified_collections.value
    receivables = financial.total_outstanding_amount.value
    net = round_money(collections - expenses) if expenses else None
    return {
        "verified_student_collections": collections,
        "institutional_expenses": expenses,
        "outstanding_receivables": receivables,
        "net_operating_position": net,
        "general_ledger_available": False,
        "note": "Net position excludes GL; use verified collections minus approved institution expenses.",
    }


async def report_fee_collections(tenant_id, filters: dict, *, group_by: str = "day") -> list[dict]:
    ctx = _ctx_from_filters(tenant_id, filters)
    scope_ids = await _student_ids_for_scope(ctx)
    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).to_list()
    buckets: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for tx in txs:
        if not _matches_student(scope_ids, tx.student_user_id):
            continue
        if not _in_date_range(tx.created_at, ctx):
            continue
        if not _verified_payment(tx):
            continue
        if group_by == "payment_method":
            key = tx.payment_mode
        elif group_by == "gateway":
            key = tx.gateway or "unknown"
        elif group_by == "month":
            key = tx.created_at.strftime("%Y-%m")
        elif group_by == "academic_year":
            if tx.demand_id:
                demand = await StudentFeeDemand.find_one(
                    Eq(StudentFeeDemand.tenant_id, tenant_id),
                    Eq(StudentFeeDemand.demand_id, tx.demand_id),
                )
                key = demand.academic_year_label if demand else "unknown"
            else:
                key = "unknown"
        else:
            key = tx.created_at.date().isoformat()
        buckets[key] += tx.amount
        counts[key] += 1
    return [{"group_key": k, "amount": round_money(v), "transaction_count": counts[k]} for k, v in sorted(buckets.items())]


async def report_invoice_register(tenant_id, filters: dict) -> list[dict]:
    ctx = _ctx_from_filters(tenant_id, filters)
    scope_ids = await _student_ids_for_scope(ctx)
    invoices = await StudentFeeInvoice.find(Eq(StudentFeeInvoice.tenant_id, tenant_id)).to_list()
    rows: list[dict] = []
    status_filter = filters.get("invoice_status")
    for inv in invoices:
        if not _matches_student(scope_ids, inv.student_user_id):
            continue
        if ctx.academic_year_label and inv.academic_year_label != ctx.academic_year_label:
            continue
        if ctx.semester_label and inv.semester_label != ctx.semester_label:
            continue
        if status_filter and inv.invoice_status != status_filter:
            continue
        rows.append(
            {
                "invoice_id": inv.invoice_id,
                "invoice_number": inv.invoice_number,
                "student_user_id": str(inv.student_user_id),
                "amount": round_money(inv.amount),
                "status": inv.invoice_status,
                "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
                "due_date": inv.due_date.isoformat(),
                "academic_year_label": inv.academic_year_label,
                "semester_label": inv.semester_label,
            }
        )
    return rows


async def report_outstanding(tenant_id, filters: dict, *, group_by: str = "student") -> list[dict]:
    ctx = _ctx_from_filters(tenant_id, filters)
    scope_ids = await _student_ids_for_scope(ctx)
    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    buckets: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for d in demands:
        if not _matches_student(scope_ids, d.student_user_id):
            continue
        if not _demand_matches(ctx, d):
            continue
        if d.status not in (FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE):
            continue
        if group_by == "programme":
            profile = await StudentProfile.find_one(Eq(StudentProfile.user_id, d.student_user_id))
            key = profile.programme_code if profile else "unknown"
        elif group_by == "academic_year":
            key = d.academic_year_label or "unknown"
        else:
            key = str(d.student_user_id)
        buckets[key] += d.amount
        counts[key] += 1
    return [{"group_key": k, "outstanding": round_money(v), "obligation_count": counts[k]} for k, v in sorted(buckets.items(), key=lambda x: -x[1])]


async def report_payments(tenant_id, filters: dict) -> dict:
    ctx = _ctx_from_filters(tenant_id, filters)
    scope_ids = await _student_ids_for_scope(ctx)
    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).to_list()
    summary = {
        "online": 0,
        "offline": 0,
        "failed": 0,
        "pending": 0,
        "reversed": 0,
        "unreconciled_legacy": 0,
    }
    by_method: dict[str, float] = defaultdict(float)
    for tx in txs:
        if not _matches_student(scope_ids, tx.student_user_id):
            continue
        if not _in_date_range(tx.created_at, ctx):
            continue
        if tx.payment_mode == "online":
            summary["online"] += 1
        else:
            summary["offline"] += 1
        if tx.status == PaymentTransactionStatus.FAILED:
            summary["failed"] += 1
        elif tx.status in (PaymentTransactionStatus.PENDING, PaymentTransactionStatus.INITIATED):
            summary["pending"] += 1
        elif tx.status == PaymentTransactionStatus.REFUNDED:
            summary["reversed"] += 1
        if _verified_payment(tx):
            by_method[tx.payment_mode] += tx.amount
    summary["unreconciled_legacy"] = await PaymentReconciliationRecord.find(
        Eq(PaymentReconciliationRecord.tenant_id, tenant_id),
        Eq(PaymentReconciliationRecord.reconciled, False),
    ).count()
    return {"summary": summary, "verified_by_method": {k: round_money(v) for k, v in by_method.items()}}


async def report_scholarship_concession(tenant_id, filters: dict) -> dict:
    apps = await OfficialScholarshipApplication.find(Eq(OfficialScholarshipApplication.tenant_id, tenant_id)).to_list()
    concessions = await FeeConcession.find(Eq(FeeConcession.tenant_id, tenant_id)).to_list()
    return {
        "scholarship_pending": sum(1 for a in apps if a.status in (ScholarshipApplicationStatus.SUBMITTED, ScholarshipApplicationStatus.IN_REVIEW)),
        "scholarship_approved": sum(1 for a in apps if a.status == ScholarshipApplicationStatus.APPROVED),
        "scholarship_rejected": sum(1 for a in apps if a.status == ScholarshipApplicationStatus.REJECTED),
        "concessions_active": sum(1 for c in concessions if c.published),
        "concession_amount": round_money(sum(c.amount for c in concessions if c.published)),
    }


async def report_refund_reconciliation(tenant_id, filters: dict) -> dict:
    ctx = _ctx_from_filters(tenant_id, filters)
    records = await RefundRecord.find(Eq(RefundRecord.tenant_id, tenant_id)).to_list()
    phase7 = await StudentRefundRequest.find(Eq(StudentRefundRequest.tenant_id, tenant_id)).to_list()
    exceptions = await PaymentReconciliationException.find(Eq(PaymentReconciliationException.tenant_id, tenant_id)).to_list()
    return {
        "refund_requested": sum(1 for r in records if r.status == RefundStatus.REQUESTED),
        "refund_approved": sum(1 for r in records if r.status == RefundStatus.APPROVED),
        "refund_completed": sum(1 for r in records if r.status == RefundStatus.PROCESSED),
        "workflow_pending": sum(
            1
            for r in phase7
            if r.status not in (RefundWorkflowStatus.SUCCESSFUL, RefundWorkflowStatus.CANCELLED, RefundWorkflowStatus.FAILED)
        ),
        "reconciliation_exceptions_open": sum(1 for e in exceptions if not e.resolved),
        "filter_applied": bool(ctx.date_from or ctx.date_to),
    }


async def report_accounting_placeholders(tenant_id=None) -> dict:
    if tenant_id is None:
        return {
            "trial_balance": {"available": False, "reason": "Tenant context required"},
            "income_expense_statement": {"available": False, "reason": "Tenant context required"},
            "balance_sheet": {"available": False, "reason": "Tenant context required"},
            "journal_register": {"available": False, "reason": "Use /general-ledger/journals"},
            "bank_reconciliation_summary": {"available": False, "reason": "Use payment reconciliation reports"},
        }
    from beanie.odm.operators.find.comparison import Eq

    from app.modules.accounts_finance.phase9_models import GeneralLedgerEntry

    gl_count = await GeneralLedgerEntry.find(Eq(GeneralLedgerEntry.tenant_id, tenant_id)).count()
    has_gl = gl_count > 0
    return {
        "trial_balance": {"available": has_gl, "reason": None if has_gl else "No posted GL entries", "api": "/accounts-finance/general-ledger/reports/trial-balance"},
        "income_expense_statement": {"available": has_gl, "reason": None if has_gl else "No posted GL entries", "api": "/accounts-finance/general-ledger/reports/income-expenditure"},
        "balance_sheet": {"available": has_gl, "reason": "Requires opening balances for completeness", "api": "/accounts-finance/general-ledger/reports/balance-sheet"},
        "journal_register": {"available": has_gl, "reason": None if has_gl else "No journals", "api": "/accounts-finance/general-ledger/journals"},
        "bank_reconciliation_summary": {"available": False, "reason": "Use payment reconciliation reports"},
    }


async def report_analytics_trends(tenant_id, filters: dict) -> dict:
    ctx = _ctx_from_filters(tenant_id, filters)
    txs = await PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).to_list()
    monthly: dict[str, float] = defaultdict(float)
    for tx in txs:
        if not _in_date_range(tx.created_at, ctx):
            continue
        if _verified_payment(tx):
            monthly[tx.created_at.strftime("%Y-%m")] += tx.amount
    series = [{"month": k, "collections": round_money(v)} for k, v in sorted(monthly.items())]
    demands = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        In(StudentFeeDemand.status, [FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE]),
    ).to_list()
    outstanding_total = round_money(sum(d.amount for d in demands))
    expenses = await InstitutionExpenseRecord.find(Eq(InstitutionExpenseRecord.tenant_id, tenant_id)).to_list()
    expense_total = round_money(sum(e.amount for e in expenses if e.status in (ExpenseStatus.APPROVED, ExpenseStatus.PAID)))
    ledger_notes = await StudentFinancialLedgerEntry.find(Eq(StudentFinancialLedgerEntry.tenant_id, tenant_id)).count()
    return {
        "collection_trend": series,
        "outstanding_total": outstanding_total,
        "expense_total": expense_total,
        "ledger_entry_count": ledger_notes,
    }


async def report_invoice_summary_counts(tenant_id, filters: dict) -> dict:
    rows = await report_invoice_register(tenant_id, filters)
    counts = defaultdict(int)
    for row in rows:
        counts[row["status"]] += 1
    overdue = sum(1 for r in rows if r["status"] == StudentInvoiceStatus.OVERDUE.value)
    return {
        "total": len(rows),
        "by_status": dict(counts),
        "overdue_invoices": overdue,
        "partially_paid": counts.get(StudentInvoiceStatus.PARTIALLY_PAID.value, 0),
        "fully_paid": counts.get(StudentInvoiceStatus.PAID.value, 0),
        "cancelled": counts.get(StudentInvoiceStatus.CANCELLED.value, 0),
    }