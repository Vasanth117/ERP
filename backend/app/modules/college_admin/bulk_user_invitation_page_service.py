"""Bulk user invitation wizard (CA 03 — create & invite)."""

from __future__ import annotations

import csv
import io
import math
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.identity_models import InstitutionBulkUserInvitationDraft
from app.modules.college_admin.identity_schemas import InstitutionUserInvite
from app.modules.college_admin.models import InstitutionProfile
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    BulkUserInvitationPageRead,
    BulkUserInvitationPagination,
    BulkUserInvitationPreviewRow,
    BulkUserInvitationSendResponse,
    BulkUserInvitationStepPayload,
    BulkUserInvitationSummaryStat,
    BulkUserInvitationToggle,
    BulkUserInvitationUploadPayload,
    BulkUserInvitationWizardStep,
)
from app.modules.college_admin.user_management_service import invite_institution_user
from app.modules.tenants.models import Department
from app.repositories.user_repository import UserRepository

_user_repo = UserRepository()
_PAGE_SIZE = 6

_WIZARD_STEPS = [
    BulkUserInvitationWizardStep(key="upload", label="Upload file", step_number=1),
    BulkUserInvitationWizardStep(key="map_validate", label="Map & validate", step_number=2),
    BulkUserInvitationWizardStep(key="preview", label="Preview", step_number=3),
    BulkUserInvitationWizardStep(key="send_invites", label="Send invites", step_number=4),
]

_TEMPLATE_CSV = (
    "name,email,role,department,employee_id\n"
    "Priya Natarajan,priya.n@example.edu.in,Faculty,Computer Science,EMP-1342\n"
)

_ROLE_MAP: dict[str, Role] = {
    "faculty": Role.FACULTY,
    "teaching staff": Role.FACULTY,
    "student": Role.STUDENT,
    "hr staff": Role.HR_STAFF,
    "hr": Role.HR_STAFF,
    "accounts": Role.ACCOUNTS_STAFF,
    "lab tech": Role.FACULTY,
    "librarian": Role.LIBRARIAN,
    "hostel admin": Role.HOSTEL_ADMIN,
    "exam cell": Role.EXAMINATION_CELL,
}


def bulk_invitation_template_csv() -> str:
    return _TEMPLATE_CSV


async def _draft(scope: AccessScope) -> InstitutionBulkUserInvitationDraft:
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    if actor_id is None:
        raise AppError(code="FORBIDDEN", message="Actor required", status_code=403)
    doc = await InstitutionBulkUserInvitationDraft.find_one(
        Eq(InstitutionBulkUserInvitationDraft.tenant_id, tenant_id),
        Eq(InstitutionBulkUserInvitationDraft.actor_id, actor_id),
    )
    if doc is None:
        doc = InstitutionBulkUserInvitationDraft(tenant_id=tenant_id, actor_id=actor_id)
        await doc.insert()
    return doc


