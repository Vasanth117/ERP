"""Shared helpers for finance payment monitoring pages."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from datetime import date
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import In

from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.schemas import FinanceDashboardTransactionRow, YearsSemestersSubNavItem
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction

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


def method_label(tx: PaymentTransaction) -> str:
    mode = (tx.payment_mode or "online").lower()
    gateway = (tx.gateway or "").lower()
    ref = (tx.offline_reference or "").lower()
    if "upi" in gateway or "upi" in ref:
        return "UPI"
    if mode == "offline":
        if "cheque" in ref or "cheque" in gateway:
            return "Cheque"
        if "dd" in ref or "demand" in ref:
            return "Demand draft"
        if any(k in ref or k in gateway for k in ("neft", "net", "bank", "rtgs", "imps")):
            return "Net banking"
        if "cash" in ref or "counter" in gateway:
            return "Cash"
        return "Counter"
    if "card" in gateway:
        return "Card"
    if mode == "online":
        return "Online"
    return (tx.payment_mode or "Online").replace("_", " ").title()


def transaction_status(tx: PaymentTransaction) -> tuple[str, str]:
    if tx.status == PaymentTransactionStatus.SUCCESS:
        if tx.reversed_total > 0:
            return "Reversed", "info"
        if tx.payment_mode == "offline" or tx.webhook_verified:
            return "Verified", "success"
        return "Pending", "warning"
    if tx.status in (
        PaymentTransactionStatus.PENDING,
        PaymentTransactionStatus.PROCESSING,
        PaymentTransactionStatus.VERIFICATION_REQUIRED,
    ):
        return "Pending", "warning"
    if tx.status == PaymentTransactionStatus.FAILED:
        return "Failed", "error"
    if tx.status == PaymentTransactionStatus.REFUNDED:
        return "Reversed", "info"
    return tx.status.value.replace("_", " ").title(), "muted"


def offline_status(tx: PaymentTransaction) -> tuple[str, str]:
    method = method_label(tx)
    if tx.status == PaymentTransactionStatus.SUCCESS:
        return "Verified", "success"
    if tx.status == PaymentTransactionStatus.PROCESSING or (method == "Cheque" and tx.status == PaymentTransactionStatus.PENDING):
        return "Clearing", "info"
    if tx.status in (PaymentTransactionStatus.PENDING, PaymentTransactionStatus.VERIFICATION_REQUIRED):
        return "Verifying", "warning"
    if tx.status == PaymentTransactionStatus.FAILED:
        return "Failed", "error"
    return "Verifying", "warning"


def invoice_label(tx: PaymentTransaction) -> str:
    if tx.invoice_id:
        if tx.invoice_id.upper().startswith("INV"):
            return tx.invoice_id
        return f"INV-{tx.invoice_id}"
    suffix = tx.transaction_id.replace("TXN-", "")[-8:] if tx.transaction_id else "00000"
    return f"INV-2026-{suffix}"


def offline_reference(tx: PaymentTransaction) -> str:
    ref = (tx.offline_reference or "").strip()
    if ref.upper().startswith("OFF"):
        return ref
    if tx.transaction_id.upper().startswith("OFF"):
        return tx.transaction_id
    suffix = re.sub(r"\D", "", tx.transaction_id)[-4:] or "0000"
    return f"OFF-2611-{suffix}"


def counter_label(tx: PaymentTransaction) -> str:
    gateway = (tx.gateway or "").strip()
    if gateway.lower().startswith("counter"):
        parts = gateway.replace("_", " ").title()
        return parts if parts else "Counter 1"
    ref = (tx.offline_reference or "").lower()
    if "counter 2" in ref:
        return "Counter 2"
    if "counter 3" in ref:
        return "Counter 3"
    return "Counter 1"


def payment_sub_nav(active_key: str) -> list[YearsSemestersSubNavItem]:
    return [
        YearsSemestersSubNavItem(
            key="online",
            label="Online monitoring",
            href="/college-admin/finance/online-payment-monitoring",
            active=active_key == "online",
        ),
        YearsSemestersSubNavItem(
            key="offline",
            label="Offline collection",
            href="/college-admin/finance/offline-payment-collection",
            active=active_key == "offline",
        ),
        YearsSemestersSubNavItem(
            key="all",
            label="All transactions",
            href="/college-admin/finance/payment-transactions",
            active=active_key == "all",
        ),
    ]


def is_online_tx(tx: PaymentTransaction) -> bool:
    return (tx.payment_mode or "online").lower() != "offline"


def is_offline_tx(tx: PaymentTransaction) -> bool:
    return (tx.payment_mode or "").lower() == "offline"


def month_label(when: date) -> str:
    return when.strftime("%b %Y")


async def build_transaction_rows(
    txs: list[PaymentTransaction],
) -> list[FinanceDashboardTransactionRow]:
    user_ids = {t.student_user_id for t in txs}
    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_names = {u.id: (u.full_name or "—").strip() or "—" for u in users}
    rows: list[FinanceDashboardTransactionRow] = []
    for tx in txs:
        status_label, status_tone = transaction_status(tx)
        rows.append(
            FinanceDashboardTransactionRow(
                transaction_id=tx.transaction_id,
                student_name=user_names.get(tx.student_user_id, "—"),
                invoice_label=invoice_label(tx),
                method_label=method_label(tx),
                amount_label=format_inr(tx.amount),
                status_label=status_label,
                status_tone=status_tone,
                detail_href="/college-admin/finance/payment-transactions",
            )
        )
    return rows


def _gateway_rate_key(gateway_name: str | None) -> str:
    """Normalize transaction gateway field for success-rate buckets."""
    raw = (gateway_name or "unknown").strip().lower()
    return raw.replace(" ", "_") if raw else "unknown"


def gateway_success_rates(txs: list[PaymentTransaction], *, day: date) -> dict[str, float]:
    buckets: dict[str, list[bool]] = defaultdict(list)
    for tx in txs:
        if not is_online_tx(tx):
            continue
        local = tx.created_at.astimezone(_IST) if tx.created_at.tzinfo else tx.created_at.replace(tzinfo=_IST)
        if local.date() != day:
            continue
        key = _gateway_rate_key(tx.gateway)
        buckets[key].append(tx.status == PaymentTransactionStatus.SUCCESS)
    out: dict[str, float] = {}
    for key, results in buckets.items():
        if results:
            out[key] = round((sum(results) / len(results)) * 100, 1)
    return out


def current_month_start() -> date:
    now = utcnow().astimezone(_IST)
    return date(now.year, now.month, 1)