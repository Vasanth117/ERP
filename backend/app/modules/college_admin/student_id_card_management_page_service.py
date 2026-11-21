"""Student ID card management page (CA 06.13 — Status / ID cards tab)."""

from __future__ import annotations

import math
import uuid
from datetime import date, timedelta

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.all_students_list_page_service import _register_number
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    PoliciesPagination,
    StudentIdCardBulkPrintPayload,
    StudentIdCardIssuePayload,
    StudentIdCardManagementPageRead,
    StudentIdCardManagementTableRow,
    UserDashboardKpi,
)
from app.modules.college_admin.student_admin_models import (
    StudentIdCard,
    StudentIdCardStatus,
    StudentLifecycleStatus,
    StudentRecord,
)
from app.modules.students.models import StudentProfile
from app.modules.tenants.models import Tenant

_PAGE_SIZE = 10
_RENEWAL_WINDOW_DAYS = 60
_ELIGIBLE_LIFECYCLE = frozenset(
    {
        StudentLifecycleStatus.ACTIVE,
        StudentLifecycleStatus.ADMITTED,
        StudentLifecycleStatus.ON_LEAVE,
        StudentLifecycleStatus.GRADUATED,
    }
)
_BLOCKED_LIFECYCLE = frozenset(
    {
        StudentLifecycleStatus.WITHDRAWN,
        StudentLifecycleStatus.DISCONTINUED,
        StudentLifecycleStatus.TRANSFERRED,
    }
)

_STATUS_LABELS = {
    StudentIdCardStatus.ACTIVE: ("Active", "success"),
    StudentIdCardStatus.PENDING_PRINT: ("Pending print", "warning"),
    StudentIdCardStatus.RENEWAL_DUE: ("Renewal due", "warning"),
    StudentIdCardStatus.REPRINT_REQUESTED: ("Pending print", "warning"),
    StudentIdCardStatus.BLOCKED: ("Blocked", "error"),
}

_NOT_ISSUED = "Not issued"
_EMPTY_DATE = "—"


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _fmt_date(value: date | None) -> str:
    if value is None:
        return _EMPTY_DATE
    return value.strftime("%d %b %Y")


def _card_number_prefix(tenant: Tenant, record: StudentRecord, profile: StudentProfile | None) -> str:
    code = (tenant.code or "ID").strip().upper()
    prefix = "".join(ch for ch in code if ch.isalnum())[:3] or "ID"
    batch = (record.batch_label or "").strip()
    batch_suffix = batch[-2:] if len(batch) >= 2 else (batch or "00")
    register = _register_number(record, profile)
    digits = "".join(ch for ch in register if ch.isdigit())
    tail = (digits[-4:] if len(digits) >= 4 else digits or register[-4:]).zfill(4)
    return f"{prefix}-{batch_suffix}-{tail}"


def _default_valid_until(record: StudentRecord) -> date:
    batch = (record.batch_label or "").strip()
    try:
        start_year = int(batch[:4]) if len(batch) >= 4 else int(batch)
    except ValueError:
        start_year = utcnow().year
    return date(start_year + 4, 6, 30)


def _resolve_status(
    *,
    record: StudentRecord,
    user: User,
    card: StudentIdCard | None,
    today: date,
) -> tuple[StudentIdCardStatus, str, str]:
    if record.lifecycle_status in _BLOCKED_LIFECYCLE or not user.is_active:
        return StudentIdCardStatus.BLOCKED, *_STATUS_LABELS[StudentIdCardStatus.BLOCKED]
    if card is None:
        return StudentIdCardStatus.PENDING_PRINT, *_STATUS_LABELS[StudentIdCardStatus.PENDING_PRINT]
    if card.status == StudentIdCardStatus.BLOCKED:
        return StudentIdCardStatus.BLOCKED, *_STATUS_LABELS[StudentIdCardStatus.BLOCKED]
    if card.status == StudentIdCardStatus.REPRINT_REQUESTED:
        return StudentIdCardStatus.REPRINT_REQUESTED, *_STATUS_LABELS[StudentIdCardStatus.REPRINT_REQUESTED]
    if card.status == StudentIdCardStatus.PENDING_PRINT or not card.card_number:
        return StudentIdCardStatus.PENDING_PRINT, *_STATUS_LABELS[StudentIdCardStatus.PENDING_PRINT]
    if card.valid_until and card.valid_until <= today + timedelta(days=_RENEWAL_WINDOW_DAYS):
        return StudentIdCardStatus.RENEWAL_DUE, *_STATUS_LABELS[StudentIdCardStatus.RENEWAL_DUE]
    if card.status in (StudentIdCardStatus.ACTIVE, StudentIdCardStatus.RENEWAL_DUE):
        label, tone = _STATUS_LABELS.get(card.status, _STATUS_LABELS[StudentIdCardStatus.ACTIVE])
        if card.valid_until and card.valid_until <= today + timedelta(days=_RENEWAL_WINDOW_DAYS):
            return StudentIdCardStatus.RENEWAL_DUE, *_STATUS_LABELS[StudentIdCardStatus.RENEWAL_DUE]
        return StudentIdCardStatus.ACTIVE, label, tone
    return card.status, *_STATUS_LABELS.get(card.status, ("—", "muted"))


