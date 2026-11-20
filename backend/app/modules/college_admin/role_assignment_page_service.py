"""Role assignment page (CA 03 — assign roles to users)."""

from __future__ import annotations

from datetime import date, datetime, time
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
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.identity_models import InstitutionRole, InstitutionRoleAssignment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.rbac_policy import actor_may_assign_role
from app.modules.college_admin.schemas import (
    InstitutionFieldMeta,
    InstitutionFieldOption,
    RoleAssignmentCurrentRoleCard,
    RoleAssignmentFormValues,
    RoleAssignmentPageRead,
    RoleAssignmentRecentRow,
    RoleAssignmentRoleOption,
    RoleAssignmentSubmitPayload,
    RoleAssignmentSubmitResponse,
    RoleAssignmentUserOption,
)
from app.modules.audit.service import record_audit
from app.modules.college_admin.user_management_service import _append_access_history
from app.modules.college_admin.identity_models import AccessHistoryEvent
from app.modules.tenants.models import Department

_IST = ZoneInfo("Asia/Kolkata")
_RECENT_LIMIT = 8

_PRIVILEGED_BASE_ROLES = frozenset(
    {
        Role.DEPARTMENT_ADMIN,
        Role.COLLEGE_ADMIN,
        Role.EXAMINATION_CELL,
        Role.FINANCE_STAFF,
        Role.ACCOUNTS_STAFF,
    }
)

_FORM_FIELD_META = [
    InstitutionFieldMeta(key="user_id", label="User", required=True, field_type="select"),
    InstitutionFieldMeta(key="institution_role_id", label="Role", required=True, field_type="select"),
    InstitutionFieldMeta(key="scope_key", label="Scope", required=True, field_type="select"),
    InstitutionFieldMeta(key="valid_from", label="Valid from", required=True, field_type="date"),
    InstitutionFieldMeta(key="valid_until", label="Valid until", required=False, field_type="date"),
    InstitutionFieldMeta(key="reason", label="Reason", required=False, field_type="textarea"),
]


def _format_ist_day(when: datetime | date | None) -> str:
    if when is None:
        return "—"
    if isinstance(when, date) and not isinstance(when, datetime):
        return when.strftime("%d %b %Y")
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("%d %b %Y")


def _snapshot_label(when: datetime) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("Live snapshot · %d %b %Y, %H:%M IST")


def _status_code(row: InstitutionRoleAssignment) -> tuple[str, str, str]:
    if row.revoked_at is not None:
        return "removed", "Removed", "muted"
    if row.assignment_status == "pending":
        return "pending", "Pending", "warning"
    return "active", "Active", "success"


def _requires_approval(role: InstitutionRole) -> bool:
    return role.base_role in _PRIVILEGED_BASE_ROLES


def _approval_notice(role_name: str) -> str:
    return f"{role_name} is a privileged role. Principal must approve before it is active."


async def _employee_id(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> str | None:
    employee = await EmployeeRecord.find_one(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.user_id, user_id),
    )
    return employee.employee_id if employee and employee.employee_id else None


async def _user_options(tenant_id: PydanticObjectId) -> list[RoleAssignmentUserOption]:
    users = await User.find(Eq(User.tenant_id, tenant_id), Eq(User.is_active, True)).sort("+full_name").limit(300).to_list()
    options: list[RoleAssignmentUserOption] = []
    for user in users:
        if user.role in {Role.SUPER_ADMIN, Role.PLATFORM_ADMIN}:
            continue
        emp = await _employee_id(tenant_id, user.id)
        suffix = emp or str(user.id)[-6:]
        options.append(
            RoleAssignmentUserOption(
                value=str(user.id),
                label=f"{user.full_name} · {suffix}",
            )
        )
    return options


async def _role_options(tenant_id: PydanticObjectId) -> list[RoleAssignmentRoleOption]:
    roles = await InstitutionRole.find(
        Eq(InstitutionRole.tenant_id, tenant_id),
        Eq(InstitutionRole.is_active, True),
    ).sort("+name").to_list()
    options: list[RoleAssignmentRoleOption] = []
    for role in roles:
        label = role.name
        if role.description and "acting" in role.description.lower():
            label = f"{role.name} (acting)"
        requires = _requires_approval(role)
        options.append(
            RoleAssignmentRoleOption(
                value=str(role.id),
                label=label,
                requires_approval=requires,
                approval_notice=_approval_notice(role.name) if requires else None,
            )
        )
    return options


async def _scope_options(tenant_id: PydanticObjectId) -> list[InstitutionFieldOption]:
    departments = await Department.find(Eq(Department.tenant_id, tenant_id)).sort("+name").to_list()
    options = [InstitutionFieldOption(value="whole_college", label="Whole college")]
    for dept in departments:
        options.append(InstitutionFieldOption(value=f"department:{dept.id}", label=dept.name))
    return options


