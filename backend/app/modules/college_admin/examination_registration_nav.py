"""Shared sub-navigation for examination registration & eligibility (CA 09.04)."""

from app.modules.college_admin.schemas import ExaminationRegistrationSubNavItem

_SUB_NAV: list[ExaminationRegistrationSubNavItem] = [
    ExaminationRegistrationSubNavItem(
        key="registrations",
        label="Registrations",
        href="/college-admin/examinations/exam-registration-management",
        active_slug="exam-registration-management",
    ),
    ExaminationRegistrationSubNavItem(
        key="eligibility",
        label="Eligibility",
        href="/college-admin/examinations/student-exam-eligibility",
        active_slug="student-exam-eligibility",
    ),
    ExaminationRegistrationSubNavItem(
        key="hall_tickets",
        label="Hall tickets",
        href="/college-admin/examinations/hall-ticket-administration",
        active_slug="hall-ticket-administration",
    ),
]


def examination_registration_sub_nav(active_slug: str) -> list[ExaminationRegistrationSubNavItem]:
    return [
        item.model_copy(update={"active": item.active_slug == active_slug})
        for item in _SUB_NAV
    ]