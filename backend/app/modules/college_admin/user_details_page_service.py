"""User details page (CA 03.03)."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.authorization.resolver import effective_permissions_for_user
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.common.ids import to_object_id
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.identity_models import (
    AccessHistoryEvent,
    InstitutionAccessHistory,
    InstitutionAccountStatus,
    InstitutionRole,
    InstitutionRoleAssignment,
    InstitutionUser,
    InstitutionUserInvitation,
    InvitationStatus,
)
from app.modules.college_admin.schemas import (
    UserDetailsAccountField,
    UserDetailsActivityItem,
    UserDetailsAssignedRoleRow,
    UserDetailsPageRead,
    UserDetailsPermissionBar,
    UserDetailsProfileBadge,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.security_admin_models import InstitutionLoginActivity
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Department

from app.modules.college_admin.user_all_users_list_page_service import (
    _ROLE_DISPLAY,
    _display_role,
    _format_last_login,
    _resolve_public_id,
    _role_codes_for_user,
    _status_presentation,
)

_IST = ZoneInfo("Asia/Kolkata")

_PERMISSION_BUCKETS: list[tuple[str, str, tuple[str, ...]]] = [
    ("students", "Students", ("college:student_admin", "student:")),
    ("attendance", "Attendance", ("college:attendance_admin", "attendance:")),
    ("examinations", "Examinations", ("college:examination", "examination:")),
    ("finance", "Finance", ("college:finance", "college:accounts", "accounts:")),
]


def _initials(full_name: str) -> str:
    parts = [p for p in full_name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return f"{parts[0][0]}{parts[-1][0]}".upper()


def _format_ist_date(when: datetime | None, *, with_time: bool = False) -> str:
    if when is None:
        return "—"
    local = as_utc_aware(when).astimezone(_IST)
    if with_time:
        return local.strftime("%d %b %Y, %H:%M")
    return local.strftime("%d %b %Y")


def _account_type_label(role: Role) -> str:
    if role == Role.STUDENT:
        return "Student"
    return "Staff"


def _username_from_email(email: str) -> str:
    return email.split("@", 1)[0]


def _permission_bucket(perms: frozenset[Permission], prefixes: tuple[str, ...]) -> tuple[int, str]:
    matched = [p for p in perms if any(p.value.startswith(px) or f".{px}" in f".{p.value}" for px in prefixes)]
    if not matched:
        return 5, "No access"
    values = [p.value for p in matched]
    if any(sub in v for v in values for sub in (":manage", ":publish", ":approve", ":config")):
        if any("attendance" in v for v in values):
            return 100, "Approve corrections"
        if any("student" in v for v in values):
            return 100, "Department scope"
        if any("examination" in v or "marks" in v for v in values):
            if any(":enter" in v for v in values) and not any(":manage" in v or ":publish" in v for v in values):
                return 72, "Marks entry only"
            return 100, "Full examination access"
        if any("finance" in v or "accounts" in v for v in values):
            return 100, "Finance operations"
        return 88, "Elevated access"
    if any(":read" in v for v in values):
        if any("examination" in v for v in values):
            return 68, "Marks entry only"
        if any("student" in v for v in values):
            return 72, "Department scope"
        return 40, "Read only"
    return 55, "Limited access"


def _activity_tone(event_type: str) -> str:
    if event_type in {AccessHistoryEvent.LOGIN_SUCCESS.value, AccessHistoryEvent.USER_ACTIVATED.value}:
        return "success"
    if event_type in {AccessHistoryEvent.USER_SUSPENDED.value, AccessHistoryEvent.LOGIN_FAILURE.value}:
        return "error"
    return "info"


def _activity_title(row: InstitutionAccessHistory) -> str:
    if row.summary.strip():
        return row.summary.strip()
    return row.event_type.value.replace("_", " ").title()


def _format_activity_when(when: datetime) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    today = utcnow().astimezone(_IST).date()
    login_date = local.date()
    if login_date == today:
        return f"Today {local.strftime('%H:%M')}"
    if login_date == today - timedelta(days=1):
        return f"Yesterday {local.strftime('%H:%M')}"
    return local.strftime("%d %b %Y, %H:%M")


async def _user_display_name(tenant_id: PydanticObjectId, user_id: PydanticObjectId | None) -> str:
    if user_id is None:
        return "System"
    actor = await User.find_one(Eq(User.tenant_id, tenant_id), Eq(User.id, user_id))
    if actor is None:
        actor = await User.get(user_id)
    return actor.full_name if actor else "—"


def _role_scope_label(role: InstitutionRole, department_name: str | None) -> str:
    code = role.role_code.lower()
    name = role.name
    if "dept" in code or "department" in name.lower():
        return f"{department_name} department" if department_name else "Department scope"
    if "faculty" in code or role.base_role == Role.FACULTY:
        return f"{department_name or 'Institution'} · teaching profile"
    if "exam" in code or "evaluator" in name.lower():
        return "Internal assessments"
    if department_name:
        return department_name
    return "Institution-wide"


async def get_user_details_page(scope: AccessScope, user_id: PydanticObjectId) -> UserDetailsPageRead:
    authorize(scope, Permission.INSTITUTION_USER_READ)
    tenant_id = require_college_tenant_scope(scope)

    user = await User.find_one(Eq(User.id, user_id), Eq(User.tenant_id, tenant_id))
    if user is None:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)

    institution = await InstitutionUser.find_one(
        Eq(InstitutionUser.tenant_id, tenant_id),
        Eq(InstitutionUser.user_id, user_id),
    )
    student = await StudentProfile.find_one(Eq(StudentProfile.tenant_id, tenant_id), Eq(StudentProfile.user_id, user_id))
    employee = await EmployeeRecord.find_one(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.user_id, user_id),
    )

    departments = await Department.find(Eq(Department.tenant_id, tenant_id)).to_list()
    dept_by_id = {d.id: d for d in departments}
    dept_name = dept_by_id[user.department_id].name if user.department_id and user.department_id in dept_by_id else None

    pending_invite = await InstitutionUserInvitation.find_one(
        Eq(InstitutionUserInvitation.tenant_id, tenant_id),
        Eq(InstitutionUserInvitation.email, user.email),
        Eq(InstitutionUserInvitation.status, InvitationStatus.PENDING),
    )
    invited = pending_invite is not None
    status = institution.account_status if institution else InstitutionAccountStatus.ACTIVE
    status_code, status_label, status_tone = _status_presentation(status, invited)

    role_codes = await _role_codes_for_user(tenant_id, user_id)
    primary_role_label = _display_role(user.role, role_codes)
    public_id = _resolve_public_id(user, student, employee)

    designation = employee.designation if employee and employee.designation else None
    designation_parts = [p for p in (designation, dept_name, public_id) if p]
    designation_line = " · ".join(designation_parts) if designation_parts else public_id

    phone = student.contact_phone if student and student.contact_phone else None
    if not phone and student:
        phone = student.phone

    last_login = institution.last_login_at if institution else None
    last_login_label = _format_last_login(last_login)
    if last_login:
        local = as_utc_aware(last_login).astimezone(_IST)
        today = utcnow().astimezone(_IST).date()
        if local.date() == today:
            last_login_summary = f"Last login today {local.strftime('%H:%M')}"
        else:
            last_login_summary = f"Last login {last_login_label.lower()}"
    else:
        last_login_summary = "No recent login recorded"

    mfa_on = bool(employee and employee.confidential_hr.get("mfa_enabled"))
    mfa_label = "Authenticator app" if mfa_on else "Not enabled"
    mfa_tone = "success" if mfa_on else "muted"

    created_history = await InstitutionAccessHistory.find_one(
        Eq(InstitutionAccessHistory.tenant_id, tenant_id),
        Eq(InstitutionAccessHistory.user_id, user_id),
        Eq(InstitutionAccessHistory.event_type, AccessHistoryEvent.USER_CREATED),
    )
    created_by = await _user_display_name(tenant_id, created_history.actor_id) if created_history else "—"
    created_label = f"{_format_ist_date(user.created_at)} by {created_by}"

    pwd_history = await (
        InstitutionAccessHistory.find(
            Eq(InstitutionAccessHistory.tenant_id, tenant_id),
            Eq(InstitutionAccessHistory.user_id, user_id),
            Eq(InstitutionAccessHistory.event_type, AccessHistoryEvent.PASSWORD_RESET),
        )
        .sort("-created_at")
        .limit(1)
        .to_list()
    )
    pwd_changed_at = pwd_history[0].created_at if pwd_history else user.updated_at
    password_changed_label = _format_ist_date(pwd_changed_at)

    account_fields = [
        UserDetailsAccountField(key="username", label="Username", value=_username_from_email(user.email)),
        UserDetailsAccountField(key="account_type", label="Account type", value=_account_type_label(user.role)),
        UserDetailsAccountField(key="created", label="Created", value=created_label),
        UserDetailsAccountField(
            key="password_changed",
            label="Password last changed",
            value=password_changed_label,
        ),
        UserDetailsAccountField(key="mfa", label="Multi-factor authentication", value=mfa_label, tone=mfa_tone),
        UserDetailsAccountField(
            key="login_method",
            label="Login method",
            value="College account (email & password)",
        ),
    ]

    assignments = await InstitutionRoleAssignment.find(
        Eq(InstitutionRoleAssignment.tenant_id, tenant_id),
        Eq(InstitutionRoleAssignment.user_id, user_id),
        Eq(InstitutionRoleAssignment.revoked_at, None),
    ).to_list()
    role_rows: list[UserDetailsAssignedRoleRow] = []
    for assignment in assignments:
        role_doc = await InstitutionRole.get(assignment.institution_role_id)
        if role_doc is None or not role_doc.is_active:
            continue
        role_rows.append(
            UserDetailsAssignedRoleRow(
                role_name=role_doc.name,
                scope_label=_role_scope_label(role_doc, dept_name),
                assigned_by_label=await _user_display_name(tenant_id, assignment.assigned_by),
                since_label=_format_ist_date(assignment.assigned_at),
            ),
        )
    if not role_rows:
        role_rows.append(
            UserDetailsAssignedRoleRow(
                role_name=primary_role_label,
                scope_label=dept_name or "Institution-wide",
                assigned_by_label=created_by,
                since_label=_format_ist_date(user.created_at),
            ),
        )

    effective = await effective_permissions_for_user(user)
    permission_bars = [
        UserDetailsPermissionBar(
            key=key,
            label=title,
            description=desc,
            progress_percent=percent,
        )
        for key, title, prefixes in _PERMISSION_BUCKETS
        for percent, desc in [_permission_bucket(effective, prefixes)]
    ]

    history_rows = await (
        InstitutionAccessHistory.find(
            Eq(InstitutionAccessHistory.tenant_id, tenant_id),
            Eq(InstitutionAccessHistory.user_id, user_id),
        )
        .sort("-created_at")
        .limit(8)
        .to_list()
    )
    login_rows = await (
        InstitutionLoginActivity.find(
            Eq(InstitutionLoginActivity.tenant_id, tenant_id),
            Eq(InstitutionLoginActivity.user_id, user_id),
            Eq(InstitutionLoginActivity.success, True),
        )
        .sort("-created_at")
        .limit(5)
        .to_list()
    )

    activity_ranked: list[tuple[datetime, UserDetailsActivityItem]] = []
    for row in history_rows:
        meta = row.metadata or {}
        subtitle_bits = [_format_activity_when(row.created_at)]
        if meta.get("ip_address"):
            subtitle_bits.append(str(meta["ip_address"]))
        activity_ranked.append(
            (
                row.created_at,
                UserDetailsActivityItem(
                    key=str(row.id),
                    title=_activity_title(row),
                    subtitle=" · ".join(subtitle_bits),
                    tone=_activity_tone(row.event_type.value),
                ),
            ),
        )
    for row in login_rows:
        ua = (row.user_agent or "Unknown client").split(")")[0].replace("Mozilla/5.0 (", "")
        subtitle_bits = [_format_activity_when(row.created_at), ua]
        if row.ip_address:
            subtitle_bits.append(row.ip_address)
        activity_ranked.append(
            (
                row.created_at,
                UserDetailsActivityItem(
                    key=f"login-{row.id}",
                    title="Logged in",
                    subtitle=" · ".join(subtitle_bits),
                    tone="success",
                ),
            ),
        )
    activity_ranked.sort(key=lambda pair: pair[0], reverse=True)
    activity = [item for _, item in activity_ranked[:5]]

    user_id_str = str(user_id)
    suspend_visible = status_code not in {"suspended", "deactivated"}

    return UserDetailsPageRead(
        page_title="User Details",
        page_subtitle="Profile, roles and access for a single account",
        back_href="/college-admin/users/all-users-list",
        back_label="All users",
        user_id=user_id_str,
        reset_password_label="Reset password",
        suspend_label="Suspend",
        edit_user_label="Edit user",
        reset_password_action_user_id=user_id_str,
        suspend_href=f"/college-admin/users/user-account-activation-suspension?userId={user_id_str}",
        edit_user_href=f"/college-admin/users/edit-user-information?userId={user_id_str}",
        show_suspend_action=suspend_visible,
        profile_initials=_initials(user.full_name),
        profile_name=user.full_name,
        profile_badges=[
            UserDetailsProfileBadge(key="status", label=status_label, tone=status_tone),
            UserDetailsProfileBadge(key="role", label=primary_role_label, tone="info"),
        ],
        designation_line=designation_line,
        email=user.email,
        phone_label=phone or "—",
        last_login_summary=last_login_summary,
        account_section_title="Account information",
        account_edit_href=f"/college-admin/users/edit-user-information?userId={user_id_str}",
        account_edit_label="Edit",
        account_fields=account_fields,
        roles_section_title="Assigned roles",
        assign_role_href=f"/college-admin/users/role-assignment?userId={user_id_str}",
        assign_role_label="Assign role",
        roles_table_headers=["Role", "Scope", "Assigned by", "Since"],
        assigned_roles=role_rows,
        active_roles_footer_label=f"{len(role_rows)} active role{'s' if len(role_rows) != 1 else ''}",
        role_assignment_href=f"/college-admin/users/role-assignment?userId={user_id_str}",
        role_assignment_label="Role assignment",
        permissions_section_title="Effective permissions",
        permission_bars=permission_bars,
        activity_section_title="Recent activity",
        access_history_href=f"/college-admin/users/user-access-history?userId={user_id_str}",
        access_history_label="Access history",
        recent_activity=activity,
        footer_disclaimer=(
            "Live institution user records · Profile, roles and activity from stored data · All times IST"
        ),
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )


async def get_user_details_page_by_id(scope: AccessScope, user_id_raw: str) -> UserDetailsPageRead:
    user_oid = to_object_id(user_id_raw, "user id")
    return await get_user_details_page(scope, user_oid)