"""Permission management matrix (CA 03 — permissions)."""

from __future__ import annotations

import csv
import io
from collections import defaultdict
from zoneinfo import ZoneInfo

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.college_admin.identity_models import InstitutionRole
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.rbac_policy import validate_custom_permissions
from app.modules.college_admin.schemas import (
    PermissionManagementPageRead,
    PermissionManagementSavePayload,
    PermissionMatrixCell,
    PermissionMatrixColumn,
    PermissionMatrixGroup,
    PermissionMatrixRow,
)

_IST = ZoneInfo("Asia/Kolkata")
_P = Permission

_MATRIX_COLUMNS: list[tuple[Role, str]] = [
    (Role.DEPARTMENT_ADMIN, "Dept Admin"),
    (Role.FACULTY, "Faculty"),
    (Role.STUDENT, "Student"),
    (Role.ACCOUNTS_STAFF, "Accounts"),
    (Role.HR_STAFF, "HR Staff"),
    (Role.LIBRARIAN, "Librarian"),
    (Role.HOSTEL_ADMIN, "Hostel"),
    (Role.EXAMINATION_CELL, "Exam Cell"),
]

_MATRIX_ROWS: list[tuple[str, str, list[tuple[str, str, Permission]]]] = [
    (
        "students_academics",
        "Students & Academics",
        [
            ("student_profiles_view", "View student profiles", _P.STUDENT_ADMIN_READ),
            ("student_records_edit", "Edit student records", _P.STUDENT_ADMIN_MANAGE),
            ("attendance_corrections_approve", "Approve attendance corrections", _P.ATTENDANCE_ADMIN_MANAGE),
            ("internal_marks_enter", "Enter internal marks", _P.EXAMINATION_CELL_MARKS_ENTER),
        ],
    ),
    (
        "finance",
        "Finance",
        [
            ("fee_dues_view", "View fee dues", _P.FINANCE_PAYMENT_READ),
            ("payments_collect", "Collect payments", _P.FINANCE_OFFLINE_COLLECT),
            ("refunds_approve", "Approve refunds", _P.FINANCE_REFUND_APPROVE),
        ],
    ),
    (
        "hr_payroll",
        "HR & Payroll",
        [
            ("staff_records_view", "View staff records", _P.HR_EMPLOYEE_READ),
            ("payroll_process", "Process payroll", _P.HR_PAYROLL_PREPARE),
        ],
    ),
    (
        "library_hostel",
        "Library & Hostel",
        [
            ("library_circulation", "Issue / return books", _P.LIBRARY_CIRCULATION_MANAGE),
            ("hostel_allocate", "Allocate hostel rooms", _P.HOSTEL_ALLOCATION_MANAGE),
        ],
    ),
    (
        "examinations",
        "Examinations",
        [
            ("results_publish", "Publish results", _P.EXAMINATION_CELL_PUBLICATION_PUBLISH),
            ("hall_tickets_download", "Download hall tickets", _P.EXAMINATION_CELL_HALL_TICKET_READ),
        ],
    ),
]


def _snapshot_label(when) -> str:
    local = as_utc_aware(when).astimezone(_IST)
    return local.strftime("Live snapshot · %d %b %Y, %H:%M IST")


def _effective_permissions(role: InstitutionRole | None, base_role: Role) -> set[str]:
    if role is None:
        return {p.value for p in permissions_for_role(base_role)}
    granted = list(role.granted_permissions)
    if not granted:
        granted = [p.value for p in permissions_for_role(role.base_role)]
    effective = set(granted) - set(role.denied_permissions or [])
    return effective


def _column_key(role: InstitutionRole | None, base_role: Role) -> str:
    if role is not None:
        return str(role.id)
    return f"base:{base_role.value}"


async def _resolve_role_columns(
    tenant_id: PydanticObjectId,
) -> list[tuple[InstitutionRole | None, Role, str]]:
    roles = await InstitutionRole.find(Eq(InstitutionRole.tenant_id, tenant_id)).to_list()
    by_base: dict[Role, InstitutionRole] = {}
    for role in roles:
        if not role.is_active:
            continue
        current = by_base.get(role.base_role)
        if current is None:
            by_base[role.base_role] = role
            continue
        if role.is_system and not current.is_system:
            by_base[role.base_role] = role
    resolved: list[tuple[InstitutionRole | None, Role, str]] = []
    for base_role, label in _MATRIX_COLUMNS:
        resolved.append((by_base.get(base_role), base_role, label))
    return resolved


