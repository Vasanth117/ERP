"""All users list page (CA 03.02)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import as_utc_aware, utcnow
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.identity_models import (
    InstitutionAccountStatus,
    InstitutionUser,
    InstitutionUserInvitation,
    InvitationStatus,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    UserAllUsersListPageRead,
    UserListFilterOption,
    UserListTableRow,
)
from app.modules.college_admin.security_admin_models import InstitutionSecurityPolicy
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Department

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 10

_ROLE_DISPLAY: dict[Role, str] = {
    Role.DEPARTMENT_ADMIN: "Dept Admin",
    Role.FACULTY: "Faculty",
    Role.STUDENT: "Student",
    Role.LIBRARIAN: "Librarian",
    Role.ACCOUNTS_STAFF: "Accounts",
    Role.FINANCE_STAFF: "Accounts",
    Role.HOSTEL_ADMIN: "Hostel Admin",
    Role.EXAMINATION_CELL: "Exam Cell",
    Role.COLLEGE_ADMIN: "College Admin",
    Role.HR_STAFF: "HR staff",
}

_PRIVILEGED_MFA_ROLES = {
    Role.COLLEGE_ADMIN,
    Role.FINANCE_STAFF,
    Role.ACCOUNTS_STAFF,
    Role.HR_STAFF,
}


@dataclass
class _AccountListRow:
    user: User | None
    institution: InstitutionUser | None
    invite: InstitutionUserInvitation | None
    role_codes: list[str]
    public_id: str
    phone: str | None
    employee: EmployeeRecord | None
    sort_at: datetime


def _display_role(role: Role, institution_role_codes: list[str]) -> str:
    if institution_role_codes:
        return institution_role_codes[0].replace("_", " ").title()
    return _ROLE_DISPLAY.get(role, role.value.replace("_", " ").title())


def _status_presentation(status: InstitutionAccountStatus, invited: bool) -> tuple[str, str, str]:
    if invited or status == InstitutionAccountStatus.INVITED:
        return "invited", "Invited", "info"
    if status == InstitutionAccountStatus.SUSPENDED:
        return "suspended", "Suspended", "error"
    if status == InstitutionAccountStatus.DEACTIVATED:
        return "deactivated", "Deactivated", "muted"
    return "active", "Active", "success"


def _format_last_login(when: datetime | None) -> str:
    if when is None:
        return "—"
    local = as_utc_aware(when).astimezone(_IST)
    today = utcnow().astimezone(_IST).date()
    login_date = local.date()
    if login_date == today:
        return f"Today {local.strftime('%H:%M')}"
    if login_date == today - timedelta(days=1):
        return "Yesterday"
    return local.strftime("%d %b")


async def _role_codes_for_user(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> list[str]:
    from app.modules.college_admin.identity_models import InstitutionRole, InstitutionRoleAssignment

    assignments = await InstitutionRoleAssignment.find(
        {"tenant_id": tenant_id, "user_id": user_id, "revoked_at": None},
    ).to_list()
    codes: list[str] = []
    for row in assignments:
        role = await InstitutionRole.get(row.institution_role_id)
        if role and role.is_active:
            codes.append(role.role_code)
    return codes


def _resolve_public_id(
    user: User,
    student: StudentProfile | None,
    employee: EmployeeRecord | None,
) -> str:
    if student:
        for candidate in (student.roll_number, student.student_id, student.admission_number):
            if candidate:
                return candidate
    if employee and employee.employee_id:
        return employee.employee_id
    return f"USR-{str(user.id)[-8:].upper()}"


def _matches_search(
    user: User,
    *,
    public_id: str,
    phone: str | None,
    needle: str,
) -> bool:
    hay = " ".join(
        [
            user.full_name,
            user.email,
            public_id,
            phone or "",
            user.role.value,
        ],
    ).lower()
    return needle in hay


async def get_all_users_list_page(
    scope: AccessScope,
    *,
    page: int = 1,
    search: str | None = None,
    role_filter: str | None = None,
    department_id: str | None = None,
    status_filter: str | None = None,
) -> UserAllUsersListPageRead:
    authorize(scope, Permission.INSTITUTION_USER_READ)
    tenant_id = require_college_tenant_scope(scope)

    users = await User.find(Eq(User.tenant_id, tenant_id)).to_list()
    institution_rows = await InstitutionUser.find(Eq(InstitutionUser.tenant_id, tenant_id)).to_list()
    institution_by_user = {row.user_id: row for row in institution_rows}

    students = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    student_by_user = {row.user_id: row for row in students}

    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    employee_by_user = {row.user_id: row for row in employees}

    departments = await Department.find(Eq(Department.tenant_id, tenant_id)).to_list()
    dept_by_id = {d.id: d for d in departments}

    pending_invites = await InstitutionUserInvitation.find(
        Eq(InstitutionUserInvitation.tenant_id, tenant_id),
        Eq(InstitutionUserInvitation.status, InvitationStatus.PENDING),
    ).to_list()
    invited_emails = {inv.email.lower() for inv in pending_invites}

    policy = await InstitutionSecurityPolicy.find_one(
        Eq(InstitutionSecurityPolicy.tenant_id, tenant_id),
        Eq(InstitutionSecurityPolicy.policy_id, "default"),
    )
    require_mfa = policy.require_mfa_privileged if policy else False

    dept_filter_oid: PydanticObjectId | None = None
    if department_id:
        dept_filter_oid = PydanticObjectId(department_id)

    needle = (search or "").strip().lower()
    user_emails = {user.email.lower() for user in users}
    filtered: list[_AccountListRow] = []
    for user in users:
        if role_filter and user.role.value != role_filter:
            continue
        if dept_filter_oid is not None and user.department_id != dept_filter_oid:
            continue
        inst = institution_by_user.get(user.id)
        student = student_by_user.get(user.id)
        employee = employee_by_user.get(user.id)
        invited = user.email.lower() in invited_emails
        status = inst.account_status if inst else InstitutionAccountStatus.ACTIVE
        status_code, _, _ = _status_presentation(status, invited)
        if status_filter and status_code != status_filter:
            continue
        public_id = _resolve_public_id(user, student, employee)
        phone = student.contact_phone if student else None
        if needle and not _matches_search(user, public_id=public_id, phone=phone, needle=needle):
            continue
        codes = await _role_codes_for_user(tenant_id, user.id)
        sort_at = inst.last_login_at if inst and inst.last_login_at else user.created_at
        filtered.append(
            _AccountListRow(
                user=user,
                institution=inst,
                invite=None,
                role_codes=codes,
                public_id=public_id,
                phone=phone,
                employee=employee,
                sort_at=sort_at,
            ),
        )

    for inv in pending_invites:
        if inv.email.lower() in user_emails:
            continue
        if role_filter and inv.intended_role.value != role_filter:
            continue
        if dept_filter_oid is not None and inv.department_id != dept_filter_oid:
            continue
        if status_filter and status_filter != "invited":
            continue
        reference_id = (inv.provisioning_reference_id or "").strip()
        public_id = reference_id or f"INV-{str(inv.id)[-6:].upper()}"
        if needle:
            hay = " ".join([inv.full_name, inv.email, public_id, inv.intended_role.value]).lower()
            if needle not in hay:
                continue
        filtered.append(
            _AccountListRow(
                user=None,
                institution=None,
                invite=inv,
                role_codes=[],
                public_id=public_id,
                phone=None,
                employee=None,
                sort_at=inv.created_at,
            ),
        )

    filtered.sort(key=lambda row: row.sort_at, reverse=True)

    total = len(filtered)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_slice = filtered[start : start + _PAGE_SIZE]

    table_rows: list[UserListTableRow] = []
    for row in page_slice:
        if row.user is not None:
            user = row.user
            inst = row.institution
            invited = user.email.lower() in invited_emails
            status = inst.account_status if inst else InstitutionAccountStatus.ACTIVE
            status_code, status_label, status_tone = _status_presentation(status, invited)
            dept_label = "—"
            if user.department_id and user.department_id in dept_by_id:
                dept_label = dept_by_id[user.department_id].name

            employee = row.employee
            mfa_on = bool(employee and employee.confidential_hr.get("mfa_enabled"))
            if not mfa_on and require_mfa and user.role in _PRIVILEGED_MFA_ROLES:
                mfa_on = False
            mfa_label = "On" if mfa_on else "Off"
            mfa_tone = "success" if mfa_on else "muted"

            last_login = inst.last_login_at if inst else None
            table_rows.append(
                UserListTableRow(
                    user_id=str(user.id),
                    full_name=user.full_name,
                    public_id=row.public_id,
                    role_label=_display_role(user.role, row.role_codes),
                    department_label=dept_label,
                    last_login_label=_format_last_login(last_login),
                    mfa_label=mfa_label,
                    mfa_tone=mfa_tone,
                    status_code=status_code,
                    status_label=status_label,
                    status_tone=status_tone,
                    detail_href=f"/college-admin/users/user-details?userId={user.id}",
                ),
            )
            continue

        inv = row.invite
        if inv is None:
            continue
        dept_label = "—"
        if inv.department_id and inv.department_id in dept_by_id:
            dept_label = dept_by_id[inv.department_id].name
        search_href = f"/college-admin/users/all-users-list?search={quote(inv.email)}"
        table_rows.append(
            UserListTableRow(
                user_id=f"inv:{inv.id}",
                full_name=inv.full_name,
                public_id=row.public_id,
                role_label=_display_role(inv.intended_role, []),
                department_label=dept_label,
                last_login_label="—",
                mfa_label="Off",
                mfa_tone="muted",
                status_code="invited",
                status_label="Invited",
                status_tone="info",
                detail_href=search_href,
            ),
        )

    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    seen_roles: set[str] = set()
    role_options = [UserListFilterOption(value="", label="Role")]
    for user in users:
        if user.role.value not in seen_roles:
            seen_roles.add(user.role.value)
            role_options.append(
                UserListFilterOption(value=user.role.value, label=_ROLE_DISPLAY.get(user.role, user.role.value)),
            )
    role_options.sort(key=lambda o: o.label)

    status_options = [
        UserListFilterOption(value="", label="Status"),
        UserListFilterOption(value="active", label="Active"),
        UserListFilterOption(value="invited", label="Invited"),
        UserListFilterOption(value="suspended", label="Suspended"),
        UserListFilterOption(value="deactivated", label="Deactivated"),
    ]

    dept_options = [UserListFilterOption(value="", label="Department")]
    for dept in sorted(departments, key=lambda d: d.name):
        dept_options.append(UserListFilterOption(value=str(dept.id), label=dept.name))

    return UserAllUsersListPageRead(
        page_title="All Users List",
        page_subtitle="Search, filter and manage every account in the college",
        export_label="Export",
        create_user_label="Create user",
        create_user_href="/college-admin/users/create-new-user",
        bulk_actions_label="Bulk actions",
        bulk_actions_href="/college-admin/users/bulk-user-invitation",
        search_placeholder="Search by name, ID, email or phone...",
        role_filter_label="Role",
        department_filter_label="Department",
        status_filter_label="Status",
        role_options=role_options,
        department_options=dept_options,
        status_options=status_options,
        users_section_title="Users",
        accounts_count_label=f"{total:,} accounts",
        table_headers=["Name", "User ID", "Role", "Department", "Last login", "MFA", "Status"],
        users=table_rows,
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
        footer_disclaimer="Live institution user records · Search and filters apply to stored accounts · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )