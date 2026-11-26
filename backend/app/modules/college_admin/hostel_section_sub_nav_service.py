"""Hostel section sub-navigation API."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.modules.college_admin.hostel_section_sub_nav import hostel_section_sub_nav_for_path
from app.modules.college_admin.schemas import HostelSectionSubNavRead


async def get_hostel_section_sub_nav(scope: AccessScope, *, path: str) -> HostelSectionSubNavRead:
    authorize(scope, Permission.HOSTEL_ADMIN_READ)
    return hostel_section_sub_nav_for_path(path)