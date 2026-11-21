"""Create / edit institution role page (CA 03 — roles)."""

from __future__ import annotations

from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.identity_models import InstitutionRole, InstitutionRoleAssignment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.rbac_policy import validate_custom_permissions
from app.modules.college_admin.schemas import (
    CreateEditRoleAccessToggle,
    CreateEditRoleAssignedUser,
    CreateEditRoleFormValues,
    CreateEditRolePageRead,
    CreateEditRolePermissionCell,
    CreateEditRolePermissionGroup,
    CreateEditRolePermissionRow,
    CreateEditRolePermissionToggle,
    CreateEditRoleSavePayload,
    InstitutionFieldMeta,
    InstitutionFieldOption,
)

_ACTION_COLUMNS = ("view", "create", "edit", "approve", "export")
_COLUMN_LABELS = ["Permission", "View", "Create", "Edit", "Approve", "Export"]

_P = Permission

_MATRIX_SPEC: list[tuple[str, str, list[tuple[str, str, dict[str, str | None]]]]] = [
    (
        "examinations",
        "Examinations",
        [
            (
                "exam_sessions",
                "Exam sessions & timetable",
                {
                    "view": _P.EXAMINATION_CELL_SESSION_READ.value,
                    "create": _P.EXAMINATION_CELL_SESSION_MANAGE.value,
                    "edit": _P.EXAMINATION_CELL_SESSION_MANAGE.value,
                    "approve": _P.EXAMINATION_CELL_TIMETABLE_APPROVE.value,
                    "export": _P.EXAMINATION_CELL_DOCUMENT_GENERATE.value,
                },
            ),
            (
                "hall_tickets",
                "Hall tickets",
                {
                    "view": _P.EXAMINATION_CELL_HALL_TICKET_READ.value,
                    "create": _P.EXAMINATION_CELL_HALL_TICKET_MANAGE.value,
                    "edit": _P.EXAMINATION_CELL_HALL_TICKET_MANAGE.value,
                    "approve": _P.EXAMINATION_CELL_HALL_TICKET_PUBLISH.value,
                    "export": _P.EXAMINATION_CELL_DOCUMENT_GENERATE.value,
                },
            ),
            (
                "marks_entry",
                "Marks entry",
                {
                    "view": _P.EXAMINATION_CELL_MARKS_READ.value,
                    "create": _P.EXAMINATION_CELL_MARKS_ENTER.value,
                    "edit": _P.EXAMINATION_CELL_MARKS_MANAGE.value,
                    "approve": None,
                    "export": None,
                },
            ),
            (
                "result_processing",
                "Result processing",
                {
                    "view": _P.EXAMINATION_CELL_PUBLICATION_READ.value,
                    "create": None,
                    "edit": _P.EXAMINATION_CELL_MARKS_MODERATE.value,
                    "approve": _P.EXAMINATION_CELL_RESULT_APPROVE.value,
                    "export": _P.EXAMINATION_CELL_DOCUMENT_GENERATE.value,
                },
            ),
        ],
    ),
    (
        "students",
        "Students",
        [
            (
                "student_profiles",
                "Student profiles",
                {
                    "view": _P.STUDENT_ADMIN_READ.value,
                    "create": _P.STUDENT_ADMIN_MANAGE.value,
                    "edit": _P.STUDENT_ADMIN_MANAGE.value,
                    "approve": None,
                    "export": None,
                },
            ),
            (
                "exam_eligibility",
                "Exam eligibility",
                {
                    "view": _P.EXAMINATION_CELL_ELIGIBILITY_READ.value,
                    "create": _P.EXAMINATION_CELL_ELIGIBILITY_MANAGE.value,
                    "edit": _P.EXAMINATION_CELL_ELIGIBILITY_MANAGE.value,
                    "approve": None,
                    "export": _P.EXAMINATION_CELL_DOCUMENT_GENERATE.value,
                },
            ),
        ],
    ),
    (
        "finance",
        "Finance",
        [
            (
                "fee_dues",
                "Fee dues (for hall tickets)",
                {
                    "view": _P.FINANCE_PAYMENT_READ.value,
                    "create": None,
                    "edit": None,
                    "approve": None,
                    "export": None,
                },
            ),
        ],
    ),
]

