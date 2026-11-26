"""Shared helpers for hostel fee management pages."""

from __future__ import annotations

from collections import Counter

from beanie import PydanticObjectId

from app.modules.college_admin.finance_reconciliation_reports_shared import format_inr, format_inr_compact
from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.finance.payment_reconciliation import _verified_paid_on_demand
from app.modules.hostel.mess_models import HostelMessBillingRecord, MessBillingRecordStatus

_HOSTEL_KEYWORDS = ("hostel", "mess", "room rent", "deposit")


def is_hostel_fee_demand(demand: StudentFeeDemand) -> bool:
    desc = (demand.description or "").lower()
    return any(k in desc for k in _HOSTEL_KEYWORDS)


def fee_status_label(*, balance: float, overdue: bool, paid: float, billed: float) -> tuple[str, str]:
    if billed <= 0:
        return "—", "muted"
    if balance <= 0 and paid >= billed:
        return "Paid", "success"
    if overdue:
        return "Overdue", "error"
    if balance > 0:
        return "Due", "warning"
    return "Paid", "success"


def pick_academic_year_label(*, demands: list[StudentFeeDemand], period_labels: list[str]) -> str | None:
    counts = Counter(d.academic_year_label for d in demands if d.academic_year_label)
    if counts:
        return counts.most_common(1)[0][0]
    if period_labels:
        return period_labels[0]
    return None


async def demand_paid_amount(tenant_id: PydanticObjectId, demand_id: str) -> float:
    return await _verified_paid_on_demand(tenant_id, demand_id)


def billing_record_paid_amount(record: HostelMessBillingRecord) -> float:
    if record.status in (MessBillingRecordStatus.PAID, MessBillingRecordStatus.RECONCILED):
        return record.amount
    if record.status == MessBillingRecordStatus.PARTIALLY_PAID:
        return record.amount * 0.5
    return 0.0


def demand_balance(demand: StudentFeeDemand, paid: float) -> float:
    if demand.status == FeeDemandStatus.WAIVED:
        return 0.0
    total = demand.amount + (demand.late_fee or 0)
    return max(0.0, total - paid)


def deposit_held_amount(clearance: dict | None) -> float:
    if not clearance:
        return 0.0
    total = 0.0
    for key in ("deposit_held", "security_deposit", "deposit_balance", "deposit_amount"):
        raw = clearance.get(key)
        if raw is None:
            continue
        try:
            total += float(raw)
        except (TypeError, ValueError):
            continue
    return total


__all__ = [
    "billing_record_paid_amount",
    "demand_balance",
    "demand_paid_amount",
    "deposit_held_amount",
    "fee_status_label",
    "format_inr",
    "format_inr_compact",
    "is_hostel_fee_demand",
    "pick_academic_year_label",
]