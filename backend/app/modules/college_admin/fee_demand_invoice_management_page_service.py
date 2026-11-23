"""Fee demand & invoice management page (CA 10.04)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import date
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.finance_overview_service import _verified_payment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    FeeDemandInvoiceManagementPageRead,
    FeeDemandInvoiceManagementTableRow,
    PoliciesPagination,
    UserDashboardKpi,
)
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand, StudentFeeInvoice

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 10


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _format_inr(amount: float) -> str:
    rupees = int(round(amount))
    s = str(rupees)
    if len(s) <= 3:
        return f"₹{s}"
    last3 = s[-3:]
    rest = s[:-3]
    groups: list[str] = []
    while rest:
        take = 2 if len(rest) > 2 else len(rest)
        groups.insert(0, rest[-take:])
        rest = rest[:-take]
    return f"₹{','.join(groups + [last3])}"


def _format_inr_compact(amount: float) -> str:
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f} Cr"
    if amount >= 100_000:
        return f"₹{amount / 100_000:.1f} L"
    return _format_inr(amount)


def _invoice_label(inv: StudentFeeInvoice) -> str:
    if inv.invoice_number:
        return inv.invoice_number
    if inv.invoice_id.upper().startswith("INV-"):
        return inv.invoice_id
    year = inv.issued_at.astimezone(_IST).year if inv.issued_at else utcnow().year
    suffix = "".join(ch for ch in inv.invoice_id if ch.isdigit())[-5:] or inv.invoice_id[-5:]
    return f"INV-{year}-{suffix.zfill(5)}"


def _due_label(due: date) -> str:
    return due.strftime("%d %b %Y")


def _row_status(
    inv: StudentFeeInvoice,
    demand: StudentFeeDemand | None,
    paid: float,
) -> tuple[str, str]:
    total_due = inv.amount + (demand.late_fee if demand else 0)
    if demand and demand.status == FeeDemandStatus.PAID:
        return "Paid", "success"
    if paid >= total_due > 0:
        return "Paid", "success"
    if paid > 0:
        return "Partly paid", "warning"
    if demand and demand.status == FeeDemandStatus.OVERDUE:
        return "Overdue", "error"
    if demand and demand.due_date < utcnow().date() and demand.status in (
        FeeDemandStatus.OPEN,
        FeeDemandStatus.PARTIALLY_PAID,
    ):
        return "Overdue", "error"
    if not inv.published:
        return "Draft", "muted"
    return "Open", "info"


async def get_fee_demand_invoice_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> FeeDemandInvoiceManagementPageRead:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    invoices = await StudentFeeInvoice.find(Eq(StudentFeeInvoice.tenant_id, tenant_id)).sort("-issued_at").to_list()
    demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    demand_by_id = {d.demand_id: d for d in demands}

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

    total_invoices = len(invoices)
    published_count = sum(1 for inv in invoices if inv.published)
    published_pct = round((published_count / total_invoices) * 100, 1) if total_invoices else 0.0

    overdue_count = 0
    overdue_amount = 0.0
    for demand in demands:
        if demand.status == FeeDemandStatus.OVERDUE:
            overdue_count += 1
            overdue_amount += demand.amount + demand.late_fee
        elif demand.due_date < today and demand.status in (
            FeeDemandStatus.OPEN,
            FeeDemandStatus.PARTIALLY_PAID,
        ):
            overdue_count += 1
            overdue_amount += demand.amount + demand.late_fee - paid_by_demand.get(demand.demand_id, 0)

    corrections_open = sum(
        1
        for inv in invoices
        if not inv.published
        or (inv.invoice_status or "").lower() in {"draft", "adjusted", "correction", "pending"}
    )

    total = total_invoices
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_invoices = invoices[start : start + _PAGE_SIZE]

    user_ids = {inv.student_user_id for inv in page_invoices}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_names = {u.id: (u.full_name or "—").strip() or "—" for u in users}

    rows: list[FeeDemandInvoiceManagementTableRow] = []
    for inv in page_invoices:
        demand = demand_by_id.get(inv.demand_id or "")
        paid = paid_by_demand.get(inv.demand_id or "", 0.0)
        status_label, status_tone = _row_status(inv, demand, paid)
        rows.append(
            FeeDemandInvoiceManagementTableRow(
                invoice_id=inv.invoice_id,
                invoice_label=_invoice_label(inv),
                student_name=user_names.get(inv.student_user_id, "—"),
                due_label=_due_label(inv.due_date),
                total_label=_format_inr(inv.amount + (demand.late_fee if demand else 0)),
                paid_label=_format_inr(paid),
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/finance/fee-demand-invoice-management",
            )
        )

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    kpis = [
        UserDashboardKpi(
            key="invoices",
            label="Invoices",
            value=f"{total_invoices:,}",
            hint_line="Generated",
            hint_tone="info",
        ),
        UserDashboardKpi(
            key="published",
            label="Published",
            value=f"{published_count:,}",
            hint_line=f"{published_pct:g}%" if total_invoices else "—",
            hint_tone="success",
        ),
        UserDashboardKpi(
            key="overdue",
            label="Overdue",
            value=f"{overdue_count:,}",
            hint_line=_format_inr_compact(overdue_amount) if overdue_amount > 0 else "None",
            hint_tone="error" if overdue_count else "success",
        ),
        UserDashboardKpi(
            key="corrections",
            label="Corrections open",
            value=f"{corrections_open:,}",
            hint_line="Draft or adjustment",
            hint_tone="warning" if corrections_open else "success",
        ),
    ]

    return FeeDemandInvoiceManagementPageRead(
        page_title="Fee Demand & Invoice Management",
        page_subtitle="Generate and publish fee demands",
        generate_demands_label="Generate demands",
        generate_demands_href="/college-admin/finance/fee-demand-invoice-management?generate=1",
        publish_label="Publish",
        publish_href="/college-admin/finance/fee-demand-invoice-management?publish=1",
        kpis=kpis,
        invoices_section_title="Invoices",
        invoices_count_label=f"{total_invoices:,} invoices" if total_invoices else "0 invoices",
        table_headers=["Invoice", "Student", "Due", "Total", "Paid", "Status"],
        invoice_rows=rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total_invoices:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1,
            has_next=page < total_pages,
        ),
        generated_at=now,
    )