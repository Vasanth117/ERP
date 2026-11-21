"""Login & account activity page (CA 03 — activity)."""

from __future__ import annotations

import csv
import io
import ipaddress
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import as_utc_aware, utcnow
from app.modules.auth.models import RefreshToken, User
from app.modules.college_admin.identity_models import InstitutionAccountStatus, InstitutionUser
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    LoginAccountActivityDailyBar,
    LoginAccountActivityLockedCard,
    LoginAccountActivityMethodBar,
    LoginAccountActivityPageRead,
    LoginAccountActivityRecentRow,
    UserDashboardFilterOption,
    UserDashboardKpi,
)
from app.modules.college_admin.security_admin_models import InstitutionLoginActivity, InstitutionSecurityPolicy

_IST = ZoneInfo("Asia/Kolkata")
_RECENT_LIMIT = 8
_LOCKED_LIMIT = 5

_DATE_RANGE_DAYS: dict[str, int] = {
    "last_7_days": 7,
    "last_30_days": 30,
    "last_90_days": 90,
}

_ROLE_FILTERS: list[tuple[str, str, set[Role] | None]] = [
    ("", "All roles", None),
    ("students", "Students", {Role.STUDENT}),
    ("faculty", "Faculty", {Role.FACULTY}),
    ("staff", "Staff", {Role.ACCOUNTS_STAFF, Role.FINANCE_STAFF, Role.HR_STAFF, Role.EXAMINATION_CELL, Role.LIBRARIAN, Role.HOSTEL_ADMIN}),
    ("admins", "Admins", {Role.DEPARTMENT_ADMIN, Role.COLLEGE_ADMIN}),
]

_LOCATION_FILTERS = [
    ("", "All locations"),
    ("campus_lan", "Campus LAN"),
    ("mobile", "Mobile apps"),
    ("external", "External"),
]

_WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _cutoff(date_range: str) -> datetime:
    days = _DATE_RANGE_DAYS.get(date_range, 7)
    return utcnow() - timedelta(days=days)


def _updated_label(when: datetime) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return f"Updated {local.strftime('%H:%M')} IST"


def _snapshot_label(when: datetime) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return f"Live snapshot · {local.strftime('%d %b %Y, %H:%M IST')}"


def _device_label(user_agent: str | None, stored: str | None) -> str:
    if stored:
        return stored
    if not user_agent:
        return "Unknown device"
    ua = user_agent.lower()
    browser = "Browser"
    if "chrome" in ua:
        browser = "Chrome"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "edg" in ua:
        browser = "Edge"
    elif "safari" in ua:
        browser = "Safari"
    platform = "Unknown"
    if "windows" in ua:
        platform = "Windows"
    elif "android" in ua:
        platform = "Android"
        browser = "App"
    elif "iphone" in ua or "ipad" in ua:
        platform = "iOS"
        browser = "App"
    elif "mac" in ua:
        platform = "macOS"
    return f"{browser} · {platform}"


def _location_label(ip: str | None, stored: str | None) -> str:
    if stored:
        return stored
    if not ip:
        return "Unknown"
    try:
        addr = ipaddress.ip_address(ip.strip())
        if addr.is_private or addr.is_loopback:
            return "Campus LAN"
    except ValueError:
        pass
    if ip.startswith("10.") or ip.startswith("192.168."):
        return "Campus LAN"
    return "External"


def _location_bucket(label: str) -> str:
    if label == "Campus LAN":
        return "campus_lan"
    if "App" in label or "Android" in label or "iOS" in label:
        return "mobile"
    return "external"


def _login_method(row: InstitutionLoginActivity) -> str:
    if row.login_method:
        return row.login_method.replace("_", " ").title()
    reason = (row.failure_reason or "").lower()
    if "otp" in reason or "otp" in (row.email or "").lower():
        return "OTP on mobile"
    if row.success and row.user_id:
        return "College SSO"
    return "Password"


def _result_presentation(row: InstitutionLoginActivity, suspended: bool) -> tuple[str, str, str]:
    if row.success:
        return "success", "Success", "success"
    if suspended:
        return "blocked", "Blocked", "error"
    reason = (row.failure_reason or "").lower()
    if "password" in reason or "credential" in reason:
        return "wrong_password", "Wrong password", "warning"
    if "lock" in reason or "blocked" in reason:
        return "blocked", "Blocked", "error"
    return "failed", "Failed", "warning"


