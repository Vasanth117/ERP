"""User account activation / suspension page (CA 03)."""

from __future__ import annotations

import csv
import io
import math
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.auth.session import revoke_all_for_user
from app.modules.college_admin.identity_models import (
    AccessHistoryEvent,
    InstitutionAccountStatus,
    InstitutionUser,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    AccountStatusInfoCard,
    AccountStatusPageRead,
    AccountStatusSuspendFormValues,
    AccountStatusSuspendPayload,
    AccountStatusSuspendResponse,
    AccountStatusTab,
    AccountStatusTableRow,
    InstitutionFieldMeta,
    InstitutionFieldOption,
    PoliciesPagination,
)
from app.modules.college_admin.user_management_service import _append_access_history
from app.modules.tenants.models import Department

_IST = ZoneInfo("Asia/Kolkata")
_PAGE_SIZE = 10

_TAB_ORDER = ("suspended", "pending_activation", "deactivated")

_TAB_STATUS: dict[str, InstitutionAccountStatus] = {
    "suspended": InstitutionAccountStatus.SUSPENDED,
    "pending_activation": InstitutionAccountStatus.INVITED,
    "deactivated": InstitutionAccountStatus.DEACTIVATED,
}

_REASON_OPTIONS: list[tuple[str, str]] = [
    ("disciplinary", "Disciplinary action"),
    ("fee_default", "Fee default"),
    ("policy_violation", "Policy violation"),
    ("security", "Security concern"),
    ("other", "Other"),
]

_REASON_DETAIL: dict[str, str] = {
    "disciplinary": "Disciplinary – ragging inquiry",
    "fee_default": "Fee default > 180 days",
    "policy_violation": "Policy violation",
    "security": "Security concern",
    "other": "Administrative suspension",
}

_ROLE_DISPLAY: dict[Role, str] = {
    Role.STUDENT: "Student",
    Role.FACULTY: "Faculty",
    Role.DEPARTMENT_ADMIN: "Dept Admin",
    Role.ACCOUNTS_STAFF: "Accounts",
    Role.FINANCE_STAFF: "Finance",
    Role.HR_STAFF: "HR Staff",
    Role.EXAMINATION_CELL: "Exam Cell",
    Role.LIBRARIAN: "Librarian",
    Role.HOSTEL_ADMIN: "Hostel",
    Role.COLLEGE_ADMIN: "College Admin",
}

_SUSPEND_FIELD_META = [
    InstitutionFieldMeta(key="user_id", label="User", required=True, field_type="select"),
    InstitutionFieldMeta(key="reason_code", label="Reason", required=True, field_type="select"),
    InstitutionFieldMeta(key="effective_from", label="Effective from", required=True, field_type="date"),
    InstitutionFieldMeta(key="review_date", label="Review date", required=False, field_type="date"),
    InstitutionFieldMeta(key="notes", label="Notes", required=True, field_type="textarea"),
]


def _format_short_day(when: datetime | None) -> str:
    if when is None:
        return "—"
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("%d %b")


def _parse_date(raw: str, field: str) -> datetime:
    try:
        parsed = date.fromisoformat(raw.strip())
    except ValueError as exc:
        raise AppError(code="VALIDATION_ERROR", message=f"Invalid {field}", status_code=422) from exc
    return datetime.combine(parsed, time.min, tzinfo=_IST)


def _reason_label(institution: InstitutionUser) -> str:
    if institution.suspension_reason and len(institution.suspension_reason) > 3:
        return institution.suspension_reason
    code = institution.suspension_reason_code or "other"
    return _REASON_DETAIL.get(code, institution.suspension_reason or "—")


def _review_cell(institution: InstitutionUser) -> tuple[str, str]:
    code = institution.suspension_review_status
    if code == "on_hold":
        return "On hold", "muted"
    if code == "scheduled":
        return "Scheduled", "purple"
    if code == "in_review":
        return "In review", "info"
    if institution.suspension_review_at:
        local = as_utc_aware(institution.suspension_review_at).astimezone(_IST)
        return f"Due {local.strftime('%d %b')}", "warning"
    return "In review", "info"


def _role_label(user: User) -> str:
    return _ROLE_DISPLAY.get(user.role, user.role.value.replace("_", " ").title())


async def _department_name(tenant_id: PydanticObjectId, department_id: PydanticObjectId | None) -> str:
    if department_id is None:
        return "—"
    dept = await Department.get(department_id)
    return dept.name if dept else "—"


async def _institution_map(tenant_id: PydanticObjectId, user_ids: list[PydanticObjectId]) -> dict[PydanticObjectId, InstitutionUser]:
    if not user_ids:
        return {}
    rows = await InstitutionUser.find(
        Eq(InstitutionUser.tenant_id, tenant_id),
    ).to_list()
    return {row.user_id: row for row in rows if row.user_id in set(user_ids)}


async def _tab_count(tenant_id: PydanticObjectId, status: InstitutionAccountStatus) -> int:
    return await InstitutionUser.find(
        Eq(InstitutionUser.tenant_id, tenant_id),
        Eq(InstitutionUser.account_status, status),
    ).count()


