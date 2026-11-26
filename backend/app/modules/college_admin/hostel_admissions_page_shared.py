"""Shared helpers for hostel admission applications and bed allocation pages."""

from __future__ import annotations

import re
from collections import Counter
from datetime import datetime

from app.modules.hostel.hostel_enums import HostelApplicationStatus
from app.modules.hostel.hostel_models import HostelApplication

_PENDING_STATUSES = frozenset(
    {
        HostelApplicationStatus.SUBMITTED,
        HostelApplicationStatus.UNDER_REVIEW,
        HostelApplicationStatus.ADDITIONAL_INFO_REQUIRED,
    }
)
_APPROVED_STATUSES = frozenset(
    {
        HostelApplicationStatus.APPROVED,
        HostelApplicationStatus.ALLOCATION_OFFERED,
        HostelApplicationStatus.ACCEPTED,
    }
)
_WAITLIST_STATUSES = frozenset({HostelApplicationStatus.WAITLISTED})
_ALLOCATION_QUEUE_STATUSES = _APPROVED_STATUSES


def pick_academic_year_label(apps: list[HostelApplication]) -> str | None:
    if not apps:
        return None
    counts = Counter(a.academic_year_label for a in apps if a.academic_year_label)
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def _academic_year_start(academic_year_label: str | None) -> int | None:
    if not academic_year_label:
        return None
    match = re.search(r"(20\d{2})", academic_year_label)
    return int(match.group(1)) if match else None


def _batch_start_year(batch_label: str | None) -> int | None:
    if not batch_label:
        return None
    match = re.search(r"(20\d{2})", batch_label)
    return int(match.group(1)) if match else None


def study_year_ordinal(batch_label: str | None, academic_year_label: str | None) -> str:
    batch_start = _batch_start_year(batch_label)
    ay_start = _academic_year_start(academic_year_label)
    if batch_start is None or ay_start is None:
        return "—"
    year = max(1, min(6, ay_start - batch_start + 1))
    if year == 1:
        return "1st"
    if year == 2:
        return "2nd"
    if year == 3:
        return "3rd"
    return f"{year}th"


def distance_label(payload: dict | None) -> str:
    if not payload:
        return "—"
    for key in ("distance_km", "distance", "home_distance_km"):
        raw = payload.get(key)
        if raw is None or raw == "":
            continue
        try:
            value = float(raw)
            if value == int(value):
                return f"{int(value)} km"
            return f"{value:.1f} km"
        except (TypeError, ValueError):
            continue
    return "—"


def application_bucket(status: HostelApplicationStatus) -> str:
    if status in _PENDING_STATUSES:
        return "pending"
    if status in _APPROVED_STATUSES:
        return "approved"
    if status in _WAITLIST_STATUSES:
        return "waitlisted"
    return "other"


def application_display_status(status: HostelApplicationStatus) -> tuple[str, str]:
    if status in _PENDING_STATUSES:
        return "Pending", "warning"
    if status in _APPROVED_STATUSES:
        return "Approved", "success"
    if status in _WAITLIST_STATUSES:
        return "Waitlisted", "muted"
    if status == HostelApplicationStatus.REJECTED:
        return "Rejected", "error"
    key = status.value.replace("_", " ")
    return key.title(), "muted"


def submitted_short(when: datetime | None) -> str:
    if not when:
        return "—"
    return when.strftime("%d %b")


def preference_label(
    *,
    room_type: str | None,
    hostel_name: str | None,
) -> str:
    parts: list[str] = []
    if room_type:
        parts.append(room_type.replace("_", " ").title())
    if hostel_name:
        parts.append(hostel_name)
    return ", ".join(parts) if parts else "—"


def conflicts_in_eligibility(eligibility_result: dict | None) -> bool:
    if not eligibility_result:
        return False
    issues = eligibility_result.get("issues") or []
    if not isinstance(issues, list):
        return False
    for issue in issues:
        text = str(issue).lower()
        if "gender" in text or "year" in text or "academic" in text:
            return True
    return False


def filter_apps_for_year(apps: list[HostelApplication], year_label: str | None) -> list[HostelApplication]:
    if not year_label:
        return list(apps)
    return [a for a in apps if a.academic_year_label == year_label]


def allocation_queue_apps(apps: list[HostelApplication], year_label: str | None) -> list[HostelApplication]:
    scoped = filter_apps_for_year(apps, year_label)
    return [a for a in scoped if a.status in _ALLOCATION_QUEUE_STATUSES]


def format_allocated_bed(*, block: str | None, room: str | None, bed: str | None) -> str:
    left = "—"
    if block and room:
        left = f"{block}-{room}"
    elif room:
        left = room
    elif block:
        left = block
    if bed and bed != "—":
        return f"{left} / {bed}"
    return left if left != "—" else "—"