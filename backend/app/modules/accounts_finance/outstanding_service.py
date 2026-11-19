"""Outstanding dues dashboard, statements and ageing."""

from datetime import date, timedelta
from typing import Any

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.accounts_finance.late_fee_service import _active_policy, classify_ageing
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.payment_core import demand_outstanding, verified_payments_total
from app.modules.accounts_finance.phase4_models import StudentFinancialAccount
from app.modules.accounts_finance.phase5_models import StudentFeeConcessionAward, StudentFeeWaiver, StudentScholarshipAward
from app.modules.accounts_finance.phase6_enums import InstallmentStatus
from app.modules.accounts_finance.phase6_models import StudentInstallmentSchedule, StudentLateFeeTransaction, StudentLateFeeWaiver
from app.modules.accounts_finance.policy import authorize_finance_outstanding_read, require_finance_tenant_scope
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand, StudentFeeInvoice, StudentFinancialLedgerEntry


async def outstanding_dashboard(scope: AccessScope) -> dict[str, Any]:
    authorize_finance_outstanding_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    policy = await _active_policy(tenant_id, None)
    buckets = policy.ageing_buckets if policy else []

    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    today = date.today()
    total_outstanding = 0.0
    total_overdue = 0.0
    students_outstanding: set[str] = set()
    students_overdue: set[str] = set()
    upcoming_deadlines = 0
    overdue_installments = 0
    late_fees_applied = 0.0
    waiver_total = 0.0
    ageing_totals: dict[str, float] = {}

    for d in demands:
        if d.status in (FeeDemandStatus.PAID, FeeDemandStatus.WAIVED):
            continue
        outstanding = await demand_outstanding(tenant_id, d)
        if outstanding <= 0:
            continue
        total_outstanding = round_money(total_outstanding + outstanding)
        students_outstanding.add(str(d.student_user_id))
        overdue_days = max(0, (today - d.due_date).days) if d.due_date else 0
        bucket = classify_ageing(overdue_days, buckets)
        ageing_totals[bucket] = round_money(ageing_totals.get(bucket, 0) + outstanding)
        if d.due_date and d.due_date < today:
            total_overdue = round_money(total_overdue + outstanding)
            students_overdue.add(str(d.student_user_id))
        elif d.due_date and d.due_date <= today + timedelta(days=7):
            upcoming_deadlines += 1

    schedules = await StudentInstallmentSchedule.find({"tenant_id": tenant_id, "active": True}).to_list()
    for s in schedules:
        for inst in s.installments:
            if inst.get("status") == InstallmentStatus.OVERDUE.value:
                overdue_installments += 1

    ltx = await StudentLateFeeTransaction.find(Eq(StudentLateFeeTransaction.tenant_id, tenant_id)).to_list()
    late_fees_applied = round_money(sum(t.amount for t in ltx))
    waivers = await StudentLateFeeWaiver.find(Eq(StudentLateFeeWaiver.tenant_id, tenant_id)).to_list()
    waiver_total = round_money(sum(w.waived_amount for w in waivers))

    return {
        "total_outstanding_amount": total_outstanding,
        "total_overdue_amount": total_overdue,
        "students_with_outstanding": len(students_outstanding),
        "students_with_overdue": len(students_overdue),
        "upcoming_payment_deadlines": upcoming_deadlines,
        "overdue_installments": overdue_installments,
        "late_fees_applied": late_fees_applied,
        "late_fee_waivers": waiver_total,
        "ageing_breakdown": ageing_totals,
    }


async def student_outstanding_statement(scope: AccessScope, student_user_id: str) -> dict[str, Any]:
    authorize_finance_outstanding_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    sid = to_object_id(student_user_id, "student_user_id")

    account = await StudentFinancialAccount.find_one(
        Eq(StudentFinancialAccount.tenant_id, tenant_id),
        Eq(StudentFinancialAccount.student_user_id, sid),
    )
    ledger_balance = account.outstanding_balance if account else 0.0
    if not ledger_balance:
        last = (
            await StudentFinancialLedgerEntry.find({"tenant_id": tenant_id, "student_user_id": sid})
            .sort("-posted_at")
            .limit(1)
            .to_list()
        )
        ledger_balance = last[0].balance_after if last else 0.0

    invoices = await StudentFeeInvoice.find({"tenant_id": tenant_id, "student_user_id": sid}).to_list()
    original_invoice_total = round_money(sum(i.original_amount or i.amount for i in invoices))
    demands = await StudentFeeDemand.find({"tenant_id": tenant_id, "student_user_id": sid}).to_list()
    verified_payments = 0.0
    for d in demands:
        verified_payments += await verified_payments_total(tenant_id, d.demand_id)

    scholarships = await StudentScholarshipAward.find({"tenant_id": tenant_id, "student_user_id": sid}).to_list()
    scholarship_credits = round_money(sum(a.approved_amount for a in scholarships if a.status.value in ("active", "approved")))
    concessions = await StudentFeeConcessionAward.find({"tenant_id": tenant_id, "student_user_id": sid}).to_list()
    concession_credits = round_money(sum(c.approved_amount for c in concessions if c.status.value in ("active", "approved")))
    waivers = await StudentFeeWaiver.find({"tenant_id": tenant_id, "student_user_id": sid}).to_list()
    waiver_credits = round_money(sum(w.waived_amount for w in waivers if w.status == "approved"))

    remaining = max(
        0.0,
        round_money(original_invoice_total - verified_payments - scholarship_credits - concession_credits - waiver_credits),
    )

    invoice_balances = []
    for inv in invoices:
        paid = 0.0
        if inv.demand_id:
            paid = await verified_payments_total(tenant_id, inv.demand_id)
        invoice_balances.append(
            {
                "invoice_id": inv.invoice_id,
                "original_amount": inv.original_amount or inv.amount,
                "current_amount": inv.amount,
                "verified_payments": paid,
                "remaining": max(0.0, round_money(inv.amount - paid)),
            }
        )

    return {
        "student_user_id": student_user_id,
        "ledger_outstanding_balance": round_money(ledger_balance),
        "original_invoice_amount": original_invoice_total,
        "verified_payments": round_money(verified_payments),
        "scholarship_credits": scholarship_credits,
        "concession_credits": concession_credits,
        "waiver_credits": waiver_credits,
        "remaining_payable": remaining,
        "invoice_balances": invoice_balances,
    }


async def list_overdue_students(scope: AccessScope, pagination: Pagination) -> Page[dict[str, Any]]:
    authorize_finance_outstanding_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    today = date.today()
    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for d in demands:
        if d.status in (FeeDemandStatus.PAID, FeeDemandStatus.WAIVED):
            continue
        if not d.due_date or d.due_date >= today:
            continue
        outstanding = await demand_outstanding(tenant_id, d)
        if outstanding <= 0:
            continue
        sid = str(d.student_user_id)
        if sid in seen:
            continue
        seen.add(sid)
        rows.append(
            {
                "student_user_id": sid,
                "demand_id": d.demand_id,
                "outstanding": outstanding,
                "overdue_days": (today - d.due_date).days,
                "due_date": d.due_date.isoformat(),
            }
        )
    total = len(rows)
    page = rows[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=page, total=total, limit=pagination.limit, offset=pagination.offset)