"""Shared sub-navigation for CA 05 years & semesters screens."""

from app.modules.college_admin.schemas import YearsSemestersSubNavItem

_YEAR_HREF = "/college-admin/academics/academic-year-management"
_SEMESTER_HREF = "/college-admin/academics/semester-management"
_CALENDAR_HREF = "/college-admin/academics/academic-calendar-configuration"


def years_semesters_sub_nav(*, active: str) -> list[YearsSemestersSubNavItem]:
    return [
        YearsSemestersSubNavItem(
            key="years",
            label="Years",
            href=_YEAR_HREF,
            active=active == "years",
        ),
        YearsSemestersSubNavItem(
            key="semesters",
            label="Semesters",
            href=_SEMESTER_HREF,
            active=active == "semesters",
        ),
        YearsSemestersSubNavItem(
            key="calendar",
            label="Academic calendar",
            href=_CALENDAR_HREF,
            active=active == "calendar",
        ),
    ]