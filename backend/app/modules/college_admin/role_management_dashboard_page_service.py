"""Role management dashboard (CA 03 — roles)."""

from __future__ import annotations

import math
from collections import defaultdict
from datetime import timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE

from app.authorization.permissions import Permission, permissions_for_role
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import as_utc_aware, utcnow
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import InstitutionRole, InstitutionRoleAssignment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    RoleManagementDashboardPageRead,
    RoleManagementTableRow,
    UserDashboardKpi,
)
from app.modules.college_admin.rbac_service import seed_tenant_permission_catalog

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 10

_PRIVILEGED_BASE_ROLES = {
    Role.COLLEGE_ADMIN,
    Role.DEPARTMENT_ADMIN,
    Role.FINANCE_STAFF,
    Role.ACCOUNTS_STAFF,
    Role.EXAMINATION_CELL,
}

_CATEGORY_LABELS: dict[str, str] = {
    "college": "Students",
    "student": "Students",
    "faculty": "Faculty",
    "attendance": "Attendance",
    "examination": "Examinations",
    "finance": "Finance",
    "accounts": "Accounts",
    "hr": "HR",
    "hostel": "Hostel",
    "library": "Library",
    "lms": "LMS",
    "institution": "Institution",
}


def _format_changed(when) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("%d %b %Y")


def _modules_label(role: InstitutionRole) -> str:
    labels: list[str] = []
    seen: set[str] = set()
    perms = list(role.granted_permissions)
    if not perms and role.is_system:
        perms = [p.value for p in permissions_for_role(role.base_role)]
    if role.base_role == Role.COLLEGE_ADMIN and role.is_system and not role.granted_permissions:
        return "All modules"
    for code in perms:
        prefix = code.split(":")[0] if ":" in code else "general"
        friendly = _CATEGORY_LABELS.get(prefix, prefix.replace("_", " ").title())
        if friendly.lower() not in seen:
            seen.add(friendly.lower())
            labels.append(friendly)
    if not labels:
        if role.base_role == Role.FACULTY:
            return "Attendance, LMS, marks"
        if role.base_role == Role.STUDENT:
            return "Student portal"
        return "—"
    if len(labels) > 4:
        return ", ".join(labels[:3]) + ", …"
    return ", ".join(labels)


def _is_privileged_role(role: InstitutionRole) -> bool:
    if role.base_role in _PRIVILEGED_BASE_ROLES:
        return True
    for code in role.granted_permissions:
        if any(k in code for k in ("finance", "examination", "privileged", "college_admin")):
            return True
    return False


async def get_role_management_dashboard_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> RoleManagementDashboardPageRead:
    authorize(scope, Permission.INSTITUTION_ROLE_READ)
    tenant_id = require_college_tenant_scope(scope)
    await seed_tenant_permission_catalog(tenant_id)

    all_roles = await InstitutionRole.find(Eq(InstitutionRole.tenant_id, tenant_id)).sort("+name").to_list()
    system_count = sum(1 for r in all_roles if r.is_system)
    custom_count = len(all_roles) - system_count

    assignments = await InstitutionRoleAssignment.find(
        Eq(InstitutionRoleAssignment.tenant_id, tenant_id),
        Eq(InstitutionRoleAssignment.revoked_at, None),
    ).to_list()
    users_per_role: dict[PydanticObjectId, int] = defaultdict(int)
    assigned_user_ids: set[PydanticObjectId] = set()
    for row in assignments:
        users_per_role[row.institution_role_id] += 1
        assigned_user_ids.add(row.user_id)

    total_users = await User.find(Eq(User.tenant_id, tenant_id)).count()
    assigned_pct = int(round(100 * len(assigned_user_ids) / total_users)) if total_users else 0

    privileged_count = sum(1 for r in all_roles if _is_privileged_role(r))

    cutoff = utcnow() - timedelta(days=30)
    changed_30d = sum(1 for r in all_roles if r.updated_at >= cutoff)

    kpis = [
        UserDashboardKpi(
            key="roles",
            label="Roles",
            value=f"{len(all_roles):,}",
            hint_line=f"{system_count} system · {custom_count} custom",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="users_with_roles",
            label="Users with roles",
            value=f"{len(assigned_user_ids):,}",
            hint_line=f"{assigned_pct}% assigned",
            hint_tone="success" if assigned_pct >= 80 else "muted",
        ),
        UserDashboardKpi(
            key="privileged",
            label="Privileged roles",
            value=str(privileged_count),
            hint_line="Finance, exams, admin",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="changed",
            label="Roles changed (30 days)",
            value=str(changed_30d),
            hint_line="From role update records",
            hint_tone="muted",
        ),
    ]

    total = len(all_roles)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = all_roles[start : start + _PAGE_SIZE]

    table_rows: list[RoleManagementTableRow] = []
    for role in page_slice:
        status_label = "Active" if role.is_active else "Draft"
        status_tone = "success" if role.is_active else "warning"
        table_rows.append(
            RoleManagementTableRow(
                role_id=str(role.id),
                role_name=role.name,
                role_code=role.role_code,
                type_label="System" if role.is_system else "Custom",
                users_count=users_per_role.get(role.id, 0),
                modules_label=_modules_label(role),
                last_changed_label=_format_changed(role.updated_at),
                status_code="active" if role.is_active else "draft",
                status_label=status_label,
                status_tone=status_tone,
                detail_href=f"/college-admin/users/create-edit-role?roleId={role.id}",
            ),
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]
    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return RoleManagementDashboardPageRead(
        page_title="Role Management Dashboard",
        page_subtitle="System and custom roles available in the college",
        compare_roles_label="Compare roles",
        compare_roles_href="/college-admin/users/permission-management",
        create_role_label="Create role",
        create_role_href="/college-admin/users/create-edit-role",
        kpis=kpis,
        roles_section_title="Roles",
        roles_count_label=f"{total:,} roles" if total else "0 roles",
        table_headers=["Role", "Type", "Users", "Modules", "Last changed", "Status"],
        roles=table_rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=page_numbers,
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institution role records · User counts from active assignments · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )