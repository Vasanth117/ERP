"""Shared sub-navigation for revaluation & supplementary (CA 09.10)."""

from app.modules.college_admin.schemas import ExaminationRegistrationSubNavItem

_SUB_NAV: list[ExaminationRegistrationSubNavItem] = [
    ExaminationRegistrationSubNavItem(
        key="revaluation",
        label="Revaluation",
        href="/college-admin/examinations/revaluation-management",
        active_slug="revaluation-management",
    ),
    ExaminationRegistrationSubNavItem(
        key="supplementary",
        label="Supplementary",
        href="/college-admin/examinations/supplementary-examination-management",
        active_slug="supplementary-examination-management",
    ),
]


def examination_revaluation_supplementary_sub_nav(active_slug: str) -> list[ExaminationRegistrationSubNavItem]:
    return [
        item.model_copy(update={"active": item.active_slug == active_slug})
        for item in _SUB_NAV
    ]