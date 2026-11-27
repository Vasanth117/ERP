"""Attendance section sub-navigation API."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.modules.college_admin.attendance_section_sub_nav import attendance_section_sub_nav_for_path
from app.modules.college_admin.schemas import AttendanceSectionSubNavRead


async def get_attendance_section_sub_nav(scope: AccessScope, *, path: str) -> AttendanceSectionSubNavRead:
    authorize(scope, Permission.ATTENDANCE_ADMIN_READ)
    return attendance_section_sub_nav_for_path(path)