"""Shared reports & settings section navigation (CA 11.13–11.14)."""

from app.modules.college_admin.schemas import HrRecruitmentSubNavItem

HR_REPORTS_SETTINGS_SUB_NAV: list[HrRecruitmentSubNavItem] = [
    HrRecruitmentSubNavItem(
        key="hr-reports",
        label="HR reports",
        href="/college-admin/hr/hr-reports",
    ),
    HrRecruitmentSubNavItem(
        key="settings-policies",
        label="HR settings & policies",
        href="/college-admin/hr/hr-settings-policies",
    ),
]