def _scope_label_for(scope_key: str, departments: dict[str, Department]) -> str:
    if scope_key == "whole_college":
        return "Whole college"
    if scope_key.startswith("department:"):
        dept_id = scope_key.split(":", 1)[1]
        dept = departments.get(dept_id)
        return dept.name if dept else scope_key
    return scope_key


async def _current_roles(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
) -> list[RoleAssignmentCurrentRoleCard]:
    user = await User.get(user_id)
    if user is None:
        return []
    assignments = await InstitutionRoleAssignment.find(
        Eq(InstitutionRoleAssignment.tenant_id, tenant_id),
        Eq(InstitutionRoleAssignment.user_id, user_id),
        Eq(InstitutionRoleAssignment.revoked_at, None),
    ).to_list()
    cards: list[RoleAssignmentCurrentRoleCard] = []
    seen: set[str] = set()
    for assignment in assignments:
        role_doc = await InstitutionRole.get(assignment.institution_role_id)
        if role_doc is None:
            continue
        status_code, status_label, status_tone = _status_code(assignment)
        scope = assignment.scope_label or "Institution-wide"
        since = _format_ist_day(assignment.valid_from or assignment.assigned_at)
        extra = f"{scope} · since {since}"
        if assignment.reason and "course" in assignment.reason.lower():
            extra = assignment.reason
        cards.append(
            RoleAssignmentCurrentRoleCard(
                role_name=role_doc.name,
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
                detail_line=extra,
            )
        )
        seen.add(role_doc.name)
    if not cards:
        dept_name = None
        if user.department_id:
            dept = await Department.get(user.department_id)
            dept_name = dept.name if dept else None
        cards.append(
            RoleAssignmentCurrentRoleCard(
                role_name=user.role.value.replace("_", " ").title(),
                status_code="active",
                status_label="Active",
                status_tone="success",
                detail_line=f"{dept_name or 'Institution'} · since {_format_ist_day(user.created_at)}",
            )
        )
    return cards


async def _recent_rows(tenant_id: PydanticObjectId) -> list[RoleAssignmentRecentRow]:
    rows = await InstitutionRoleAssignment.find(Eq(InstitutionRoleAssignment.tenant_id, tenant_id)).sort("-assigned_at").limit(
        _RECENT_LIMIT
    ).to_list()
    departments = {str(d.id): d for d in await Department.find(Eq(Department.tenant_id, tenant_id)).to_list()}
    recent: list[RoleAssignmentRecentRow] = []
    for assignment in rows:
        user = await User.get(assignment.user_id)
        role_doc = await InstitutionRole.get(assignment.institution_role_id)
        if user is None or role_doc is None:
            continue
        status_code, status_label, status_tone = _status_code(assignment)
        scope = assignment.scope_label or _scope_label_for(assignment.scope_key or "whole_college", departments)
        until = "—"
        if assignment.valid_until:
            until = _format_ist_day(assignment.valid_until)
        elif assignment.revoked_at:
            until = _format_ist_day(assignment.revoked_at)
        recent.append(
            RoleAssignmentRecentRow(
                user_name=user.full_name,
                role_name=role_doc.name,
                scope_label=scope,
                until_label=until,
                status_code=status_code,
                status_label=status_label,
                status_tone=status_tone,
            )
        )
    return recent


def _default_form(
    user_id: str | None,
    role_id: str | None,
) -> RoleAssignmentFormValues:
    today = utcnow().astimezone(_IST).date()
    return RoleAssignmentFormValues(
        user_id=user_id or "",
        institution_role_id=role_id or "",
        scope_key="whole_college",
        valid_from=today.isoformat(),
        valid_until="",
        reason="",
    )


def _parse_date(raw: str, field: str) -> datetime:
    try:
        parsed = date.fromisoformat(raw.strip())
    except ValueError as exc:
        raise AppError(code="VALIDATION_ERROR", message=f"Invalid {field} date", status_code=422) from exc
    return datetime.combine(parsed, time.min, tzinfo=_IST)


