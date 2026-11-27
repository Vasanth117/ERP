"""Pill sub-navigation within grouped LMS section tabs (CA 15)."""

from __future__ import annotations

from app.modules.college_admin.schemas import LmsSectionSubNavItem, LmsSectionSubNavRead

_SECTION_GROUPS: tuple[tuple[str, tuple[tuple[str, str, str, str], ...]], ...] = (
    (
        "courses_mapping",
        (
            ("courses", "Courses", "/college-admin/lms/course-management", "courses"),
            ("mapping", "Subject mapping", "/college-admin/lms/subject-course-mapping", "mapping"),
        ),
    ),
    (
        "content",
        (
            ("materials", "Learning materials", "/college-admin/lms/learning-material-management", "materials"),
            ("video", "Video lectures", "/college-admin/lms/video-lecture-management", "video"),
            ("units", "Units & chapters", "/college-admin/lms/unit-chapter-management", "units"),
        ),
    ),
    (
        "assessments",
        (
            ("assignments", "Assignments", "/college-admin/lms/assignment-management", "assignments"),
            ("quizzes", "Quizzes", "/college-admin/lms/quiz-management", "quizzes"),
            ("assessments", "Assessments", "/college-admin/lms/assessment-management", "assessments"),
        ),
    ),
    (
        "progress_faculty",
        (
            ("progress", "Student progress", "/college-admin/lms/student-learning-progress", "progress"),
            ("faculty", "Faculty content", "/college-admin/lms/faculty-content-management", "faculty"),
        ),
    ),
    (
        "reports_settings",
        (
            ("reports", "LMS reports", "/college-admin/lms/lms-reports", "reports"),
            ("settings", "Settings", "/college-admin/lms/lms-settings", "settings"),
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


def lms_section_sub_nav_for_path(path: str) -> LmsSectionSubNavRead:
    section_key = _section_key_for_path(path)
    normalized = _normalize_path(path)
    items: list[LmsSectionSubNavItem] = []
    if section_key:
        for group_key, pages in _SECTION_GROUPS:
            if group_key != section_key:
                continue
            for key, label, href, icon_key in pages:
                active = normalized == href or normalized.startswith(f"{href}/")
                items.append(
                    LmsSectionSubNavItem(key=key, label=label, href=href, icon_key=icon_key, active=active),
                )
            break
    return LmsSectionSubNavRead(path=normalized, section_key=section_key, items=items)