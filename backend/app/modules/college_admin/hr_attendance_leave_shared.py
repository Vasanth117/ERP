"""Shared attendance & leave section navigation (CA 11 — Attendance & leave)."""

from app.modules.college_admin.schemas import HrRecruitmentSubNavItem

HR_ATTENDANCE_LEAVE_SUB_NAV: list[HrRecruitmentSubNavItem] = [
    HrRecruitmentSubNavItem(
        key="employee-attendance",
        label="Employee attendance",
        href="/college-admin/hr/employee-attendance",
    ),
    HrRecruitmentSubNavItem(
        key="leave-management",
        label="Leave management",
        href="/college-admin/hr/leave-management",
    ),
]