_BASE_ROLE_OPTIONS: list[tuple[Role, str]] = [
    (Role.DEPARTMENT_ADMIN, "Department Admin"),
    (Role.EXAMINATION_CELL, "Examination Cell"),
    (Role.FINANCE_STAFF, "Finance Staff"),
    (Role.ACCOUNTS_STAFF, "Accounts Staff"),
    (Role.FACULTY, "Faculty"),
    (Role.HR_STAFF, "HR Staff"),
    (Role.HOSTEL_ADMIN, "Hostel Admin"),
    (Role.LIBRARIAN, "Librarian"),
]

_SCOPE_OPTIONS: list[tuple[str, str]] = [
    ("whole_college", "Whole college"),
    ("department", "Department only"),
    ("campus", "Campus only"),
]

_ROLE_DETAILS_FIELD_META = [
    InstitutionFieldMeta(key="name", label="Role name", required=True, input_type="text"),
    InstitutionFieldMeta(key="role_code", label="Role code", required=True, input_type="text"),
    InstitutionFieldMeta(key="base_role", label="Based on", required=False, input_type="select"),
    InstitutionFieldMeta(key="scope", label="Scope", required=True, input_type="select"),
    InstitutionFieldMeta(key="description", label="Description", required=False, input_type="textarea"),
]

_ACCESS_TOGGLE_META: list[tuple[str, str, str]] = [
    ("require_mfa", "Require MFA", "Mandatory for this role"),
    ("restrict_campus_network", "Restrict to campus network", "Block logins from outside college IP"),
    ("time_bound_access", "Time-bound access", "Expires at end of exam session"),
]


def _permission_lookup() -> dict[tuple[str, str], str | None]:
    mapping: dict[tuple[str, str], str | None] = {}
    for _, _, rows in _MATRIX_SPEC:
        for row_key, _, actions in rows:
            for column_key, code in actions.items():
                mapping[(row_key, column_key)] = code
    return mapping


_PERMISSION_LOOKUP = _permission_lookup()


def _build_permission_groups(granted: set[str]) -> list[CreateEditRolePermissionGroup]:
    groups: list[CreateEditRolePermissionGroup] = []
    for group_key, group_label, rows in _MATRIX_SPEC:
        built_rows: list[CreateEditRolePermissionRow] = []
        for row_key, row_label, actions in rows:
            cells: list[CreateEditRolePermissionCell] = []
            for column_key in _ACTION_COLUMNS:
                code = actions.get(column_key)
                applicable = code is not None
                checked = applicable and code in granted
                cells.append(
                    CreateEditRolePermissionCell(
                        column_key=column_key,
                        applicable=applicable,
                        checked=checked,
                    )
                )
            built_rows.append(CreateEditRolePermissionRow(row_key=row_key, label=row_label, cells=cells))
        groups.append(
            CreateEditRolePermissionGroup(group_key=group_key, group_label=group_label, rows=built_rows)
        )
    return groups


def _granted_from_toggles(toggles: list[CreateEditRolePermissionToggle]) -> list[str]:
    granted: set[str] = set()
    for toggle in toggles:
        if not toggle.checked:
            continue
        code = _PERMISSION_LOOKUP.get((toggle.row_key, toggle.column_key))
        if code:
            granted.add(code)
    return sorted(granted)


def _role_settings_dict(form: CreateEditRoleFormValues) -> dict[str, Any]:
    return {
        "scope": form.scope,
        "require_mfa": form.require_mfa,
        "restrict_campus_network": form.restrict_campus_network,
        "time_bound_access": form.time_bound_access,
    }


