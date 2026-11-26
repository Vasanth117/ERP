"""Shared benefits & performance section navigation (CA 11.11–11.12)."""

from app.modules.college_admin.schemas import HrRecruitmentSubNavItem

HR_BENEFITS_PERFORMANCE_SUB_NAV: list[HrRecruitmentSubNavItem] = [
    HrRecruitmentSubNavItem(
        key="benefits-claims",
        label="Employee benefits & claims",
        href="/college-admin/hr/employee-benefits-claims",
    ),
    HrRecruitmentSubNavItem(
        key="performance",
        label="Performance management",
        href="/college-admin/hr/performance-management",
    ),
]