def _build_matrix(
    resolved_columns: list[tuple[InstitutionRole | None, Role, str]],
    *,
    can_manage: bool,
) -> tuple[list[PermissionMatrixColumn], list[PermissionMatrixGroup], list[str]]:
    columns: list[PermissionMatrixColumn] = []
    for role, base_role, label in resolved_columns:
        editable = can_manage and role is not None and not role.is_system
        columns.append(
            PermissionMatrixColumn(
                column_key=_column_key(role, base_role),
                institution_role_id=str(role.id) if role else None,
                label=label,
                editable=editable,
            )
        )

    groups: list[PermissionMatrixGroup] = []
    for group_key, group_label, rows_spec in _MATRIX_ROWS:
        built_rows: list[PermissionMatrixRow] = []
        for row_key, row_label, perm in rows_spec:
            code = perm.value
            cells: list[PermissionMatrixCell] = []
            for role, base_role, _ in resolved_columns:
                effective = _effective_permissions(role, base_role)
                col_key = _column_key(role, base_role)
                editable = can_manage and role is not None and not role.is_system
                cells.append(
                    PermissionMatrixCell(
                        column_key=col_key,
                        checked=code in effective,
                        editable=editable,
                    )
                )
            built_rows.append(
                PermissionMatrixRow(
                    row_key=row_key,
                    label=row_label,
                    permission_code=code,
                    cells=cells,
                )
            )
        groups.append(PermissionMatrixGroup(group_key=group_key, group_label=group_label, rows=built_rows))

    permission_columns = ["Permission", *[c.label for c in columns]]
    return columns, groups, permission_columns


async def get_permission_management_page(scope: AccessScope) -> PermissionManagementPageRead:
    authorize(scope, Permission.INSTITUTION_ROLE_READ)
    tenant_id = require_college_tenant_scope(scope)
    can_manage = Permission.INSTITUTION_ROLE_MANAGE in scope.effective_permissions

    resolved = await _resolve_role_columns(tenant_id)
    columns, groups, permission_columns = _build_matrix(resolved, can_manage=can_manage)
    generated = utcnow()

    return PermissionManagementPageRead(
        page_title="Permission Management",
        page_subtitle="Compare and adjust module permissions for every role",
        export_matrix_label="Export matrix",
        save_changes_label="Save changes",
        matrix_section_title="Permission matrix",
        matrix_legend="✓ = role has access",
        permission_columns=permission_columns,
        columns=columns,
        groups=groups,
        unsaved_changes_title="unsaved changes",
        unsaved_changes_note="Changes will apply after you confirm with Save changes.",
        change_on_label="On",
        change_off_label="Off",
        can_save=can_manage,
        footer_disclaimer="Live institution role permissions · Matrix reflects assigned grants per role · All times IST",
        footer_snapshot_label=_snapshot_label(generated),
        generated_at=generated,
    )


def permission_matrix_csv(scope: AccessScope, page: PermissionManagementPageRead) -> str:
    authorize(scope, Permission.INSTITUTION_ROLE_READ)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(page.permission_columns)
    for group in page.groups:
        writer.writerow([group.group_label] + [""] * (len(page.permission_columns) - 1))
        for row in group.rows:
            values = [row.label]
            for idx, col in enumerate(page.columns):
                cell = row.cells[idx]
                values.append("Yes" if cell.checked else "No")
            writer.writerow(values)
    return buffer.getvalue()


async def save_permission_management_matrix(
    scope: AccessScope,
    payload: PermissionManagementSavePayload,
) -> PermissionManagementPageRead:
    authorize(scope, Permission.INSTITUTION_ROLE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    if not payload.changes:
        return await get_permission_management_page(scope)

    resolved = await _resolve_role_columns(tenant_id)
    role_by_id: dict[str, InstitutionRole] = {
        str(role.id): role for role, _, _ in resolved if role is not None
    }

    grouped: dict[str, list[tuple[str, bool]]] = defaultdict(list)
    for change in payload.changes:
        role = role_by_id.get(change.institution_role_id)
        if role is None:
            raise AppError(code="VALIDATION_ERROR", message="Unknown institution role in change", status_code=422)
        if role.is_system:
            raise AppError(code="FORBIDDEN", message="System roles cannot be modified", status_code=403)
        grouped[change.institution_role_id].append((change.permission_code, change.granted))

    for role_id_str, deltas in grouped.items():
        role = role_by_id[role_id_str]
        granted = set(_effective_permissions(role, role.base_role))

        for code, is_granted in deltas:
            if is_granted:
                granted.add(code)
            else:
                granted.discard(code)

        try:
            validated_granted, _ = validate_custom_permissions(
                sorted(granted),
                list(role.denied_permissions or []),
                base_role=role.base_role,
            )
        except (ValueError, TypeError) as exc:
            raise AppError(code="VALIDATION_ERROR", message=str(exc), status_code=422) from exc

        role.granted_permissions = validated_granted
        role.version += 1
        role.updated_at = utcnow()
        role.updated_by = scope.user_id
        await role.save()
        await record_audit(
            actor_id=scope.user_id,
            action="institution.permission_matrix.updated",
            resource_type="institution_role",
            resource_id=str(role.id),
            tenant_id=tenant_id,
            metadata={"delta_count": len(deltas)},
        )

    return await get_permission_management_page(scope)


async def get_permission_management_page_export(scope: AccessScope) -> str:
    page = await get_permission_management_page(scope)
    return permission_matrix_csv(scope, page)