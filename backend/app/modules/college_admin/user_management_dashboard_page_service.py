"""User management dashboard page (CA 03.01)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import as_utc_aware, utcnow
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import (
    InstitutionAccountStatus,
    InstitutionUser,
    InstitutionUserInvitation,
    InvitationStatus,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    UserDashboardDailyPoint,
    UserDashboardFilterOption,
    UserDashboardKpi,
    UserDashboardPageRead,
    UserDashboardRecentRow,
    UserDashboardRoleBar,
    UserDashboardSecurityItem,
)
from app.modules.college_admin.security_admin_models import (
    InstitutionLoginActivity,
    InstitutionSecurityEvent,
    SecurityIncidentStatus,
)
from app.modules.tenants.models import Department

_IST = ZoneInfo("Asia/Kolkata")

_DATE_RANGE_DAYS: dict[str, int] = {
    "last_7_days": 7,
    "last_30_days": 30,
    "last_90_days": 90,
}

_ROLE_BUCKET_SPECS: list[tuple[str, str, set[Role]]] = [
    ("students", "Students", {Role.STUDENT}),
    ("faculty", "Faculty", {Role.FACULTY}),
    ("department_admins", "Department admins", {Role.DEPARTMENT_ADMIN}),
    ("accounts_staff", "Accounts staff", {Role.ACCOUNTS_STAFF, Role.FINANCE_STAFF}),
    ("hr_staff", "HR staff", {Role.HR_STAFF}),
    (
        "other_staff",
        "Other staff",
        {
            Role.COLLEGE_ADMIN,
            Role.EXAMINATION_CELL,
            Role.HOSTEL_ADMIN,
            Role.LIBRARIAN,
            Role.PARENT,
        },
    ),
]

_FINANCE_ROLES = {Role.ACCOUNTS_STAFF, Role.FINANCE_STAFF}
_STAFF_ROLES = {r for r in Role if r != Role.STUDENT and r not in {Role.SUPER_ADMIN, Role.PLATFORM_ADMIN}}


def _format_short_date(d: date) -> str:
    return d.strftime("%d %b")


def _format_created(when: datetime) -> str:
    return as_utc_aware(when).astimezone(_IST).strftime("%d %b")


def _status_presentation(status: InstitutionAccountStatus, invited: bool) -> tuple[str, str, str]:
    if invited or status == InstitutionAccountStatus.INVITED:
        return "invited", "Invited", "info"
    if status == InstitutionAccountStatus.SUSPENDED:
        return "suspended", "Suspended", "error"
    if status == InstitutionAccountStatus.DEACTIVATED:
        return "deactivated", "Deactivated", "muted"
    return "active", "Active", "success"


def _role_label(role: Role) -> str:
    return role.value.replace("_", " ").title()


async def get_user_management_dashboard_page(
    scope: AccessScope,
    *,
    date_range: str = "last_30_days",
    role_filter: str | None = None,
    department_id: str | None = None,
) -> UserDashboardPageRead:
    authorize(scope, Permission.INSTITUTION_USER_READ)
    tenant_id = require_college_tenant_scope(scope)
    days = _DATE_RANGE_DAYS.get(date_range, 30)
    cutoff = utcnow() - timedelta(days=days)
    week_cutoff = utcnow() - timedelta(days=7)
    inactive_cutoff = utcnow() - timedelta(days=90)
    soon = utcnow() + timedelta(hours=48)

    users = await User.find(Eq(User.tenant_id, tenant_id)).to_list()
    institution_rows = await InstitutionUser.find(Eq(InstitutionUser.tenant_id, tenant_id)).to_list()
    institution_by_user = {row.user_id: row for row in institution_rows}

    dept_filter_oid: PydanticObjectId | None = None
    if department_id:
        dept_filter_oid = PydanticObjectId(department_id)

    filtered_users: list[User] = []
    for user in users:
        if role_filter and user.role.value != role_filter:
            continue
        if dept_filter_oid is not None and user.department_id != dept_filter_oid:
            continue
        filtered_users.append(user)

    total_accounts = len(filtered_users)
    students = sum(1 for u in filtered_users if u.role == Role.STUDENT)
    staff = total_accounts - students

    active_week = 0
    for user in filtered_users:
        inst = institution_by_user.get(user.id)
        last = inst.last_login_at if inst else None
        if last and as_utc_aware(last) >= week_cutoff:
            active_week += 1
    active_pct = round((active_week / total_accounts) * 100) if total_accounts else 0

    pending_invites = await InstitutionUserInvitation.find(
        Eq(InstitutionUserInvitation.tenant_id, tenant_id),
        Eq(InstitutionUserInvitation.status, InvitationStatus.PENDING),
    ).to_list()
    expiring_soon = sum(1 for inv in pending_invites if as_utc_aware(inv.expires_at) <= soon)

    suspended = sum(
        1
        for u in filtered_users
        if (inst := institution_by_user.get(u.id))
        and inst.account_status == InstitutionAccountStatus.SUSPENDED
    )
    suspended_review = sum(
        1
        for u in filtered_users
        if (inst := institution_by_user.get(u.id))
        and inst.account_status == InstitutionAccountStatus.SUSPENDED
        and inst.suspension_reason
    )

    role_counts: dict[str, int] = {key: 0 for key, _, _ in _ROLE_BUCKET_SPECS}
    for user in filtered_users:
        for key, _, roles in _ROLE_BUCKET_SPECS:
            if user.role in roles:
                role_counts[key] += 1
                break
    max_role = max(role_counts.values()) if role_counts else 0
    role_bars = [
        UserDashboardRoleBar(
            key=key,
            label=label,
            count=role_counts[key],
            progress_percent=round((role_counts[key] / max_role) * 100) if max_role else 0,
        )
        for key, label, _ in _ROLE_BUCKET_SPECS
        if role_counts[key] > 0 or key in {"students", "faculty"}
    ]

    daily_points: list[UserDashboardDailyPoint] = []
    start_day = cutoff.date()
    today = utcnow().date()
    day = start_day
    login_rows = await InstitutionLoginActivity.find(
        Eq(InstitutionLoginActivity.tenant_id, tenant_id),
        Eq(InstitutionLoginActivity.success, True),
        GTE(InstitutionLoginActivity.created_at, cutoff),
    ).to_list()
    logins_by_day: dict[date, set[str]] = defaultdict(set)
    for row in login_rows:
        if row.user_id:
            logins_by_day[as_utc_aware(row.created_at).astimezone(_IST).date()].add(str(row.user_id))

    all_days: list[tuple[date, int]] = []
    while day <= today:
        active_count = len(logins_by_day.get(day, set()))
        if active_count == 0:
            active_count = sum(
                1
                for u in filtered_users
                if (inst := institution_by_user.get(u.id))
                and inst.last_login_at
                and as_utc_aware(inst.last_login_at).astimezone(_IST).date() == day
            )
        all_days.append((day, active_count))
        day += timedelta(days=1)
    if all_days:
        step = max(1, len(all_days) // 7)
        sampled = all_days[::step]
        if sampled[-1][0] != all_days[-1][0]:
            sampled.append(all_days[-1])
        daily_points = [
            UserDashboardDailyPoint(date_label=_format_short_date(d), active_users=count)
            for d, count in sampled[:8]
        ]

    departments = await Department.find(Eq(Department.tenant_id, tenant_id)).to_list()
    dept_by_id = {d.id: d for d in departments}

    recent_candidates: list[tuple[datetime, UserDashboardRecentRow]] = []
    sorted_users = sorted(filtered_users, key=lambda u: u.created_at, reverse=True)
    created_in_range = [u for u in sorted_users if as_utc_aware(u.created_at) >= cutoff]
    all_user_emails = {u.email.lower() for u in users}
    for user in created_in_range:
        inst = institution_by_user.get(user.id)
        dept_label = "—"
        if user.department_id and user.department_id in dept_by_id:
            dept_label = dept_by_id[user.department_id].name
        role_name = _role_label(user.role)
        invited = any(
            inv.email.lower() == user.email.lower() and inv.status == InvitationStatus.PENDING
            for inv in pending_invites
        )
        status = inst.account_status if inst else InstitutionAccountStatus.ACTIVE
        code, label, tone = _status_presentation(status, invited)
        recent_candidates.append(
            (
                user.created_at,
                UserDashboardRecentRow(
                    user_id=str(user.id),
                    user_name=user.full_name,
                    role_label=role_name,
                    department_label=dept_label,
                    created_label=_format_created(user.created_at),
                    status_code=code,
                    status_label=label,
                    status_tone=tone,
                    detail_href=f"/college-admin/users/user-details?userId={user.id}",
                ),
            ),
        )
    for inv in pending_invites:
        if inv.email.lower() in all_user_emails:
            continue
        if as_utc_aware(inv.created_at) < cutoff:
            continue
        dept_label = "—"
        if inv.department_id and inv.department_id in dept_by_id:
            dept_label = dept_by_id[inv.department_id].name
        recent_candidates.append(
            (
                inv.created_at,
                UserDashboardRecentRow(
                    user_id=f"inv:{inv.id}",
                    user_name=inv.full_name,
                    role_label=_role_label(inv.intended_role),
                    department_label=dept_label,
                    created_label=_format_created(inv.created_at),
                    status_code="invited",
                    status_label="Invited",
                    status_tone="info",
                    detail_href=f"/college-admin/users/all-users-list?search={quote(inv.email)}",
                ),
            ),
        )
    recent_candidates.sort(key=lambda pair: pair[0], reverse=True)
    recent = [row for _, row in recent_candidates[:4]]

    finance_without_mfa = sum(1 for u in filtered_users if u.role in _FINANCE_ROLES)
    open_mfa_events = await InstitutionSecurityEvent.find(
        Eq(InstitutionSecurityEvent.tenant_id, tenant_id),
    ).to_list()
    open_mfa_events = [
        e
        for e in open_mfa_events
        if e.status in {SecurityIncidentStatus.OPEN, SecurityIncidentStatus.INVESTIGATING}
    ]
    mfa_count = sum(1 for e in open_mfa_events if "mfa" in e.code.lower() or "mfa" in e.title.lower())
    if mfa_count == 0 and finance_without_mfa:
        mfa_count = finance_without_mfa

    inactive_staff = 0
    for user in filtered_users:
        if user.role not in _STAFF_ROLES or user.role == Role.STUDENT:
            continue
        inst = institution_by_user.get(user.id)
        last = inst.last_login_at if inst else None
        if last is None or as_utc_aware(last) < inactive_cutoff:
            inactive_staff += 1

    by_ip: dict[str, set[str]] = defaultdict(set)
    for row in login_rows:
        if row.ip_address and row.user_id:
            by_ip[row.ip_address].add(str(row.user_id))
    shared_login_groups = sum(1 for uids in by_ip.values() if len(uids) > 1)

    security_items = [
        UserDashboardSecurityItem(
            key="mfa_not_enabled",
            title="MFA not enabled",
            description="Staff accounts with finance access",
            count=mfa_count,
            tone="warning",
        ),
        UserDashboardSecurityItem(
            key="inactive_90_days",
            title="Inactive 90+ days",
            description="Staff accounts to review",
            count=inactive_staff,
            tone="info",
        ),
        UserDashboardSecurityItem(
            key="shared_logins",
            title="Shared logins suspected",
            description="Same device, different users",
            count=shared_login_groups,
            tone="error",
        ),
    ]

    seen_roles: set[str] = set()
    role_options = [UserDashboardFilterOption(value="", label="All roles")]
    for user in users:
        if user.role.value not in seen_roles:
            seen_roles.add(user.role.value)
            role_options.append(UserDashboardFilterOption(value=user.role.value, label=_role_label(user.role)))
    role_options.sort(key=lambda o: o.label)

    dept_options = [UserDashboardFilterOption(value="", label="All departments")]
    for dept in sorted(departments, key=lambda d: d.name):
        dept_options.append(UserDashboardFilterOption(value=str(dept.id), label=dept.name))

    date_options = [
        UserDashboardFilterOption(value="last_7_days", label="Last 7 days"),
        UserDashboardFilterOption(value="last_30_days", label="Last 30 days"),
        UserDashboardFilterOption(value="last_90_days", label="Last 90 days"),
    ]

    updated_label = as_utc_aware(utcnow()).astimezone(_IST).strftime("%H:%M") + " IST"

    return UserDashboardPageRead(
        page_title="User Management Dashboard",
        page_subtitle="Accounts, roles and access across students, faculty and staff",
        bulk_invite_label="Bulk invite",
        bulk_invite_href="/college-admin/users/bulk-user-invitation",
        create_user_label="Create user",
        create_user_href="/college-admin/users/create-new-user",
        date_range_filter_label="Date range",
        role_filter_label="Role",
        department_filter_label="Department",
        scope_indicator_label="College scope",
        updated_at_label=updated_label,
        date_range_options=date_options,
        role_options=role_options,
        department_options=dept_options,
        kpis=[
            UserDashboardKpi(
                key="total_accounts",
                label="Total accounts",
                value=str(total_accounts),
                hint_line=f"{students} students · {staff} staff",
                hint_tone="muted",
            ),
            UserDashboardKpi(
                key="active_week",
                label="Active this week",
                value=str(active_week),
                hint_line=f"{active_pct}% of accounts",
                hint_tone="success",
            ),
            UserDashboardKpi(
                key="pending_invitations",
                label="Pending invitations",
                value=str(len(pending_invites)),
                hint_line=f"{expiring_soon} expire in 48 hours" if expiring_soon else "None expiring within 48 hours",
                hint_tone="warning" if expiring_soon else "muted",
            ),
            UserDashboardKpi(
                key="suspended",
                label="Suspended",
                value=str(suspended),
                hint_line=f"{suspended_review} awaiting review" if suspended_review else "No suspensions awaiting review",
                hint_tone="error" if suspended else "muted",
            ),
        ],
        daily_active_title="Daily active users",
        daily_active_points=daily_points,
        accounts_by_role_title="Accounts by role",
        role_bars=role_bars,
        recent_accounts_title="Recently created accounts",
        recent_accounts=recent,
        recent_accounts_footer_label=f"Last {days} days · {len(created_in_range)} accounts",
        view_all_href="/college-admin/users/all-users-list",
        view_all_label="View all →",
        security_checks_title="Security checks",
        security_audit_href="/college-admin/security-administration/audit-logs",
        security_audit_label="Security & audit →",
        security_items=security_items,
        footer_disclaimer="Live institution user records · Metrics from accounts, invitations and login activity · All times IST",
        footer_snapshot_label="Live snapshot",
        generated_at=utcnow(),
    )