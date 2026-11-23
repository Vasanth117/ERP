"""Shared helpers for finance aid & refunds pages."""

from __future__ import annotations

import re
from datetime import date
from zoneinfo import ZoneInfo

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


def refund_display_id(refund_id: str) -> str:
    rid = (refund_id or "").strip()
    if rid.upper().startswith("RFD"):
        return rid
    suffix = re.sub(r"\D", "", rid)[-4:] or "0001"
    return f"RFD-2611-{suffix.zfill(4)}"


def aid_sub_nav(active_key: str) -> list[YearsSemestersSubNavItem]:
    return [
        YearsSemestersSubNavItem(
            key="scholarships",
            label="Scholarships",
            href="/college-admin/finance/scholarship-management",
            active=active_key == "scholarships",
        ),
        YearsSemestersSubNavItem(
            key="concessions",
            label="Concessions & waivers",
            href="/college-admin/finance/fee-concession-waiver-management",
            active=active_key == "concessions",
        ),
        YearsSemestersSubNavItem(
            key="refunds",
            label="Refunds",
            href="/college-admin/finance/refund-management",
            active=active_key == "refunds",
        ),
    ]


def showing_slice(shown: int, total: int) -> str:
    if total <= 0:
        return "0 of 0"
    return f"{min(shown, total)} of {format_count(total)}"