def _form_from_role(role: InstitutionRole | None) -> CreateEditRoleFormValues:
    settings = (role.role_settings or {}) if role else {}
    if role:
        return CreateEditRoleFormValues(
            name=role.name,
            role_code=role.role_code,
            base_role=role.base_role.value,
            scope=str(settings.get("scope") or "whole_college"),
            description=role.description,
            require_mfa=bool(settings.get("require_mfa")),
            restrict_campus_network=bool(settings.get("restrict_campus_network")),
            time_bound_access=bool(settings.get("time_bound_access")),
        )
    return CreateEditRoleFormValues(
        name="",
        role_code="",
        base_role=Role.DEPARTMENT_ADMIN.value,
        scope="whole_college",
        description="",
        require_mfa=True,
        restrict_campus_network=True,
        time_bound_access=False,
    )


def _subtitle(role: InstitutionRole | None) -> str:
    if role:
        return f"Define what the {role.name} role can see and do"
    return "Define what this role can see and do"


async def _assigned_users(
    tenant_id: PydanticObjectId,
    role_id: PydanticObjectId,
    limit: int = 2,
) -> tuple[list[CreateEditRoleAssignedUser], str | None]:
    assignments = await InstitutionRoleAssignment.find(
        Eq(InstitutionRoleAssignment.tenant_id, tenant_id),
        Eq(InstitutionRoleAssignment.institution_role_id, role_id),
        Eq(InstitutionRoleAssignment.revoked_at, None),
    ).sort("-assigned_at").to_list()
    total = len(assignments)
    if not assignments:
        return [], None

    rows: list[CreateEditRoleAssignedUser] = []
    for assignment in assignments[:limit]:
        user = await User.get(assignment.user_id)
        if user is None:
            continue
        employee = await EmployeeRecord.find_one(
            Eq(EmployeeRecord.tenant_id, tenant_id),
            Eq(EmployeeRecord.user_id, assignment.user_id),
        )
        subtitle = employee.designation if employee and employee.designation else user.role.value.replace("_", " ").title()
        rows.append(
            CreateEditRoleAssignedUser(
                user_id=str(user.id),
                name=user.full_name,
                subtitle=subtitle,
                detail_href=f"/college-admin/users/role-assignment?userId={user.id}&roleId={role_id}",
            )
        )
    more: str | None = None
    remaining = total - len(rows)
    if remaining > 0:
        more = f"+ {remaining} more"
    return rows, more


async def get_create_edit_role_page(
    scope: AccessScope,
    role_id: PydanticObjectId | None = None,
) -> CreateEditRolePageRead:
    authorize(scope, Permission.INSTITUTION_ROLE_READ)
    tenant_id = require_college_tenant_scope(scope)

    role: InstitutionRole | None = None
    if role_id is not None:
        role = await InstitutionRole.get(role_id)
        if role is None or role.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Institution role not found", status_code=404)

    is_create = role is None
    can_save = is_create or not role.is_system
    granted = set(role.granted_permissions) if role else set()

    form = _form_from_role(role)
    access_toggles = [
        CreateEditRoleAccessToggle(
            key=key,
            label=label,
            description=description,
            checked=bool(getattr(form, key)),
        )
        for key, label, description in _ACCESS_TOGGLE_META
    ]

    assigned_users: list[CreateEditRoleAssignedUser] = []
    more_users_label: str | None = None
    assign_href = "/college-admin/users/role-assignment"
    if role:
        assigned_users, more_users_label = await _assigned_users(tenant_id, role.id)
        assign_href = f"/college-admin/users/role-assignment?roleId={role.id}"

    badge_label = "Custom role" if is_create or not role.is_system else "System role"
    badge_tone = "info" if badge_label == "Custom role" else "muted"

    return CreateEditRolePageRead(
        page_title="Create / Edit Role",
        page_subtitle=_subtitle(role),
        back_href="/college-admin/users/role-management-dashboard",
        back_label="Back",
        cancel_href="/college-admin/users/role-management-dashboard",
        cancel_label="Cancel",
        save_label="Save role",
        type_badge_label=badge_label,
        type_badge_tone=badge_tone,
        role_details_section_title="Role details",
        module_permissions_section_title="Module permissions",
        access_rules_section_title="Access rules",
        users_with_role_section_title="Users with this role",
        assign_users_label="Assign",
        assign_users_href=assign_href,
        permission_columns=_COLUMN_LABELS,
        permission_groups=_build_permission_groups(granted),
        access_toggles=access_toggles,
        assigned_users=assigned_users,
        more_users_label=more_users_label,
        base_role_options=[InstitutionFieldOption(value=r.value, label=label) for r, label in _BASE_ROLE_OPTIONS],
        scope_options=[InstitutionFieldOption(value=value, label=label) for value, label in _SCOPE_OPTIONS],
        role_details_field_meta=_ROLE_DETAILS_FIELD_META,
        form=form,
        role_id=str(role.id) if role else None,
        is_create=is_create,
        can_save=can_save,
        footer_note="Role changes take effect at the next login for every assigned user.",
        generated_at=utcnow(),
    )


