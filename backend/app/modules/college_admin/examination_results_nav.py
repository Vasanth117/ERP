"""Shared sub-navigation for examination results (CA 09.09)."""

from app.modules.college_admin.schemas import ExaminationRegistrationSubNavItem

_SUB_NAV: list[ExaminationRegistrationSubNavItem] = [
    ExaminationRegistrationSubNavItem(
        key="processing",
        label="Processing",
        href="/college-admin/examinations/result-processing",
        active_slug="result-processing",
    ),
    ExaminationRegistrationSubNavItem(
        key="approval",
        label="Approval",
        href="/college-admin/examinations/result-approval",
        active_slug="result-approval",
    ),
    ExaminationRegistrationSubNavItem(
        key="publication",
        label="Publication",
        href="/college-admin/examinations/result-publication",
        active_slug="result-publication",
    ),
]


def examination_results_sub_nav(active_slug: str) -> list[ExaminationRegistrationSubNavItem]:
    return [
        item.model_copy(update={"active": item.active_slug == active_slug})
        for item in _SUB_NAV
    ]