"""Shared helpers for hostel resident management and check-in/out pages."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.modules.finance.finance_enums import FeeDemandStatus
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.hostel.hostel_portal_enums import HostelCategory
from app.modules.hostel.infrastructure_models import InstitutionHostel
from app.modules.hostel.mess_models import HostelMessBillingRecord, MessBillingRecordStatus
from app.modules.hostel.resident_models import HostelResidentStatus

_IST = ZoneInfo("Asia/Kolkata")
_ALL = ""

_IN_RESIDENCE = frozenset({HostelResidentStatus.CHECKED_IN, HostelResidentStatus.TEMPORARILY_OUTSIDE})
_NOTICE = frozenset({HostelResidentStatus.CHECKOUT_REQUESTED, HostelResidentStatus.TRANSFER_PENDING})


def week_start_ist(now: datetime | None = None) -> datetime:
    base = (now or datetime.now(_IST)).astimezone(_IST)
    start = base.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=base.weekday())
    return start


def block_display_label(
    *,
    block_code: str,
    hostel: InstitutionHostel | None,
    block_name: str | None,
) -> str:
    name = (block_name or block_code).strip()
    if not hostel:
        return name
    category = ""
    if hostel.category == HostelCategory.CUSTOM and hostel.custom_category_label:
        category = hostel.custom_category_label
    else:
        category = hostel.category.value.replace("_", " ").title()
    if category:
        return f"{name} ({category})"
    if hostel.name and hostel.name != name:
        return f"{hostel.name} ({name})"
    return name


def resident_status_display(status: HostelResidentStatus) -> tuple[str, str]:
    if status in _IN_RESIDENCE:
        return "In residence", "success"
    if status in _NOTICE:
        return "Notice", "warning"
    if status == HostelResidentStatus.AWAITING_CHECKIN:
        return "Awaiting check-in", "info"
    if status == HostelResidentStatus.CHECKED_OUT:
        return "Checked out", "muted"
    key = status.value.replace("_", " ")
    return key.title(), "muted"


def status_filter_matches(status: HostelResidentStatus, filter_key: str | None) -> bool:
    if not filter_key or filter_key == _ALL:
        return True
    if filter_key == "in_residence":
        return status in _IN_RESIDENCE
    if filter_key == "notice":
        return status in _NOTICE
    if filter_key == "awaiting":
        return status == HostelResidentStatus.AWAITING_CHECKIN
    return status.value == filter_key


def register_number(*, roll_number: str | None, student_id: str | None) -> str:
    for candidate in (roll_number, student_id):
        if candidate and str(candidate).strip():
            return str(candidate).strip()
    return "—"


def fee_column(
    *,
    demands: list[StudentFeeDemand],
    billing_rows: list[HostelMessBillingRecord],
) -> tuple[str, str]:
    hostel_demands = [d for d in demands if "hostel" in (d.description or "").lower()]
    if hostel_demands:
        open_demands = [d for d in hostel_demands if d.status != FeeDemandStatus.WAIVED]
        if open_demands:
            statuses = {d.status for d in open_demands}
            today = date.today()
            if any(d.due_date < today and d.status not in (FeeDemandStatus.PAID,) for d in open_demands):
                return "Overdue", "error"
            if FeeDemandStatus.OVERDUE in statuses:
                return "Overdue", "error"
            if FeeDemandStatus.OPEN in statuses or FeeDemandStatus.PARTIALLY_PAID in statuses:
                return "Due", "warning"
            if all(d.status == FeeDemandStatus.PAID for d in open_demands):
                return "Paid", "success"
            return "Due", "warning"
        return "Paid", "success"

    if billing_rows:
        latest = max(billing_rows, key=lambda row: row.updated_at)
        status = latest.status
        if status in (MessBillingRecordStatus.PAID, MessBillingRecordStatus.RECONCILED):
            return "Paid", "success"
        if status == MessBillingRecordStatus.PARTIALLY_PAID:
            return "Due", "warning"
        if status == MessBillingRecordStatus.PAYMENT_FAILED:
            return "Overdue", "error"
        if status in (MessBillingRecordStatus.DRAFT, MessBillingRecordStatus.PENDING_REVIEW):
            return "Due", "warning"
        return "Due", "warning"

    return "—", "muted"


def deposit_refund_total(clearance: dict | None) -> float:
    if not clearance:
        return 0.0
    total = 0.0
    for key in ("deposit_refund", "refund_amount", "deposit_refund_amount", "refund_total"):
        raw = clearance.get(key)
        if raw is None:
            continue
        try:
            total += float(raw)
        except (TypeError, ValueError):
            continue
    return total