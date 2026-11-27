"""Pill sub-navigation within grouped Reports & Analytics section tabs (CA 16)."""

from __future__ import annotations

from app.modules.college_admin.schemas import ReportsSectionSubNavItem, ReportsSectionSubNavRead

_SECTION_GROUPS: tuple[tuple[str, tuple[tuple[str, str, str, str], ...]], ...] = (
    (
        "academic",
        (
            ("students", "Student reports", "/college-admin/reports/student-reports", "students"),
            ("department", "Departments", "/college-admin/reports/department-reports", "department"),
            ("academic_performance", "Academic performance", "/college-admin/reports/academic-performance-reports", "performance"),
            ("attendance", "Attendance", "/college-admin/reports/attendance-reports", "attendance"),
            ("examination", "Examinations", "/college-admin/reports/examination-reports", "exam"),
        ),
    ),
    (
        "people",
        (
            ("faculty", "Faculty & employees", "/college-admin/reports/faculty-employee-reports", "faculty"),
            ("hr", "HR reports", "/college-admin/reports/hr-reports", "hr"),
        ),
    ),
    (
        "operations",
        (
            ("finance", "Finance", "/college-admin/reports/finance-reports", "finance"),
            ("library", "Library", "/college-admin/reports/library-reports", "library"),
            ("hostel", "Hostel", "/college-admin/reports/hostel-reports", "hostel"),
        ),
    ),
    (
        "custom_scheduled",
        (
            ("custom", "Custom builder", "/college-admin/reports/custom-report-builder", "custom"),
            ("scheduled", "Scheduled reports", "/college-admin/reports/scheduled-reports", "scheduled"),
            ("exports", "Export history", "/college-admin/reports/export-download-history", "exports"),
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


def reports_section_sub_nav_for_path(path: str) -> ReportsSectionSubNavRead:
    section_key = _section_key_for_path(path)
    normalized = _normalize_path(path)
    items: list[ReportsSectionSubNavItem] = []
    if section_key:
        for group_key, pages in _SECTION_GROUPS:
            if group_key != section_key:
                continue
            for key, label, href, icon_key in pages:
                active = normalized == href or normalized.startswith(f"{href}/")
                items.append(
                    ReportsSectionSubNavItem(key=key, label=label, href=href, icon_key=icon_key, active=active),
                )
            break
    return ReportsSectionSubNavRead(path=normalized, section_key=section_key, items=items)