async def _build_rows(
    tenant: Tenant,
    records: list[StudentRecord],
    users: dict,
    profiles: dict,
    cards_by_record: dict,
) -> list[tuple[StudentRecord, StudentIdCardManagementTableRow, StudentIdCardStatus]]:
    today = utcnow().date()
    built: list[tuple[StudentRecord, StudentIdCardManagementTableRow, StudentIdCardStatus]] = []
    for record in records:
        user = users.get(record.user_id)
        if user is None:
            continue
        card = cards_by_record.get(record.id)
        status, status_label, status_tone = _resolve_status(record=record, user=user, card=card, today=today)
        profile = profiles.get(record.user_id)
        card_number = card.card_number if card and card.card_number else _NOT_ISSUED
        issued_label = _fmt_date(card.issued_at.date()) if card and card.issued_at else _EMPTY_DATE
        valid_label = _fmt_date(card.valid_until if card else None)
        row = StudentIdCardManagementTableRow(
            record_id=str(record.id),
            card_id=str(card.id) if card else "",
            student_name=user.full_name,
            card_number_label=card_number,
            issued_label=issued_label,
            valid_until_label=valid_label,
            status_label=status_label,
            status_tone=status_tone,
        )
        built.append((record, row, status))
    built.sort(key=lambda item: item[1].student_name.lower())
    return built


