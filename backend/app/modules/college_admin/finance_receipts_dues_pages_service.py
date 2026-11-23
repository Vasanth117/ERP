"""Receipt management and outstanding dues pages (CA 10)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase4_models import PaymentReceiptDocumentHistory
from app.modules.auth.models import User
from app.modules.college_admin.finance_overview_service import _verified_payment
from app.modules.college_admin.finance_receipts_page_shared import (
    current_month_start,
    format_count,
    format_inr,
    format_inr_compact,
    invoice_label_for_receipt,
    month_label,
    page_numbers,
    receipt_date_label,
    receipt_label,
    receipt_status,
    receipts_sub_nav,
    showing_slice,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FinanceAgingBucketItem,
    FinanceOutstandingDuesTableRow,
    FinanceReceiptTableRow,
    OutstandingDuesManagementPageRead,
    PoliciesPagination,
    ReceiptManagementPageRead,
    UserDashboardKpi,
)
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import (
    FeeInstallmentSchedule,
    PaymentReceipt,
    PaymentTransaction,
    StudentFeeDemand,
    StudentFeeInvoice,
)

_RECEIPT_PAGE_SIZE = 10
_DUES_PAGE_SIZE = 10


def _pagination(total: int, page: int, page_size: int) -> tuple[PoliciesPagination, int]:
    total_pages = math.ceil(total / page_size) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * page_size
    return (
        PoliciesPagination(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        start,
    )


def _receipt_in_month(receipt: PaymentReceipt, month_start: date, month_end: date) -> bool:
    local = receipt.issued_at
    if local.tzinfo:
        local = local.replace(tzinfo=None)
    day = local.date()
    return month_start <= day < month_end


def _month_end(month_start: date) -> date:
    if month_start.month == 12:
        return date(month_start.year + 1, 1, 1)
    return date(month_start.year, month_start.month + 1, 1)


async def get_receipt_management_page(scope: AccessScope, *, page: int = 1) -> ReceiptManagementPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    month_start = current_month_start()
    month_end = _month_end(month_start)

    receipts = await PaymentReceipt.find(Eq(PaymentReceipt.tenant_id, tenant_id)).sort("-issued_at").to_list()
    month_receipts = [r for r in receipts if _receipt_in_month(r, month_start, month_end)]

    generated = len(month_receipts) if month_receipts else len(receipts)
    published = sum(1 for r in (month_receipts or receipts) if r.published)

    history = await PaymentReceiptDocumentHistory.find(
        Eq(PaymentReceiptDocumentHistory.tenant_id, tenant_id),
    ).to_list()
    reissue_requests = sum(1 for row in history if (row.action or "").lower() in {"reissue", "reissue_request", "reissue_requested"})

    cancelled_reversed = sum(
        1
        for r in receipts
        if (r.receipt_status or "").lower() in {"cancelled", "reversed", "superseded"} or r.superseded_by
    )

    kpis = [
        UserDashboardKpi(
            key="generated",
            label="Generated",
            value=format_count(generated),
            hint_line=month_label(month_start),
            hint_tone="blue",
        ),
        UserDashboardKpi(key="published", label="Published", value=format_count(published), hint_line="", hint_tone="muted"),
        UserDashboardKpi(
            key="reissue_requests",
            label="Reissue requests",
            value=str(reissue_requests),
            hint_line="",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="cancelled_reversed",
            label="Cancelled / reversed",
            value=str(cancelled_reversed),
            hint_line="",
            hint_tone="muted",
        ),
    ]

    total = len(receipts)
    pagination, start = _pagination(total, page, _RECEIPT_PAGE_SIZE)
    page_rows = receipts[start : start + _RECEIPT_PAGE_SIZE]

    invoice_ids = {r.invoice_id for r in page_rows if r.invoice_id}
    invoices = (
        await StudentFeeInvoice.find(
            Eq(StudentFeeInvoice.tenant_id, tenant_id),
            In(StudentFeeInvoice.invoice_id, list(invoice_ids)),
        ).to_list()
        if invoice_ids
        else []
    )
    invoice_by_id = {inv.invoice_id: inv for inv in invoices}

    user_ids = {r.student_user_id for r in page_rows}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_names = {u.id: (u.full_name or "—").strip() or "—" for u in users}

    table_rows: list[FinanceReceiptTableRow] = []
    for receipt in page_rows:
        status_label, status_tone = receipt_status(receipt)
        inv = invoice_by_id.get(receipt.invoice_id or "")
        table_rows.append(
            FinanceReceiptTableRow(
                receipt_label=receipt_label(receipt),
                student_name=user_names.get(receipt.student_user_id, "—"),
                invoice_label=invoice_label_for_receipt(receipt.invoice_id, inv),
                amount_label=format_inr(receipt.amount),
                date_label=receipt_date_label(receipt.issued_at),
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/finance/receipt-management",
            )
        )

    shown = len(page_rows)
    return ReceiptManagementPageRead(
        page_title="Receipt Management",
        page_subtitle="Official receipts and reissues",
        bulk_generate_label="Bulk generate",
        bulk_generate_href="/college-admin/finance/receipt-management?bulk=1",
        kpis=kpis,
        sub_nav=receipts_sub_nav("receipts"),
        receipts_section_title="Receipts",
        table_headers=["Receipt", "Student", "Invoice", "Amount", "Date", "Status"],
        receipt_rows=table_rows,
        showing_label=showing_slice(start, shown, total),
        pagination=pagination,
        generated_at=now,
    )


def _demand_balance(demand: StudentFeeDemand, paid: float) -> float:
    due = round_money(demand.amount + demand.late_fee)
    return max(0.0, round_money(due - paid))


def _aging_key(days_overdue: int, not_due: bool) -> str:
    if not_due:
        return "not_due"
    if days_overdue <= 30:
        return "1_30"
    if days_overdue <= 60:
        return "31_60"
    return "over_60"


_AGING_META = (
    ("not_due", "Not yet due", "green"),
    ("1_30", "1–30 days", "blue"),
    ("31_60", "31–60 days", "amber"),
    ("over_60", "Over 60 days", "error"),
)


async def get_outstanding_dues_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> OutstandingDuesManagementPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.date()

    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    invoices = await StudentFeeInvoice.find(Eq(StudentFeeInvoice.tenant_id, tenant_id)).to_list()
    invoice_by_demand = {inv.demand_id: inv for inv in invoices if inv.demand_id}

    txs = await PaymentTransaction.find(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.status, PaymentTransactionStatus.SUCCESS),
    ).to_list()
    paid_by_demand: dict[str, float] = defaultdict(float)
    for tx in txs:
        if not _verified_payment(tx):
            continue
        if tx.demand_id:
            paid_by_demand[tx.demand_id] += tx.amount

    outstanding_rows: list[tuple[StudentFeeDemand, float, int, StudentFeeInvoice | None]] = []
    total_unpaid = 0.0
    students_with_dues: set = set()
    overdue_invoice_count = 0
    overdue_invoice_amount = 0.0
    late_fees_assessed = 0.0
    aging_amounts: dict[str, float] = defaultdict(float)

    for demand in demands:
        if demand.status in (FeeDemandStatus.PAID, FeeDemandStatus.WAIVED):
            continue
        paid = paid_by_demand.get(demand.demand_id, 0.0)
        balance = _demand_balance(demand, paid)
        if balance <= 0:
            continue
        days_overdue = max(0, (today - demand.due_date).days)
        not_due = demand.due_date > today
        inv = invoice_by_demand.get(demand.demand_id)
        outstanding_rows.append((demand, balance, days_overdue, inv))
        total_unpaid += balance
        students_with_dues.add(demand.student_user_id)
        if demand.late_fee > 0:
            late_fees_assessed += demand.late_fee
        if days_overdue > 0:
            overdue_invoice_count += 1
            overdue_invoice_amount += balance
        aging_amounts[_aging_key(days_overdue, not_due)] += balance

    outstanding_rows.sort(key=lambda row: (-row[2], -row[1]))

    installment_overdue_n = 0
    installment_overdue_amt = 0.0
    schedules = await FeeInstallmentSchedule.find(Eq(FeeInstallmentSchedule.tenant_id, tenant_id)).to_list()
    for schedule in schedules:
        for inst in schedule.installments or []:
            due_raw = inst.get("due_date")
            remaining = float(inst.get("remaining_amount") or inst.get("amount") or 0)
            if not due_raw or remaining <= 0:
                continue
            try:
                due = date.fromisoformat(str(due_raw)[:10])
            except ValueError:
                continue
            if due < today:
                installment_overdue_n += 1
                installment_overdue_amt += remaining

    kpis = [
        UserDashboardKpi(
            key="total_unpaid",
            label="Total unpaid",
            value=format_inr_compact(total_unpaid),
            hint_line=f"{format_count(len(students_with_dues))} students",
            hint_tone="amber",
        ),
        UserDashboardKpi(
            key="overdue_invoices",
            label="Overdue invoices",
            value=str(overdue_invoice_count),
            hint_line=format_inr_compact(overdue_invoice_amount),
            hint_tone="rose",
        ),
        UserDashboardKpi(
            key="late_fees",
            label="Late fees assessed",
            value=format_inr_compact(late_fees_assessed),
            hint_line="Not yet posted",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="installments_overdue",
            label="Installments overdue",
            value=str(installment_overdue_n),
            hint_line=format_inr_compact(installment_overdue_amt),
            hint_tone="amber",
        ),
    ]

    total = len(outstanding_rows)
    pagination, start = _pagination(total, page, _DUES_PAGE_SIZE)
    page_slice = outstanding_rows[start : start + _DUES_PAGE_SIZE]

    user_ids = {row[0].student_user_id for row in page_slice}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_names = {u.id: (u.full_name or "—").strip() or "—" for u in users}

    def _invoice_label(inv: StudentFeeInvoice | None, demand: StudentFeeDemand) -> str:
        if inv:
            return invoice_label_for_receipt(inv.invoice_id, inv)
        suffix = "".join(ch for ch in demand.demand_id if ch.isdigit())[-5:] or "00000"
        return f"INV-{today.year}-{suffix.zfill(5)}"

    table_rows: list[FinanceOutstandingDuesTableRow] = []
    for demand, balance, days_overdue, inv in page_slice:
        overdue_label = f"{days_overdue} days" if days_overdue > 0 else "—"
        table_rows.append(
            FinanceOutstandingDuesTableRow(
                student_name=user_names.get(demand.student_user_id, "—"),
                invoice_label=_invoice_label(inv, demand),
                balance_label=format_inr(balance),
                overdue_label=overdue_label,
                detail_href="/college-admin/finance/outstanding-dues-management",
            )
        )

    aging_total = sum(aging_amounts.values()) or 1.0
    aging_items: list[FinanceAgingBucketItem] = []
    for key, label, tone in _AGING_META:
        amount = aging_amounts.get(key, 0.0)
        pct = int(round((amount / aging_total) * 100)) if aging_total else 0
        aging_items.append(
            FinanceAgingBucketItem(
                bucket_key=key,
                label=label,
                amount_label=format_inr_compact(amount),
                progress_percent=pct,
                bar_tone=tone,
            )
        )

    shown = len(page_slice)
    list_footer_label = f"{min(start + shown, total)} of {format_count(len(students_with_dues))}"

    return OutstandingDuesManagementPageRead(
        page_title="Outstanding Dues Management",
        page_subtitle="Overdue invoices and follow-up",
        send_reminders_label="Send reminders",
        send_reminders_href="/college-admin/finance/outstanding-dues-management?reminders=1",
        kpis=kpis,
        sub_nav=receipts_sub_nav("dues"),
        dues_section_title="Outstanding dues",
        table_headers=["Student", "Invoice", "Balance", "Overdue"],
        dues_rows=table_rows,
        showing_label=showing_slice(start, shown, total),
        list_count_label=list_footer_label,
        pagination=pagination,
        aging_section_title="Aging",
        aging_items=aging_items,
        generated_at=now,
    )