def _normalize_header(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def _parse_csv(content: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(content.strip()))
    rows: list[dict[str, Any]] = []
    for index, raw in enumerate(reader, start=1):
        mapped: dict[str, Any] = {"row_id": f"row-{index}"}
        for key, value in raw.items():
            if key is None:
                continue
            norm = _normalize_header(key)
            mapped[norm] = (value or "").strip()
        rows.append(mapped)
    return rows


def _row_field(row: dict[str, Any], *keys: str) -> str:
    for key in keys:
        if key in row and row[key]:
            return str(row[key]).strip()
    return ""


def _resolve_role(label: str) -> Role | None:
    if not label:
        return None
    return _ROLE_MAP.get(label.strip().lower())


async def _validate_rows(
    tenant_id: PydanticObjectId,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    profile = await InstitutionProfile.find_one(Eq(InstitutionProfile.tenant_id, tenant_id))
    required_domain = None
    if profile and profile.institution_email and "@" in profile.institution_email:
        required_domain = profile.institution_email.split("@", 1)[1].lower()

    departments = await Department.find(Eq(Department.tenant_id, tenant_id)).to_list()
    dept_by_name = {d.name.lower(): d for d in departments}

    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    employee_ids = {e.employee_id.lower() for e in employees if e.employee_id}

    seen_employee: set[str] = set()
    validated: list[dict[str, Any]] = []

    for row in rows:
        name = _row_field(row, "name", "full_name")
        email = _row_field(row, "email", "official_email").lower()
        role_label = _row_field(row, "role", "role_label")
        dept_label = _row_field(row, "department", "department_name")
        emp_id = _row_field(row, "employee_id", "public_id", "employee_id")

        status_code = "ready"
        status_label = "Ready"
        status_tone = "success"

        if not name or not email or "@" not in email:
            status_code, status_label, status_tone = "invalid", "Invalid row", "error"
        elif required_domain and not email.endswith(f"@{required_domain}"):
            status_code, status_label, status_tone = "domain", "Invalid domain", "error"
        elif await _user_repo.find_by_email_in_tenant(email, tenant_id) is not None:
            status_code, status_label, status_tone = "duplicate", "Duplicate email", "warning"
        elif emp_id and emp_id.lower() in employee_ids:
            status_code, status_label, status_tone = "duplicate", "Duplicate ID", "warning"
        elif emp_id and emp_id.lower() in seen_employee:
            status_code, status_label, status_tone = "duplicate", "Duplicate ID", "warning"
        elif emp_id:
            seen_employee.add(emp_id.lower())

        dept = dept_by_name.get(dept_label.lower()) if dept_label else None
        role = _resolve_role(role_label)

        validated.append(
            {
                **row,
                "full_name": name,
                "email": email,
                "role_label": role_label or (role.value if role else "—"),
                "department_label": dept_label or "—",
                "department_id": str(dept.id) if dept else None,
                "role": role.value if role else None,
                "employee_id": emp_id or None,
                "status_code": status_code,
                "status_label": status_label,
                "status_tone": status_tone,
            },
        )
    return validated


def _summary_stats(rows: list[dict[str, Any]]) -> list[BulkUserInvitationSummaryStat]:
    ready = sum(1 for r in rows if r["status_code"] == "ready")
    domain = sum(1 for r in rows if r["status_code"] == "domain")
    duplicate = sum(1 for r in rows if r["status_code"] == "duplicate")
    return [
        BulkUserInvitationSummaryStat(
            key="ready",
            label="Ready to invite",
            count=ready,
            description="Will receive email + SMS",
            tone="success",
        ),
        BulkUserInvitationSummaryStat(
            key="domain",
            label="Invalid email domain",
            count=domain,
            description="Must match institution domain",
            tone="error",
        ),
        BulkUserInvitationSummaryStat(
            key="duplicate",
            label="Duplicate employee ID",
            count=duplicate,
            description="Already exists in system",
            tone="warning",
        ),
    ]


def _paginate(rows: list[dict], page: int) -> BulkUserInvitationPagination:
    total = len(rows)
    total_pages = max(1, math.ceil(total / _PAGE_SIZE)) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)
    page_numbers = list(range(1, min(total_pages, 12) + 1)) if total_pages else []
    if total_pages > 12:
        page_numbers = [1, 2, 3, -1, total_pages]
    return BulkUserInvitationPagination(
        page=page,
        page_size=_PAGE_SIZE,
        total=total,
        total_pages=total_pages,
        page_numbers=page_numbers,
        has_previous=page > 1 and bool(total),
        has_next=page < total_pages,
        showing_label=f"Showing {min(_PAGE_SIZE, total - start)} of {total} rows" if total else "Showing 0 of 0",
    )


async def get_bulk_user_invitation_page(scope: AccessScope, *, page: int = 1) -> BulkUserInvitationPageRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    draft = await _draft(scope)
    rows = draft.validated_rows or []
    start = (page - 1) * _PAGE_SIZE
    page_slice = rows[start : start + _PAGE_SIZE]

    preview_rows = [
        BulkUserInvitationPreviewRow(
            row_id=str(r.get("row_id", "")),
            full_name=r.get("full_name", "—"),
            email=r.get("email", "—"),
            role_label=r.get("role_label", "—"),
            department_label=r.get("department_label", "—"),
            status_code=r.get("status_code", "muted"),
            status_label=r.get("status_label", "—"),
            status_tone=r.get("status_tone", "muted"),
        )
        for r in page_slice
    ]

    ready_count = sum(1 for r in rows if r.get("status_code") == "ready")
    attention_count = max(0, len(rows) - ready_count)
    preview_summary = (
        f"{len(rows)} rows · {ready_count} ready · {attention_count} need attention"
        if rows
        else None
    )
    meta = None
    if draft.file_name:
        meta = f"Uploaded · {draft.row_count} rows" + (
            f" · {draft.file_size_bytes // 1024} KB" if draft.file_size_bytes else ""
        )

    step_key = draft.step_key
    if not rows and step_key not in {"upload", "map_validate"}:
        step_key = "upload"

    return BulkUserInvitationPageRead(
        page_title="Bulk User Invitation",
        page_subtitle="Invite many staff or students at once from a spreadsheet",
        download_template_label="Download template",
        send_invitations_label="Send invitations",
        cancel_href="/college-admin/users/user-management-dashboard",
        cancel_label="Cancel",
        audit_footer_note="Changes are saved to the audit log with your name and time.",
        back_label="Back",
        fix_errors_label="Fix errors",
        send_ready_label=f"Send {ready_count} invitations",
        browse_files_label="Browse files",
        upload_drop_hint="Upload a CSV file matching the template",
        preview_section_title=f"Preview – {draft.file_name or 'spreadsheet'}",
        preview_summary_label=preview_summary,
        validation_summary_title="Validation summary",
        invitation_options_title="Invitation options",
        table_headers=["Name", "Email", "Role", "Department", "Check"],
        current_step_key=step_key,
        steps=_WIZARD_STEPS,
        file_name=draft.file_name,
        file_meta_label=meta,
        summary_stats=_summary_stats(rows),
        invitation_toggles=[
            BulkUserInvitationToggle(
                key="skip_rows_with_errors",
                label="Skip rows with errors",
                description="Invite only valid rows",
                default_on=draft.skip_rows_with_errors,
            ),
            BulkUserInvitationToggle(
                key="require_mfa_first_login",
                label="Require MFA on first login",
                description="Recommended for staff",
                default_on=draft.require_mfa_first_login,
            ),
        ],
        preview_rows=preview_rows,
        pagination=_paginate(rows, page),
        ready_to_send_count=ready_count,
        footer_disclaimer="Live validation against institution domain and HR records · All times IST",
        generated_at=utcnow(),
    )


async def upload_bulk_user_invitation(
    scope: AccessScope,
    payload: BulkUserInvitationUploadPayload,
) -> BulkUserInvitationPageRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    if not payload.file_name.lower().endswith(".csv"):
        raise AppError(
            code="VALIDATION_ERROR",
            message="Upload a CSV file (export spreadsheet as CSV if needed)",
            status_code=422,
        )
    rows = _parse_csv(payload.file_content)
    if not rows:
        raise AppError(code="VALIDATION_ERROR", message="No data rows found in file", status_code=422)

    validated = await _validate_rows(tenant_id, rows)
    draft = await _draft(scope)
    draft.file_name = payload.file_name
    draft.file_size_bytes = payload.file_size_bytes or len(payload.file_content.encode("utf-8"))
    draft.row_count = len(validated)
    draft.rows = rows
    draft.validated_rows = validated
    draft.step_key = "preview"
    draft.updated_at = utcnow()
    await draft.save()
    return await get_bulk_user_invitation_page(scope, page=1)


async def update_bulk_user_invitation_settings(
    scope: AccessScope,
    payload: BulkUserInvitationStepPayload,
) -> BulkUserInvitationPageRead:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    draft = await _draft(scope)
    if payload.skip_rows_with_errors is not None:
        draft.skip_rows_with_errors = payload.skip_rows_with_errors
    if payload.require_mfa_first_login is not None:
        draft.require_mfa_first_login = payload.require_mfa_first_login
    if payload.step_key:
        draft.step_key = payload.step_key
    draft.updated_at = utcnow()
    await draft.save()
    return await get_bulk_user_invitation_page(scope, page=1)


async def send_bulk_user_invitations(scope: AccessScope) -> BulkUserInvitationSendResponse:
    authorize(scope, Permission.INSTITUTION_USER_MANAGE)
    draft = await _draft(scope)
    rows = list(draft.validated_rows or [])
    if not rows:
        raise AppError(code="VALIDATION_ERROR", message="Upload a file before sending invitations", status_code=422)

    sent = 0
    skipped = 0
    for row in rows:
        if row.get("status_code") != "ready":
            if draft.skip_rows_with_errors:
                skipped += 1
                continue
            skipped += 1
            continue
        role_value = row.get("role")
        if not role_value:
            skipped += 1
            continue
        try:
            role = Role(role_value)
        except ValueError:
            skipped += 1
            continue
        try:
            await invite_institution_user(
                scope,
                InstitutionUserInvite(
                    email=row["email"],
                    full_name=row["full_name"],
                    role=role,
                    department_id=row.get("department_id"),
                ),
            )
            sent += 1
        except AppError as exc:
            if exc.code == "CONFLICT":
                skipped += 1
                continue
            raise

    draft.validated_rows = []
    draft.rows = []
    draft.file_name = None
    draft.row_count = 0
    draft.step_key = "upload"
    draft.updated_at = utcnow()
    await draft.save()

    return BulkUserInvitationSendResponse(
        status="ok",
        message=f"Sent {sent} invitation(s)",
        sent_count=sent,
        skipped_count=skipped,
        href="/college-admin/users/user-management-dashboard",
    )