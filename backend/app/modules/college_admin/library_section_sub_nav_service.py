"""Library section sub-navigation API."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.modules.college_admin.library_section_sub_nav import library_section_sub_nav_for_path
from app.modules.college_admin.schemas import LibrarySectionSubNavRead


async def get_library_section_sub_nav(scope: AccessScope, *, path: str) -> LibrarySectionSubNavRead:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    return library_section_sub_nav_for_path(path)