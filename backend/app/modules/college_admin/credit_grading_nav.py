"""Sub-navigation for CA 05 credits & grading screens."""

from app.modules.college_admin.schemas import YearsSemestersSubNavItem

_CREDIT_HREF = "/college-admin/academics/credit-configuration"
_GRADING_HREF = "/college-admin/academics/grading-system-configuration"


def credit_grading_sub_nav(*, active: str) -> list[YearsSemestersSubNavItem]:
    return [
        YearsSemestersSubNavItem(
            key="credit",
            label="Credit configuration",
            href=_CREDIT_HREF,
            active=active == "credit",
        ),
        YearsSemestersSubNavItem(
            key="grading",
            label="Grading system",
            href=_GRADING_HREF,
            active=active == "grading",
        ),
    ]