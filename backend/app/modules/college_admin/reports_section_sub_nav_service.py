"""Reports section sub-navigation API."""

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.modules.college_admin.reports_section_sub_nav import reports_section_sub_nav_for_path
from app.modules.college_admin.schemas import ReportsSectionSubNavRead


async def get_reports_section_sub_nav(scope: AccessScope, *, path: str) -> ReportsSectionSubNavRead:
    authorize(scope, Permission.REPORTS_ADMIN_READ)
    return reports_section_sub_nav_for_path(path)