async def get_student_id_card_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
) -> StudentIdCardManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="Tenant not found", status_code=404)

    records = await StudentRecord.find(
        Eq(StudentRecord.tenant_id, tenant_id),
        In(StudentRecord.lifecycle_status, list(_ELIGIBLE_LIFECYCLE | _BLOCKED_LIFECYCLE)),
    ).to_list()
    user_ids = list({r.user_id for r in records})
    users_list = await User.find(In(User.id, user_ids)).to_list() if user_ids else []
    users = {u.id: u for u in users_list if u.id is not None}
    profiles_list = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profiles = {p.user_id: p for p in profiles_list}
    cards = await StudentIdCard.find(Eq(StudentIdCard.tenant_id, tenant_id)).to_list()
    cards_by_record = {c.student_record_id: c for c in cards}

    all_rows = await _build_rows(tenant, records, users, profiles, cards_by_record)

    kpi_issued = sum(1 for _, _, st in all_rows if st in (StudentIdCardStatus.ACTIVE, StudentIdCardStatus.RENEWAL_DUE))
    kpi_pending = sum(1 for _, _, st in all_rows if st == StudentIdCardStatus.PENDING_PRINT)
    kpi_reprint = sum(
        1
        for c in cards
        if c.status == StudentIdCardStatus.REPRINT_REQUESTED
    )
    kpi_blocked = sum(1 for _, _, st in all_rows if st == StudentIdCardStatus.BLOCKED)

    total = len(all_rows)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_rows = [row for _, row, _ in all_rows[start : start + _PAGE_SIZE]]

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return StudentIdCardManagementPageRead(
        page_title="Student ID Card Management",
        page_subtitle="Issue, reprint and block ID cards",
        bulk_print_label="Bulk print",
        issue_card_label="Issue card",
        issue_card_href="/college-admin/students/all-students-list",
        kpis=[
            UserDashboardKpi(
                key="issued",
                label="Issued",
                value=f"{kpi_issued:,}",
                hint_line="Active cards",
                hint_tone="success",
            ),
            UserDashboardKpi(
                key="pending_print",
                label="Pending print",
                value=f"{kpi_pending:,}",
                hint_line="New admissions",
                hint_tone="warning",
            ),
            UserDashboardKpi(
                key="reprint",
                label="Reprint requests",
                value=f"{kpi_reprint:,}",
                hint_line="Lost or damaged",
                hint_tone="info",
            ),
            UserDashboardKpi(
                key="blocked",
                label="Blocked",
                value=f"{kpi_blocked:,}",
                hint_line="Status changed",
                hint_tone="error",
            ),
        ],
        id_cards_section_title="ID cards",
        table_headers=["Student", "Card no.", "Issued", "Valid till", "Status"],
        card_rows=page_rows,
        showing_label=f"Showing {showing_from}–{showing_to} of {total:,}" if total else "Showing 0 of 0",
        pagination=PoliciesPagination(
            page=page,
            page_size=_PAGE_SIZE,
            total=total,
            total_pages=total_pages,
            page_numbers=_page_numbers(total_pages),
            has_previous=page > 1 and bool(total),
            has_next=page < total_pages,
        ),
        footer_disclaimer="Live institutional data · Student ID card records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def issue_student_id_card(
    scope: AccessScope,
    payload: StudentIdCardIssuePayload,
) -> StudentIdCardManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    tenant = await Tenant.get(tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="Tenant not found", status_code=404)

    record: StudentRecord | None = None
    if payload.record_id:
        record = await StudentRecord.get(to_object_id(payload.record_id, "record_id"))
    else:
        records = await StudentRecord.find(
            Eq(StudentRecord.tenant_id, tenant_id),
            In(StudentRecord.lifecycle_status, list(_ELIGIBLE_LIFECYCLE)),
        ).to_list()
        cards = await StudentIdCard.find(Eq(StudentIdCard.tenant_id, tenant_id)).to_list()
        issued_ids = {c.student_record_id for c in cards if c.card_number}
        record = next((r for r in records if r.id not in issued_ids), None)

    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="No eligible student for card issue", status_code=404)

    user = await User.get(record.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="Student user not found", status_code=404)

    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, record.user_id),
    )
    card = await StudentIdCard.find_one(
        Eq(StudentIdCard.tenant_id, tenant_id),
        Eq(StudentIdCard.student_record_id, record.id),
    )
    number = _card_number_prefix(tenant, record, profile)
    now = utcnow()
    valid_until = _default_valid_until(record)

    if card is None:
        card = StudentIdCard(
            tenant_id=tenant_id,
            student_record_id=record.id,
            user_id=record.user_id,
            card_number=number,
            issued_at=now,
            valid_until=valid_until,
            status=StudentIdCardStatus.ACTIVE,
            issued_by=scope.user_id,
        )
        await card.insert()
    else:
        card.card_number = number
        card.issued_at = now
        card.valid_until = valid_until
        card.status = StudentIdCardStatus.ACTIVE
        card.reprint_reason = None
        card.issued_by = scope.user_id
        card.updated_at = now
        await card.save()

    return await get_student_id_card_management_page(scope, page=payload.page)


async def bulk_print_student_id_cards(
    scope: AccessScope,
    payload: StudentIdCardBulkPrintPayload,
) -> StudentIdCardManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    batch_id = f"PRINT-{uuid.uuid4().hex[:8].upper()}"
    now = utcnow()

    if payload.record_ids:
        record_ids = [to_object_id(rid, "record_id") for rid in payload.record_ids]
        records = await StudentRecord.find(
            Eq(StudentRecord.tenant_id, tenant_id),
            In(StudentRecord.id, record_ids),
        ).to_list()
    else:
        records = await StudentRecord.find(
            Eq(StudentRecord.tenant_id, tenant_id),
            In(StudentRecord.lifecycle_status, list(_ELIGIBLE_LIFECYCLE)),
        ).to_list()

    cards = await StudentIdCard.find(Eq(StudentIdCard.tenant_id, tenant_id)).to_list()
    cards_by_record = {c.student_record_id: c for c in cards}

    for record in records:
        card = cards_by_record.get(record.id)
        pending = card is None or card.status in (
            StudentIdCardStatus.PENDING_PRINT,
            StudentIdCardStatus.REPRINT_REQUESTED,
        )
        if not pending:
            continue
        if card is None:
            card = StudentIdCard(
                tenant_id=tenant_id,
                student_record_id=record.id,
                user_id=record.user_id,
                status=StudentIdCardStatus.PENDING_PRINT,
                print_batch_id=batch_id,
            )
            await card.insert()
        else:
            card.print_batch_id = batch_id
            card.status = StudentIdCardStatus.PENDING_PRINT
            card.updated_at = now
            await card.save()

    return await get_student_id_card_management_page(scope, page=payload.page)