async def _table_rows(
    tenant_id: PydanticObjectId,
    tab_key: str,
    *,
    page: int,
) -> tuple[list[AccountStatusTableRow], int]:
    status = _TAB_STATUS[tab_key]
    institution_rows = await InstitutionUser.find(
        Eq(InstitutionUser.tenant_id, tenant_id),
        Eq(InstitutionUser.account_status, status),
    ).sort("-updated_at").to_list()
    total = len(institution_rows)
    start = (page - 1) * _PAGE_SIZE
    slice_rows = institution_rows[start : start + _PAGE_SIZE]

    table: list[AccountStatusTableRow] = []
    for institution in slice_rows:
        user = await User.get(institution.user_id)
        if user is None or user.tenant_id != tenant_id:
            continue
        review_label: str | None = None
        review_tone: str | None = None
        since_label = "—"
        reason_label = "—"
        extra_label = "—"

        if tab_key == "suspended":
            reason_label = _reason_label(institution)
            since_label = _format_short_day(institution.suspension_effective_from or institution.suspended_at)
            review_label, review_tone = _review_cell(institution)
        elif tab_key == "pending_activation":
            since_label = _format_short_day(institution.created_at)
            extra_label = await _department_name(tenant_id, institution.department_id or user.department_id)
            review_label, review_tone = "Pending invite", "warning"
        else:
            reason_label = institution.suspension_reason or "Account deactivated"
            since_label = _format_short_day(institution.updated_at)
            review_label, review_tone = "Deactivated", "muted"

        table.append(
            AccountStatusTableRow(
                user_id=str(user.id),
                user_name=user.full_name,
                role_label=_role_label(user),
                reason_label=reason_label,
                since_label=since_label,
                review_label=review_label or "—",
                review_tone=review_tone or "muted",
                department_label=extra_label,
                detail_href=f"/college-admin/users/user-details?userId={user.id}",
            )
        )
    return table, total


def _pagination(page: int, total: int) -> PoliciesPagination:
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 1
    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else [1]
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]
    return PoliciesPagination(
        page=page,
        page_size=_PAGE_SIZE,
        total=total,
        total_pages=total_pages,
        page_numbers=page_numbers,
        has_previous=page > 1 and bool(total),
        has_next=page < total_pages,
    )


async def _user_options_for_suspend(tenant_id: PydanticObjectId) -> list[InstitutionFieldOption]:
    institutions = await InstitutionUser.find(
        Eq(InstitutionUser.tenant_id, tenant_id),
        Eq(InstitutionUser.account_status, InstitutionAccountStatus.ACTIVE),
    ).to_list()
    options: list[InstitutionFieldOption] = []
    for institution in institutions[:200]:
        user = await User.get(institution.user_id)
        if user is None or not user.is_active:
            continue
        options.append(InstitutionFieldOption(value=str(user.id), label=user.full_name))
    options.sort(key=lambda row: row.label.lower())
    return options


def _default_suspend_form() -> AccountStatusSuspendFormValues:
    today = utcnow().astimezone(_IST).date()
    review = today + timedelta(days=30)
    return AccountStatusSuspendFormValues(
        user_id="",
        reason_code="disciplinary",
        effective_from=today.isoformat(),
        review_date=review.isoformat(),
        notes="",
    )


def _table_headers(tab_key: str) -> list[str]:
    if tab_key == "suspended":
        return ["User", "Role", "Reason", "Since", "Review"]
    if tab_key == "pending_activation":
        return ["User", "Role", "Invited on", "Department", "Status"]
    return ["User", "Role", "Reason", "Since", "Status"]


