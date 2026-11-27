"""Communication section sub-navigation API."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.modules.college_admin.communication_section_sub_nav import communication_section_sub_nav_for_path
from app.modules.college_admin.schemas import CommunicationSectionSubNavRead


async def get_communication_section_sub_nav(scope: AccessScope, *, path: str) -> CommunicationSectionSubNavRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    return communication_section_sub_nav_for_path(path)