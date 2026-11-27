"""LMS section sub-navigation API."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.modules.college_admin.lms_section_sub_nav import lms_section_sub_nav_for_path
from app.modules.college_admin.schemas import LmsSectionSubNavRead


async def get_lms_section_sub_nav(scope: AccessScope, *, path: str) -> LmsSectionSubNavRead:
    authorize(scope, Permission.LMS_ADMIN_READ)
    return lms_section_sub_nav_for_path(path)