async def _tenant_user_ids_by_role(tenant_id: PydanticObjectId, role_key: str) -> set[PydanticObjectId] | None:
    if not role_key:
        return None
    roles: set[Role] | None = None
    for key, _, role_set in _ROLE_FILTERS:
        if key == role_key:
            roles = role_set
            break
    if roles is None:
        return None
    users = await User.find(Eq(User.tenant_id, tenant_id)).to_list()
    return {u.id for u in users if u.role in roles}


def _row_in_filters(
    row: InstitutionLoginActivity,
    *,
    allowed_users: set[PydanticObjectId] | None,
    location_filter: str,
) -> bool:
    if allowed_users is not None and row.user_id and row.user_id not in allowed_users:
        return False
    if location_filter:
        loc = _location_label(row.ip_address, row.location_label)
        if _location_bucket(loc) != location_filter:
            return False
    return True


async def _fetch_rows(tenant_id: PydanticObjectId, since: datetime) -> list[InstitutionLoginActivity]:
    return await InstitutionLoginActivity.find(
        Eq(InstitutionLoginActivity.tenant_id, tenant_id),
        GTE(InstitutionLoginActivity.created_at, since),
    ).to_list()


async def _active_sessions(tenant_id: PydanticObjectId) -> tuple[int, int]:
    users = await User.find(Eq(User.tenant_id, tenant_id)).to_list()
    user_ids = [u.id for u in users]
    if not user_ids:
        return 0, 0
    now = utcnow()
    tokens = await RefreshToken.find(
        In(RefreshToken.user_id, user_ids),
        Eq(RefreshToken.revoked_at, None),
    ).to_list()
    active = sum(1 for t in tokens if as_utc_aware(t.expires_at) > now)
    today = now.astimezone(_IST).date()
    since_today = datetime.combine(today, datetime.min.time(), tzinfo=_IST)
    successes = await InstitutionLoginActivity.find(
        Eq(InstitutionLoginActivity.tenant_id, tenant_id),
        Eq(InstitutionLoginActivity.success, True),
        GTE(InstitutionLoginActivity.created_at, since_today),
    ).to_list()
    hour_counts: dict[int, int] = defaultdict(int)
    for row in successes:
        hour = as_utc_aware(row.created_at).astimezone(_IST).hour
        hour_counts[hour] += 1
    peak = max(hour_counts.values()) if hour_counts else active
    return active, peak


async def _display_name(tenant_id: PydanticObjectId, row: InstitutionLoginActivity) -> str:
    if row.user_id:
        user = await User.get(row.user_id)
        if user:
            return user.full_name
    if row.email:
        local = row.email.split("@", 1)[0]
        if re.match(r"^\d", local):
            return local
    return row.email or "Unknown user"