async def save_create_edit_role(scope: AccessScope, payload: CreateEditRoleSavePayload) -> CreateEditRolePageRead:
    authorize(scope, Permission.INSTITUTION_ROLE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)

    granted = _granted_from_toggles(payload.permission_toggles)
    try:
        validated_granted, _ = validate_custom_permissions(
            granted,
            [],
            base_role=Role(payload.form.base_role),
        )
    except (ValueError, TypeError) as exc:
        raise AppError(code="VALIDATION_ERROR", message=str(exc), status_code=422) from exc

    role_settings = _role_settings_dict(payload.form)
    name = payload.form.name.strip()
    code = payload.form.role_code.strip().upper()
    if len(name) < 2:
        raise AppError(code="VALIDATION_ERROR", message="Role name is required", status_code=422)
    if len(code) < 2:
        raise AppError(code="VALIDATION_ERROR", message="Role code is required", status_code=422)

    role_id: PydanticObjectId | None = None
    if payload.role_id and payload.role_id.strip():
        role_id = to_object_id(payload.role_id, "role id")

    if role_id is None:
        existing = await InstitutionRole.find_one(
            Eq(InstitutionRole.tenant_id, tenant_id),
            Eq(InstitutionRole.role_code, code),
        )
        if existing is not None:
            raise AppError(code="CONFLICT", message="Role code already exists", status_code=409)
        doc = InstitutionRole(
            tenant_id=tenant_id,
            role_code=code,
            name=name,
            description=payload.form.description,
            base_role=Role(payload.form.base_role),
            granted_permissions=validated_granted,
            denied_permissions=[],
            role_settings=role_settings,
            updated_by=scope.user_id,
        )
        await doc.insert()
        await record_audit(
            actor_id=scope.user_id,
            action="institution.role.created",
            resource_type="institution_role",
            resource_id=str(doc.id),
            tenant_id=tenant_id,
            metadata={"role_code": code},
        )
        return await get_create_edit_role_page(scope, doc.id)

    doc = await InstitutionRole.get(role_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Institution role not found", status_code=404)
    if doc.is_system:
        raise AppError(code="FORBIDDEN", message="System roles cannot be modified", status_code=403)

    if code != doc.role_code:
        conflict = await InstitutionRole.find_one(
            Eq(InstitutionRole.tenant_id, tenant_id),
            Eq(InstitutionRole.role_code, code),
        )
        if conflict is not None and conflict.id != doc.id:
            raise AppError(code="CONFLICT", message="Role code already exists", status_code=409)
        doc.role_code = code

    doc.name = name
    doc.description = payload.form.description
    doc.base_role = Role(payload.form.base_role)
    doc.granted_permissions = validated_granted
    doc.role_settings = role_settings
    doc.version += 1
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    await record_audit(
        actor_id=scope.user_id,
        action="institution.role.updated",
        resource_type="institution_role",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
    )
    return await get_create_edit_role_page(scope, doc.id)


async def get_create_edit_role_page_by_id(scope: AccessScope, role_id_raw: str | None) -> CreateEditRolePageRead:
    role_id: PydanticObjectId | None = None
    if role_id_raw and role_id_raw.strip():
        role_id = to_object_id(role_id_raw, "role id")
    return await get_create_edit_role_page(scope, role_id)