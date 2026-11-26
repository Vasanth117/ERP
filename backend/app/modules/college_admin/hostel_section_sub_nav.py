"""Pill sub-navigation within grouped hostel section tabs (CA 13)."""

from __future__ import annotations

from app.modules.college_admin.schemas import HostelSectionSubNavItem, HostelSectionSubNavRead

_SECTION_GROUPS: tuple[tuple[str, tuple[tuple[str, str, str, str], ...]], ...] = (
    (
        "buildings_rooms",
        (
            ("buildings", "Buildings", "/college-admin/hostel/hostel-building-management", "buildings"),
            ("rooms", "Rooms", "/college-admin/hostel/room-management", "rooms"),
        ),
    ),
    (
        "admissions_allocation",
        (
            ("applications", "Applications", "/college-admin/hostel/hostel-admission-applications", "applications"),
            ("bed_allocation", "Bed allocation", "/college-admin/hostel/bed-allocation", "bed_allocation"),
        ),
    ),
    (
        "residents",
        (
            ("residents", "Residents", "/college-admin/hostel/resident-management", "residents"),
            ("check_in", "Check-in / checkout", "/college-admin/hostel/hostel-check-in-checkout", "check_in"),
        ),
    ),
    (
        "fees_mess",
        (
            ("fees", "Hostel fees", "/college-admin/hostel/hostel-fee-management", "fees"),
            ("mess", "Mess", "/college-admin/hostel/mess-management", "mess"),
        ),
    ),
    (
        "visitors_outpass",
        (
            ("visitors", "Visitors", "/college-admin/hostel/visitor-management", "visitors"),
            ("outpass", "Leave & outpass", "/college-admin/hostel/leave-outpass-approval", "outpass"),
        ),
    ),
    (
        "maintenance_incidents",
        (
            ("maintenance", "Maintenance", "/college-admin/hostel/maintenance-complaints", "maintenance"),
            ("incidents", "Incidents", "/college-admin/hostel/hostel-incident-management", "incidents"),
        ),
    ),
    (
        "reports_settings",
        (
            ("reports", "Hostel reports", "/college-admin/hostel/hostel-reports", "reports"),
            ("settings", "Settings", "/college-admin/hostel/hostel-settings", "settings"),
        ),
    ),
)


def _normalize_path(path: str) -> str:
    base = (path or "").split("?")[0].rstrip("/")
    if not base:
        return ""
    return base


def _section_key_for_path(path: str) -> str | None:
    normalized = _normalize_path(path)
    if not normalized:
        return None
    for section_key, pages in _SECTION_GROUPS:
        for _key, _label, href, _icon in pages:
            if normalized == href or normalized.startswith(f"{href}/"):
                return section_key
    return None


def hostel_section_sub_nav_for_path(path: str) -> HostelSectionSubNavRead:
    section_key = _section_key_for_path(path)
    normalized = _normalize_path(path)
    items: list[HostelSectionSubNavItem] = []
    if section_key:
        for group_key, pages in _SECTION_GROUPS:
            if group_key != section_key:
                continue
            for key, label, href, icon_key in pages:
                active = normalized == href or normalized.startswith(f"{href}/")
                items.append(
                    HostelSectionSubNavItem(key=key, label=label, href=href, icon_key=icon_key, active=active),
                )
            break
    return HostelSectionSubNavRead(path=normalized, section_key=section_key, items=items)