async def get_account_status_page(
    scope: AccessScope,
    *,
    tab: str = "suspended",
    page: int = 1,
) -> AccountStatusPageRead:
    authorize(scope, Permission.INSTITUTION_USER_READ)
    tenant_id = require_college_tenant_scope(scope)
    can_suspend = Permission.INSTITUTION_USER_MANAGE in scope.effective_permissions

    if tab not in _TAB_STATUS:
        tab = "suspended"

    tabs: list[AccountStatusTab] = []
    for key in _TAB_ORDER:
        count = await _tab_count(tenant_id, _TAB_STATUS[key])
        label = {
            "suspended": "Suspended",
            "pending_activation": "Pending activation",
            "deactivated": "Deactivated",
        }[key]
        tabs.append(
            AccountStatusTab(
                key=key,
                label=label,
                count=count,
                active=key == tab,
            )
        )

    rows, total = await _table_rows(tenant_id, tab, page=page)
    generated = utcnow()

    table_footer = {
        "suspended": f"{total:,} suspended accounts" if tab == "suspended" else "",
        "pending_activation": f"{total:,} pending activations" if tab == "pending_activation" else "",
        "deactivated": f"{total:,} deactivated accounts" if tab == "deactivated" else "",
    }[tab]

    return AccountStatusPageRead(
        page_title="User Account Activation / Suspension",
        page_subtitle="Activate pending accounts and manage suspensions",
        export_label="Export",
        suspend_account_label="Suspend account",
        tabs=tabs,
        active_tab=tab,
        table_headers=_table_headers(tab),
        table_rows=rows,
        table_footer_label=table_footer or f"{total:,} records",
        pagination=_pagination(page, total),
        suspend_form_section_title="Suspend an account",
        suspend_field_meta=_SUSPEND_FIELD_META,
        reason_options=[InstitutionFieldOption(value=c, label=l) for c, l in _REASON_OPTIONS],
        user_options=await _user_options_for_suspend(tenant_id),
        suspend_form=_default_suspend_form(),
        what_happens_title="What happens",
        what_happens_cards=[
            AccountStatusInfoCard(
                key="login_blocked",
                title="Login is blocked",
                description="Active sessions end immediately",
                icon_key="lock",
            ),
            AccountStatusInfoCard(
                key="data_preserved",
                title="Data is preserved",
                description="Records stay unchanged",
                icon_key="database",
            ),
            AccountStatusInfoCard(
                key="user_notified",
                title="User is notified",
                description="Email with reason and contact",
                icon_key="mail",
            ),
        ],
        cancel_href="/college-admin/users/user-management-dashboard",
        cancel_label="Cancel",
        submit_suspend_label="Suspend account",
        footer_note="Changes are saved to the audit log with your name and time.",
        footer_snapshot_label=generated.astimezone(_IST).strftime("Live snapshot · %d %b %Y, %H:%M IST"),
        can_suspend=can_suspend,
        generated_at=generated,
    )


async def submit_account_suspension(
    scope: AccessScope,
    payload: AccountStatusSuspendPayload,
) -> AccountStatusSuspendResponse:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)

    user_id = to_object_id(payload.form.user_id, "user id")
    user = await User.get(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    if user.id == scope.user_id:
        raise AppError(code="FORBIDDEN", message="You cannot suspend your own account", status_code=403)

    notes = payload.form.notes.strip()
    if len(notes) < 3:
        raise AppError(code="VALIDATION_ERROR", message="Notes are required for the audit record", status_code=422)

    reason_code = payload.form.reason_code.strip()
    reason_detail = _REASON_DETAIL.get(reason_code, "Administrative suspension")
    if notes:
        reason_detail = f"{reason_detail} — {notes}"

    effective_from = _parse_date(payload.form.effective_from, "effective from")
    review_at: datetime | None = None
    review_status = "in_review"
    if payload.form.review_date and payload.form.review_date.strip():
        review_at = _parse_date(payload.form.review_date, "review date")
        review_status = "due"

    user.is_active = False
    user.updated_at = utcnow()
    await user.save()
    await revoke_all_for_user(user.id)

    institution = await InstitutionUser.find_one(
        Eq(InstitutionUser.tenant_id, tenant_id),
        Eq(InstitutionUser.user_id, user_id),
    )
    if institution is None:
        institution = InstitutionUser(tenant_id=tenant_id, user_id=user_id)
        await institution.insert()

    institution.account_status = InstitutionAccountStatus.SUSPENDED
    institution.suspension_reason = reason_detail
    institution.suspended_at = utcnow()
    institution.suspension_reason_code = reason_code
    institution.suspension_effective_from = effective_from
    institution.suspension_review_at = review_at
    institution.suspension_review_status = review_status
    institution.suspension_notes = notes
    institution.updated_at = utcnow()
    await institution.save()

    await _append_access_history(
        tenant_id=tenant_id,
        user_id=user_id,
        actor_id=scope.user_id,
        event_type=AccessHistoryEvent.USER_SUSPENDED,
        summary="Account suspended",
        metadata={"reason_code": reason_code, "notes": notes[:120]},
    )
    await record_audit(
        actor_id=scope.user_id,
        action="institution.user.suspended",
        resource_type="user",
        resource_id=str(user_id),
        tenant_id=tenant_id,
    )

    page = await get_account_status_page(scope, tab="suspended", page=1)
    return AccountStatusSuspendResponse(page=page, message="Account suspended")


async def export_account_status_csv(scope: AccessScope, *, tab: str) -> str:
    authorize(scope, Permission.INSTITUTION_USER_READ)
    tenant_id = require_college_tenant_scope(scope)
    if tab not in _TAB_STATUS:
        tab = "suspended"
    total_pages = max(1, math.ceil((await _tab_count(tenant_id, _TAB_STATUS[tab])) / _PAGE_SIZE))
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(_table_headers(tab))
    for page in range(1, total_pages + 1):
        rows, _ = await _table_rows(tenant_id, tab, page=page)
        for row in rows:
            if tab == "pending_activation":
                writer.writerow(
                    [row.user_name, row.role_label, row.since_label, row.department_label, row.review_label],
                )
            else:
                writer.writerow([row.user_name, row.role_label, row.reason_label, row.since_label, row.review_label])
    return buffer.getvalue()