"""Shared sub-navigation for CA 05 course & curriculum screens."""

from app.modules.college_admin.schemas import YearsSemestersSubNavItem

_COURSE_CONFIG_HREF = "/college-admin/academics/course-configuration"
_CURRICULUM_HREF = "/college-admin/academics/curriculum-management"
_SUBJECTS_HREF = "/college-admin/academics/subject-management"


def course_curriculum_sub_nav(*, active: str) -> list[YearsSemestersSubNavItem]:
    return [
        YearsSemestersSubNavItem(
            key="course_configuration",
            label="Course configuration",
            href=_COURSE_CONFIG_HREF,
            active=active == "course_configuration",
        ),
        YearsSemestersSubNavItem(
            key="curriculum",
            label="Curriculum management",
            href=_CURRICULUM_HREF,
            active=active == "curriculum",
        ),
        YearsSemestersSubNavItem(
            key="subjects",
            label="Subject management",
            href=_SUBJECTS_HREF,
            active=active == "subjects",
        ),
    ]


def new_course_configuration_href() -> str:
    return f"{_COURSE_CONFIG_HREF}?mode=create"


def course_configuration_href(course_id: str) -> str:
    return f"{_COURSE_CONFIG_HREF}?course_id={course_id}"