async def get_role_assignment_page(
    scope: AccessScope,
    *,
    user_id_raw: str | None = None,
    role_id_raw: str | None = None,
) -> RoleAssignmentPageRead:
    authorize(scope, Permission.INSTITUTION_ROLE_READ)
    tenant_id = require_college_tenant_scope(scope)
    can_submit = Permission.INSTITUTION_ROLE_MANAGE in scope.effective_permissions

    user_id: str | None = None
    if user_id_raw and user_id_raw.strip():
        user_id = str(to_object_id(user_id_raw, "user id"))
    role_id: str | None = None
    if role_id_raw and role_id_raw.strip():
        role_id = str(to_object_id(role_id_raw, "role id"))

    user_options = await _user_options(tenant_id)
    role_options = await _role_options(tenant_id)
    scope_options = await _scope_options(tenant_id)
    current_roles: list[RoleAssignmentCurrentRoleCard] = []
    if user_id:
        current_roles = await _current_roles(tenant_id, to_object_id(user_id, "user id"))

    selected_role = next((r for r in role_options if r.value == role_id), None)
    approval_notice = selected_role.approval_notice if selected_role and selected_role.requires_approval else None

    generated = utcnow()
    history_href = "/college-admin/users/user-access-history"
    if user_id:
        history_href = f"/college-admin/users/user-access-history?userId={user_id}"

    return RoleAssignmentPageRead(
        page_title="Role Assignment",
        page_subtitle="Assign or remove roles for users, with scope and validity",
        assignment_history_label="Assignment history",
        assignment_history_href=history_href,
        assign_role_label="Assign role",
        form_section_title="Assign a role",
        form_field_meta=_FORM_FIELD_META,
        user_options=user_options,
        role_options=role_options,
        scope_options=scope_options,
        form=_default_form(user_id, role_id),
        approval_notice=approval_notice,
        current_roles_section_title="Current roles of this user",
        current_roles=current_roles,
        recent_section_title="Recent assignments",
        recent_table_headers=["User", "Role", "Scope", "Until", "Status"],
        recent_rows=await _recent_rows(tenant_id),
        view_history_label="View history",
        view_history_href=history_href,
        cancel_href="/college-admin/users/role-management-dashboard",
        cancel_label="Cancel",
        submit_label="Send for approval",
        submit_direct_label="Assign role",
        footer_note="Changes are saved to the audit log with your name and time.",
        footer_snapshot_label=_snapshot_label(generated),
        can_submit=can_submit,
        generated_at=generated,
    )


async def submit_role_assignment(
    scope: AccessScope,
    payload: RoleAssignmentSubmitPayload,
) -> RoleAssignmentSubmitResponse:
    authorize(scope, Permission.INSTITUTION_ROLE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    privileged = Permission.INSTITUTION_PRIVILEGED_ROLE_ASSIGN in scope.effective_permissions

    user_id = to_object_id(payload.form.user_id, "user id")
    role_id = to_object_id(payload.form.institution_role_id, "institution role id")
    user = await User.get(user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    role_doc = await InstitutionRole.get(role_id)
    if role_doc is None or role_doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Institution role not found", status_code=404)

    actor_may_assign_role(scope.role, role_doc.base_role, has_privileged_grant=privileged)

    departments = {str(d.id): d for d in await Department.find(Eq(Department.tenant_id, tenant_id)).to_list()}
    scope_key = payload.form.scope_key.strip()
    scope_label = _scope_label_for(scope_key, departments)
    department_id: PydanticObjectId | None = None
    if scope_key.startswith("department:"):
        department_id = to_object_id(scope_key.split(":", 1)[1], "department id")

    valid_from = _parse_date(payload.form.valid_from, "valid from")
    valid_until: datetime | None = None
    if payload.form.valid_until and payload.form.valid_until.strip():
        valid_until = _parse_date(payload.form.valid_until, "valid until")
        if valid_until < valid_from:
            raise AppError(code="VALIDATION_ERROR", message="Valid until must be after valid from", status_code=422)

    requires_approval = _requires_approval(role_doc) and not privileged
    status = "pending" if requires_approval else "active"

    existing = await InstitutionRoleAssignment.find_one(
        Eq(InstitutionRoleAssignment.tenant_id, tenant_id),
        Eq(InstitutionRoleAssignment.user_id, user_id),
        Eq(InstitutionRoleAssignment.institution_role_id, role_id),
        Eq(InstitutionRoleAssignment.revoked_at, None),
    )
    if existing is not None:
        raise AppError(code="CONFLICT", message="User already has this role assignment", status_code=409)

    assignment = InstitutionRoleAssignment(
        tenant_id=tenant_id,
        user_id=user_id,
        institution_role_id=role_id,
        assigned_by=scope.user_id,
        assignment_status=status,
        scope_key=scope_key,
        scope_label=scope_label,
        department_id=department_id,
        valid_from=valid_from,
        valid_until=valid_until,
        reason=(payload.form.reason or "").strip() or None,
    )
    await assignment.insert()

    summary = f"Role {role_doc.name} assigned ({status})"
    await _append_access_history(
        tenant_id=tenant_id,
        user_id=user_id,
        actor_id=scope.user_id,
        event_type=AccessHistoryEvent.ROLE_ASSIGNED,
        summary=summary,
        metadata={"institution_role_id": str(role_id), "status": status},
    )
    await record_audit(
        actor_id=scope.user_id,
        action="institution.role_assignment.created",
        resource_type="institution_role_assignment",
        resource_id=str(assignment.id),
        tenant_id=tenant_id,
        metadata={"status": status, "user_id": str(user_id)},
    )

    page = await get_role_assignment_page(
        scope,
        user_id_raw=str(user_id),
        role_id_raw=str(role_id),
    )
    return RoleAssignmentSubmitResponse(
        page=page,
        assignment_id=str(assignment.id),
        status=status,
        message="Sent for approval" if status == "pending" else "Role assigned",
    )