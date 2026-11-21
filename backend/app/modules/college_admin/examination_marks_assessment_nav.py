"""Shared sub-navigation for marks & assessment (CA 09.08)."""

from app.modules.college_admin.schemas import ExaminationRegistrationSubNavItem

_SUB_NAV: list[ExaminationRegistrationSubNavItem] = [
    ExaminationRegistrationSubNavItem(
        key="marks_entry",
        label="Marks entry",
        href="/college-admin/examinations/marks-entry-management",
        active_slug="marks-entry-management",
    ),
    ExaminationRegistrationSubNavItem(
        key="assessment",
        label="Assessment pattern",
        href="/college-admin/examinations/internal-external-assessment",
        active_slug="internal-external-assessment",
    ),
]


def examination_marks_assessment_sub_nav(active_slug: str) -> list[ExaminationRegistrationSubNavItem]:
    return [
        item.model_copy(update={"active": item.active_slug == active_slug})
        for item in _SUB_NAV
    ]