async def get_login_account_activity_page(
    scope: AccessScope,
    *,
    date_range: str = "last_7_days",
    role_filter: str = "",
    location_filter: str = "",
) -> LoginAccountActivityPageRead:
    authorize(scope, Permission.INSTITUTION_USER_READ)
    tenant_id = require_college_tenant_scope(scope)

    days = _DATE_RANGE_DAYS.get(date_range, 7)
    since = _cutoff(date_range)
    prev_since = since - timedelta(days=days)
    allowed_users = await _tenant_user_ids_by_role(tenant_id, role_filter)

    all_rows = await _fetch_rows(tenant_id, prev_since)
    current_rows = [r for r in all_rows if as_utc_aware(r.created_at) >= since]
    prev_rows = [r for r in all_rows if prev_since <= as_utc_aware(r.created_at) < since]

    current_rows = [r for r in current_rows if _row_in_filters(r, allowed_users=allowed_users, location_filter=location_filter)]
    prev_rows = [r for r in prev_rows if _row_in_filters(r, allowed_users=allowed_users, location_filter=location_filter)]

    success_count = sum(1 for r in current_rows if r.success)
    prev_success = sum(1 for r in prev_rows if r.success)
    fail_count = sum(1 for r in current_rows if not r.success)
    failure_rate = (fail_count / max(success_count + fail_count, 1)) * 100

    policy = await InstitutionSecurityPolicy.find_one(Eq(InstitutionSecurityPolicy.tenant_id, tenant_id))
    max_failed = policy.max_failed_logins if policy else 5

    fail_window = utcnow() - timedelta(hours=24)
    recent_failures = [r for r in current_rows if not r.success and as_utc_aware(r.created_at) >= fail_window]
    failure_counts: dict[str, int] = defaultdict(int)
    last_fail: dict[str, datetime] = {}
    for row in recent_failures:
        key = str(row.user_id) if row.user_id else (row.email or "unknown")
        failure_counts[key] += 1
        last_fail[key] = max(last_fail.get(key, row.created_at), row.created_at)

    locked_keys = {k for k, v in failure_counts.items() if v >= max_failed}

    active_sessions, peak_sessions = await _active_sessions(tenant_id)

    delta_pct = 0.0
    if prev_success:
        delta_pct = ((success_count - prev_success) / prev_success) * 100
    success_hint = f"{delta_pct:+.0f}% vs prior period" if prev_success else "No prior period data"
    success_tone = "success" if delta_pct >= 0 else "warning"

    generated = utcnow()

    kpis = [
        UserDashboardKpi(
            key="successful_logins",
            label="Successful logins",
            value=f"{success_count:,}",
            hint_line=success_hint,
            hint_tone=success_tone,
        ),
        UserDashboardKpi(
            key="failed_attempts",
            label="Failed attempts",
            value=f"{fail_count:,}",
            hint_line=f"{failure_rate:.1f}% failure rate",
            hint_tone="muted",
        ),
        UserDashboardKpi(
            key="locked_accounts",
            label="Locked accounts",
            value=f"{len(locked_keys):,}",
            hint_line=f"After {max_failed} failed attempts",
            hint_tone="warning" if locked_keys else "muted",
        ),
        UserDashboardKpi(
            key="active_sessions",
            label="Active sessions now",
            value=f"{active_sessions:,}",
            hint_line=f"Peak {peak_sessions:,} today",
            hint_tone="muted",
        ),
    ]

    daily_counts: dict[date, int] = defaultdict(int)
    for row in current_rows:
        if not row.success:
            continue
        day = as_utc_aware(row.created_at).astimezone(_IST).date()
        daily_counts[day] += 1

    today = utcnow().astimezone(_IST).date()
    daily_bars: list[LoginAccountActivityDailyBar] = []
    for offset in range(min(days, 7) - 1, -1, -1):
        day = today - timedelta(days=offset)
        weekday = _WEEKDAY_LABELS[day.weekday()]
        daily_bars.append(
            LoginAccountActivityDailyBar(
                day_key=day.isoformat(),
                day_label=weekday,
                login_count=daily_counts.get(day, 0),
            )
        )

    method_counts: dict[str, int] = defaultdict(int)
    for row in current_rows:
        if row.success:
            method_counts[_login_method(row)] += 1
    method_total = sum(method_counts.values()) or 1
    method_bars = [
        LoginAccountActivityMethodBar(
            method_key=key.lower().replace(" ", "_"),
            method_label=key,
            percent=round((count / method_total) * 100),
        )
        for key, count in sorted(method_counts.items(), key=lambda item: -item[1])
    ]
    if not method_bars:
        method_bars = [
            LoginAccountActivityMethodBar(method_key="password", method_label="Password", percent=0),
        ]

    institution_by_user: dict[PydanticObjectId, InstitutionUser] = {}
    for inst in await InstitutionUser.find(Eq(InstitutionUser.tenant_id, tenant_id)).to_list():
        institution_by_user[inst.user_id] = inst

    recent_sorted = sorted(current_rows, key=lambda r: r.created_at, reverse=True)[:_RECENT_LIMIT]
    recent_rows: list[LoginAccountActivityRecentRow] = []
    for row in recent_sorted:
        suspended = False
        if row.user_id and row.user_id in institution_by_user:
            suspended = institution_by_user[row.user_id].account_status == InstitutionAccountStatus.SUSPENDED
        code, label, tone = _result_presentation(row, suspended)
        display_method = _login_method(row)
        if code == "success" and "mfa" in (row.failure_reason or "").lower():
            display_method = "SSO + MFA"
        recent_rows.append(
            LoginAccountActivityRecentRow(
                user_name=await _display_name(tenant_id, row),
                method_label=display_method,
                device_label=_device_label(row.user_agent, row.device_label),
                location_label=_location_label(row.ip_address, row.location_label),
                result_code=code,
                result_label=label,
                result_tone=tone,
            )
        )

    locked_cards: list[LoginAccountActivityLockedCard] = []
    seen_locked: set[str] = set()
    for row in sorted(recent_failures, key=lambda r: r.created_at, reverse=True):
        key = str(row.user_id) if row.user_id else (row.email or "")
        if not key or key in seen_locked:
            continue
        suspended = row.user_id and institution_by_user.get(row.user_id, None)
        is_suspended = suspended and suspended.account_status == InstitutionAccountStatus.SUSPENDED
        is_locked = key in locked_keys
        if not is_locked and not is_suspended:
            continue
        seen_locked.add(key)
        when = last_fail.get(key, row.created_at)
        local = as_utc_aware(when).astimezone(_IST)
        if is_suspended:
            subtitle = "Suspended user tried login"
            status_label = "Blocked"
            status_tone = "error"
            status_code = "blocked"
        else:
            subtitle = f"{failure_counts[key]} failed attempts · {local.strftime('%H:%M')}"
            status_label = "Locked"
            status_tone = "warning"
            status_code = "locked"
        locked_cards.append(
            LoginAccountActivityLockedCard(
                user_id=str(row.user_id) if row.user_id else "",
                user_name=await _display_name(tenant_id, row),
                subtitle=subtitle,
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
                unlock_href=f"/college-admin/users/user-account-activation-suspension?userId={row.user_id}"
                if row.user_id
                else "/college-admin/users/user-account-activation-suspension",
            )
        )
        if len(locked_cards) >= _LOCKED_LIMIT:
            break

    max_bar = max((b.login_count for b in daily_bars), default=1)

    return LoginAccountActivityPageRead(
        page_title="Login & Account Activity",
        page_subtitle="Sign-ins, failures and sessions across all accounts",
        export_label="Export",
        date_range_options=[
            UserDashboardFilterOption(value="last_7_days", label="Last 7 days"),
            UserDashboardFilterOption(value="last_30_days", label="Last 30 days"),
            UserDashboardFilterOption(value="last_90_days", label="Last 90 days"),
        ],
        role_filter_options=[UserDashboardFilterOption(value=k, label=label) for k, label, _ in _ROLE_FILTERS],
        location_filter_options=[UserDashboardFilterOption(value=v, label=l) for v, l in _LOCATION_FILTERS],
        selected_date_range=date_range if date_range in _DATE_RANGE_DAYS else "last_7_days",
        selected_role_filter=role_filter,
        selected_location_filter=location_filter,
        scope_badge_label="College scope",
        updated_label=_updated_label(generated),
        kpis=kpis,
        logins_per_day_title="Logins per day",
        daily_bars=daily_bars,
        daily_bars_max=max_bar,
        login_methods_title="Login methods",
        method_bars=method_bars,
        recent_section_title="Recent sign-ins",
        recent_live_label="Live feed",
        view_all_label="View all",
        view_all_href="/college-admin/users/user-access-history",
        recent_table_headers=["User", "Method", "Device", "Location", "Result"],
        recent_rows=recent_rows,
        locked_section_title="Locked accounts",
        unlock_label="Unlock",
        locked_accounts=locked_cards,
        footer_disclaimer="Live login activity from institution records · Sessions from active refresh tokens · All times IST",
        footer_snapshot_label=_snapshot_label(generated),
        generated_at=generated,
    )


async def export_login_account_activity_csv(
    scope: AccessScope,
    *,
    date_range: str = "last_7_days",
    role_filter: str = "",
    location_filter: str = "",
) -> str:
    page = await get_login_account_activity_page(
        scope,
        date_range=date_range,
        role_filter=role_filter,
        location_filter=location_filter,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(page.recent_table_headers)
    for row in page.recent_rows:
        writer.writerow([row.user_name, row.method_label, row.device_label, row.location_label, row.result_label])
    return buffer.getvalue()