"""Pill sub-navigation within grouped communication section tabs (CA 14)."""

from __future__ import annotations

from app.modules.college_admin.schemas import CommunicationSectionSubNavItem, CommunicationSectionSubNavRead

_SECTION_GROUPS: tuple[tuple[str, tuple[tuple[str, str, str, str], ...]], ...] = (
    (
        "announcements",
        (
            ("list", "Announcements", "/college-admin/communication/announcements-management", "announcements"),
            ("create", "Create announcement", "/college-admin/communication/create-announcement", "create"),
        ),
    ),
    (
        "audience",
        (
            ("students", "Students", "/college-admin/communication/student-notifications", "students"),
            ("faculty", "Faculty", "/college-admin/communication/faculty-notifications", "faculty"),
            ("parents", "Parents", "/college-admin/communication/parent-communication", "parents"),
        ),
    ),
    (
        "channels",
        (
            ("email", "Email", "/college-admin/communication/email-communication", "email"),
            ("sms", "SMS", "/college-admin/communication/sms-communication", "sms"),
            ("whatsapp", "WhatsApp", "/college-admin/communication/whatsapp-communication", "whatsapp"),
        ),
    ),
    (
        "templates_scheduling",
        (
            ("templates", "Templates", "/college-admin/communication/communication-templates", "templates"),
            ("scheduled", "Scheduled", "/college-admin/communication/scheduled-messages", "scheduled"),
        ),
    ),
    (
        "delivery_history",
        (
            ("delivery", "Delivery status", "/college-admin/communication/delivery-status-monitoring", "delivery"),
            ("history", "History", "/college-admin/communication/communication-history", "history"),
        ),
    ),
)


def _normalize_path(path: str) -> str:
    base = (path or "").split("?")[0].rstrip("/")
    return base if base else ""


def _section_key_for_path(path: str) -> str | None:
    normalized = _normalize_path(path)
    if not normalized:
        return None
    for section_key, pages in _SECTION_GROUPS:
        for _key, _label, href, _icon in pages:
            if normalized == href or normalized.startswith(f"{href}/"):
                return section_key
    return None


def communication_section_sub_nav_for_path(path: str) -> CommunicationSectionSubNavRead:
    section_key = _section_key_for_path(path)
    normalized = _normalize_path(path)
    items: list[CommunicationSectionSubNavItem] = []
    if section_key:
        for group_key, pages in _SECTION_GROUPS:
            if group_key != section_key:
                continue
            for key, label, href, icon_key in pages:
                active = normalized == href or normalized.startswith(f"{href}/")
                items.append(
                    CommunicationSectionSubNavItem(key=key, label=label, href=href, icon_key=icon_key, active=active),
                )
            break
    return CommunicationSectionSubNavRead(path=normalized, section_key=section_key, items=items)