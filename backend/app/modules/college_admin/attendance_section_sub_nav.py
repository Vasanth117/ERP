"""Pill sub-navigation within grouped Attendance section tabs (CA 08)."""

from __future__ import annotations

from app.modules.college_admin.schemas import AttendanceSectionSubNavItem, AttendanceSectionSubNavRead

_SECTION_GROUPS: tuple[tuple[str, tuple[tuple[str, str, str, str], ...]], ...] = (
    (
        "student_attendance",
        (
            (
                "overview",
                "Student attendance overview",
                "/college-admin/attendance/student-attendance-overview",
                "students",
            ),
            (
                "subject_wise",
                "Subject-wise attendance",
                "/college-admin/attendance/subject-wise-attendance",
                "subjects",
            ),
            (
                "department_wise",
                "Department-wise attendance",
                "/college-admin/attendance/department-wise-attendance",
                "department",
            ),
        ),
    ),
    (
        "configuration",
        (
            (
                "settings",
                "Current configuration",
                "/college-admin/attendance/attendance-configuration",
                "settings",
            ),
            (
                "rules_policies",
                "Rules & policies",
                "/college-admin/attendance/attendance-rules-policies",
                "list",
            ),
        ),
    ),
    (
        "monitoring",
        (
            (
                "monitoring",
                "Attendance monitoring",
                "/college-admin/attendance/attendance-monitoring",
                "attendance",
            ),
            (
                "missing_submissions",
                "Missing submissions",
                "/college-admin/attendance/missing-submissions",
                "list",
            ),
            (
                "shortage_report",
                "Shortage report",
                "/college-admin/attendance/attendance-shortage-report",
                "reports",
            ),
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


def attendance_section_sub_nav_for_path(path: str) -> AttendanceSectionSubNavRead:
    section_key = _section_key_for_path(path)
    normalized = _normalize_path(path)
    items: list[AttendanceSectionSubNavItem] = []
    if section_key:
        for group_key, pages in _SECTION_GROUPS:
            if group_key != section_key:
                continue
            for key, label, href, icon_key in pages:
                active = normalized == href or normalized.startswith(f"{href}/")
                items.append(
                    AttendanceSectionSubNavItem(
                        key=key,
                        label=label,
                        href=href,
                        icon_key=icon_key,
                        active=active,
                    ),
                )
            break
    return AttendanceSectionSubNavRead(path=normalized, section_key=section_key, items=items)