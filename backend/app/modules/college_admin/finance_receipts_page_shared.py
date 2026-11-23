"""Shared helpers for finance receipt & dues pages."""

from __future__ import annotations

import math
import re
from datetime import date
from zoneinfo import ZoneInfo

from app.common.time import utcnow
from app.modules.college_admin.schemas import YearsSemestersSubNavItem
from app.modules.finance.finance_models import PaymentReceipt, StudentFeeInvoice

_IST = ZoneInfo("Asia/Kolkata")


def page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def format_inr(amount: float) -> str:
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


def format_inr_compact(amount: float) -> str:
    if amount >= 10_000_000:
        return f"₹{amount / 10_000_000:.2f} Cr"
    if amount >= 100_000:
        return f"₹{amount / 100_000:.1f} L"
    return format_inr(amount)


def format_count(n: int) -> str:
    return f"{n:,}"


def month_label(when: date) -> str:
    return when.strftime("%b %Y")


def receipt_label(receipt: PaymentReceipt) -> str:
    if receipt.receipt_number:
        return receipt.receipt_number
    rid = (receipt.receipt_id or "").strip()
    if rid.upper().startswith("RCT"):
        return rid
    suffix = re.sub(r"\D", "", rid)[-4:] or "0000"
    return f"RCT-2611-{suffix}"


def invoice_label_for_receipt(invoice_id: str | None, inv: StudentFeeInvoice | None) -> str:
    if inv:
        if inv.invoice_number:
            return inv.invoice_number
        if inv.invoice_id.upper().startswith("INV"):
            return inv.invoice_id
        year = inv.issued_at.astimezone(_IST).year if inv.issued_at else utcnow().year
        suffix = "".join(ch for ch in inv.invoice_id if ch.isdigit())[-5:] or "00000"
        return f"INV-{year}-{suffix.zfill(5)}"
    if invoice_id:
        return invoice_id if invoice_id.upper().startswith("INV") else f"INV-{invoice_id}"
    return "—"


def receipt_date_label(issued_at) -> str:
    local = issued_at.astimezone(_IST) if issued_at.tzinfo else issued_at.replace(tzinfo=_IST)
    return local.strftime("%d %b")


def receipt_status(receipt: PaymentReceipt) -> tuple[str, str]:
    status = (receipt.receipt_status or "issued").lower()
    if status in ("cancelled", "reversed", "superseded") or receipt.superseded_by:
        return "Reversed", "error"
    if receipt.published:
        return "Published", "success"
    if status in ("draft",):
        return "Draft", "muted"
    return "Published", "success"


def receipts_sub_nav(active_key: str) -> list[YearsSemestersSubNavItem]:
    return [
        YearsSemestersSubNavItem(
            key="receipts",
            label="Receipt management",
            href="/college-admin/finance/receipt-management",
            active=active_key == "receipts",
        ),
        YearsSemestersSubNavItem(
            key="dues",
            label="Outstanding dues",
            href="/college-admin/finance/outstanding-dues-management",
            active=active_key == "dues",
        ),
    ]


def current_month_start() -> date:
    now = utcnow().astimezone(_IST)
    return date(now.year, now.month, 1)


def showing_slice(start: int, shown: int, total: int) -> str:
    if total <= 0:
        return "Showing 0 of 0"
    return f"Showing {shown} of {format_count(total)}"