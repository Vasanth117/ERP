"""Shared outpass presentation helpers for hostel admin pages."""

from __future__ import annotations

from datetime import date
from zoneinfo import ZoneInfo

from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus, HostelOutpassRequest, HostelOutpassType

_IST = ZoneInfo("Asia/Kolkata")

_INFORMED_STATUSES = frozenset(
    {
        HostelLeaveOutpassStatus.APPROVED.value,
        HostelLeaveOutpassStatus.DEPARTURE_RECORDED.value,
        HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE.value,
        HostelLeaveOutpassStatus.RETURNED.value,
        HostelLeaveOutpassStatus.CLOSED.value,
    }
)
_AWAITING_STATUSES = frozenset(
    {
        HostelLeaveOutpassStatus.PENDING_APPROVAL.value,
        HostelLeaveOutpassStatus.SUBMITTED.value,
        HostelLeaveOutpassStatus.RETURNED_FOR_CORRECTION.value,
    }
)

_OUTPASS_TYPE_LABELS: dict[HostelOutpassType, str] = {
    HostelOutpassType.WEEKEND: "Weekend",
    HostelOutpassType.DAY: "Day pass",
    HostelOutpassType.SHORT: "Short outpass",
    HostelOutpassType.OVERNIGHT: "Overnight",
    HostelOutpassType.EMERGENCY: "Emergency",
    HostelOutpassType.SPECIAL: "Special",
}


def short_day(d: date) -> str:
    return d.strftime("%d %b")


def outpass_type_label(req: HostelOutpassRequest) -> str:
    reason_lower = (req.reason or "").lower()
    dest_lower = (req.destination or "").lower()
    if "late" in reason_lower or "late return" in reason_lower:
        return "Late return"
    if "home" in dest_lower or "home visit" in reason_lower:
        return "Home visit"
    return _OUTPASS_TYPE_LABELS.get(req.outpass_type, req.outpass_type.value.replace("_", " ").title())


def guardian_for_status(status: HostelLeaveOutpassStatus | str) -> tuple[str, str]:
    key = status.value if isinstance(status, HostelLeaveOutpassStatus) else str(status)
    if key in _INFORMED_STATUSES:
        return "Informed", "success"
    if key in _AWAITING_STATUSES:
        return "Awaiting", "warning"
    if key == HostelLeaveOutpassStatus.REJECTED.value:
        return "Not informed", "error"
    return "—", "muted"


def outpass_status_presentation(status: HostelLeaveOutpassStatus | str) -> tuple[str, str]:
    key = status.value if isinstance(status, HostelLeaveOutpassStatus) else str(status)
    if key in _AWAITING_STATUSES:
        return "Pending", "warning"
    if key == HostelLeaveOutpassStatus.APPROVED.value:
        return "Approved", "success"
    if key == HostelLeaveOutpassStatus.REJECTED.value:
        return "Rejected", "error"
    if key in {HostelLeaveOutpassStatus.CURRENTLY_OUTSIDE.value, HostelLeaveOutpassStatus.DEPARTURE_RECORDED.value}:
        return "Active", "info"
    if key == HostelLeaveOutpassStatus.RETURNED.value:
        return "Returned", "success"
    return key.replace("_", " ").title(), "muted"


def outpass_sort_key(req: HostelOutpassRequest) -> tuple[int, float]:
    status = req.status.value if hasattr(req.status, "value") else str(req.status)
    priority = 0 if status in _AWAITING_STATUSES else 1
    return priority, -req.from_at.timestamp()