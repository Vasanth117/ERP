"""Pill sub-navigation within grouped library section tabs (CA 12)."""

from __future__ import annotations

from app.modules.college_admin.schemas import LibrarySectionSubNavItem, LibrarySectionSubNavRead

_SECTION_GROUPS: tuple[tuple[str, tuple[tuple[str, str, str, str], ...]], ...] = (
    (
        "branches_catalogue",
        (
            ("branches", "Branches", "/college-admin/library/library-branch-management", "branches"),
            ("catalogue", "Book catalogue", "/college-admin/library/book-catalogue", "catalogue"),
        ),
    ),
    (
        "inventory_acquisition",
        (
            ("inventory", "Book inventory", "/college-admin/library/book-inventory", "inventory"),
            ("acquisition", "Book acquisition", "/college-admin/library/book-acquisition", "acquisition"),
        ),
    ),
    (
        "circulation",
        (
            ("issue_return", "Issue & return", "/college-admin/library/book-issue-return-management", "issue_return"),
            ("reservations", "Reservations", "/college-admin/library/reservation-management", "reservations"),
        ),
    ),
    (
        "members_fines",
        (
            ("members", "Members", "/college-admin/library/library-member-management", "members"),
            ("fines", "Fines", "/college-admin/library/fine-management", "fines"),
            ("lost_damaged", "Lost & damaged", "/college-admin/library/lost-damaged-books", "lost_damaged"),
        ),
    ),
    (
        "reports_settings",
        (
            ("reports", "Library reports", "/college-admin/library/library-reports", "reports"),
            ("settings", "Settings", "/college-admin/library/library-settings", "settings"),
        ),
    ),
)

_EXTRA_PATHS: dict[str, str] = {
    "/college-admin/library/library-circulation": "circulation",
}


def _normalize_path(path: str) -> str:
    base = (path or "").split("?")[0].rstrip("/")
    if not base:
        return ""
    return base


def _section_key_for_path(path: str) -> str | None:
    normalized = _normalize_path(path)
    if not normalized:
        return None
    if normalized in _EXTRA_PATHS:
        return _EXTRA_PATHS[normalized]
    for section_key, pages in _SECTION_GROUPS:
        for _key, _label, href, _icon in pages:
            if normalized == href or normalized.startswith(f"{href}/"):
                return section_key
    return None


def library_section_sub_nav_for_path(path: str) -> LibrarySectionSubNavRead:
    section_key = _section_key_for_path(path)
    normalized = _normalize_path(path)
    items: list[LibrarySectionSubNavItem] = []
    if section_key:
        for group_key, pages in _SECTION_GROUPS:
            if group_key != section_key:
                continue
            for key, label, href, icon_key in pages:
                active = normalized == href or normalized.startswith(f"{href}/")
                items.append(
                    LibrarySectionSubNavItem(key=key, label=label, href=href, icon_key=icon_key, active=active),
                )
            break
    return LibrarySectionSubNavRead(path=normalized, section_key=section_key, items=items)