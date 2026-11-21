"""Shared sub-navigation for halls & invigilation (CA 09.07)."""

from app.modules.college_admin.schemas import ExaminationRegistrationSubNavItem

_SUB_NAV: list[ExaminationRegistrationSubNavItem] = [
    ExaminationRegistrationSubNavItem(
        key="seating",
        label="Halls & seating",
        href="/college-admin/examinations/examination-hall-seating-management",
        active_slug="examination-hall-seating-management",
    ),
    ExaminationRegistrationSubNavItem(
        key="invigilation",
        label="Invigilation",
        href="/college-admin/examinations/invigilator-allocation",
        active_slug="invigilator-allocation",
    ),
]


def examination_halls_invigilation_sub_nav(active_slug: str) -> list[ExaminationRegistrationSubNavItem]:
    return [
        item.model_copy(update={"active": item.active_slug == active_slug})
        for item in _SUB_NAV
    ]