"""Shared helpers for finance reconciliation & reports pages."""

from __future__ import annotations

import re
from zoneinfo import ZoneInfo

from app.common.time import utcnow
from app.modules.college_admin.schemas import YearsSemestersSubNavItem

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


def short_date(when) -> str:
    local = when.astimezone(_IST) if when.tzinfo else when.replace(tzinfo=_IST)
    return local.strftime("%d %b")


def month_label() -> str:
    now = utcnow().astimezone(_IST)
    return now.strftime("%b %Y")


def batch_label(batch_id: str) -> str:
    bid = (batch_id or "").strip()
    if bid.upper().startswith("RB"):
        return bid
    suffix = re.sub(r"\D", "", bid)[-2:] or "01"
    return f"RB-2611-{suffix.zfill(2)}"


def source_label(source_type: str) -> str:
    key = (source_type or "").lower()
    if "razor" in key or key == "gateway":
        return "Razorpay"
    if "hdfc" in key:
        return "HDFC bank"
    if "payu" in key:
        return "PayU"
    if "bank" in key:
        return "Bank file"
    if not key:
        return "Gateway"
    return source_type.replace("_", " ").title()


def period_range_label(start, end) -> str:
    if start and end:
        if start.month == end.month and start.year == end.year:
            return f"{start.day:02d}–{end.day:02d} {start.strftime('%b')}"
        return f"{start.strftime('%d %b')}–{end.strftime('%d %b')}"
    return "—"


def schedule_label(cron_hint: str | None) -> str:
    hint = (cron_hint or "").lower()
    if "daily" in hint or hint == "0 6 * * *":
        return "Daily"
    if "weekly" in hint or hint.startswith("0 6 * *"):
        return "Weekly"
    if "monthly" in hint:
        return "Monthly"
    return cron_hint or "Manual"


def reconciliation_sub_nav(active_key: str) -> list[YearsSemestersSubNavItem]:
    return [
        YearsSemestersSubNavItem(
            key="reconciliation",
            label="Payment reconciliation",
            href="/college-admin/finance/payment-reconciliation",
            active=active_key == "reconciliation",
        ),
        YearsSemestersSubNavItem(
            key="reports",
            label="Financial reports",
            href="/college-admin/finance/financial-reports",
            active=active_key == "reports",
        ),
    ]


def showing_slice(shown: int, total: int) -> str:
    if total <= 0:
        return "Showing 0 of 0"
    return f"Showing {shown} of {format_count(total)}"