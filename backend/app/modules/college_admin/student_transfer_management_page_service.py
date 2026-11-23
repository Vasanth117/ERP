"""Student transfer management page (CA 06.10 — Transfers & promotions tab)."""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.academic_config_models import AcademicProgramme
from app.modules.college_admin.all_students_list_page_service import _fee_presentation, _register_number
from app.modules.college_admin.batch_section_allocation_page_service import _programme_table_label
from app.modules.college_admin.integrations.operational_reader import OperationalDataReader
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionFieldOption,
    PoliciesPagination,
    StudentTransferApprovalStep,
    StudentTransferCreatePageRead,
    StudentTransferManagementPageRead,
    StudentTransferManagementTableRow,
    StudentTransferRequestCreate,
    StudentTransferRequestCreateResult,
    StudentTransferReviewSavePayload,
)
from app.modules.college_admin.student_admin_models import (
    StudentLifecycleStatus,
    StudentRecord,
    StudentTransfer,
    TransferStatus,
)
from app.modules.college_admin.student_statistics_overview_service import _ENROLLED_LIFECYCLE
from app.modules.college_admin.student_administration_dashboard_page_service import _fmt_time_label
from app.modules.department_admin.models import (
    DepartmentRequestStatus,
    DepartmentSectionTransferRequest,
    SectionTransferApprovalRole,
    SectionTransferScenario,
)
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.students.models import StudentProfile

_reader = OperationalDataReader()
_PAGE_SIZE = 10

_ROLE_LABELS = {
    SectionTransferApprovalRole.SOURCE_DEPARTMENT_ADMIN: "Department Admin",
    SectionTransferApprovalRole.DESTINATION_DEPARTMENT_ADMIN: "Destination dept admin",
    SectionTransferApprovalRole.COLLEGE_ADMIN: "College Admin",
}

_TRANSFER_TYPE_OPTIONS = [
    InstitutionFieldOption(value="programme", label="Programme"),
    InstitutionFieldOption(value="section", label="Section"),
    InstitutionFieldOption(value="outgoing", label="Outgoing"),
]


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _request_number(created_at: datetime, doc_id) -> str:
    local = created_at
    stamp = f"{local.year % 100:02d}{local.month:02d}"
    suffix = str(doc_id)[-3:].upper().replace("-", "0")[:3]
    digits = "".join(ch for ch in suffix if ch.isdigit()) or "0"
    return f"TRF-{stamp}-{int(digits[:3] or 0):03d}"


def _status_presentation(status: DepartmentRequestStatus | TransferStatus, *, tc_issued: bool = False) -> tuple[str, str]:
    if tc_issued:
        return "TC issued", "info"
    if isinstance(status, TransferStatus):
        if status == TransferStatus.REQUESTED:
            return "Pending approval", "warning"
        if status == TransferStatus.APPROVED:
            return "Approved", "success"
        if status == TransferStatus.REJECTED:
            return "Rejected", "error"
        return "Approved", "success"
    if status == DepartmentRequestStatus.PENDING:
        return "Pending approval", "warning"
    if status == DepartmentRequestStatus.APPROVED:
        return "Approved", "success"
    if status == DepartmentRequestStatus.REJECTED:
        return "Rejected", "error"
    if status == DepartmentRequestStatus.COMPLETED:
        return "Approved", "success"
    return status.value.replace("_", " ").title(), "muted"


def _accounts_step(fee_raw: str) -> StudentTransferApprovalStep:
    if fee_raw == "Paid":
        return StudentTransferApprovalStep(key="accounts", label="Accounts clearance", status_label="Approved", tone="success")
    if fee_raw in ("Overdue", "Partial"):
        return StudentTransferApprovalStep(key="accounts", label="Accounts clearance", status_label="Pending", tone="warning")
    return StudentTransferApprovalStep(key="accounts", label="Accounts clearance", status_label="Not started", tone="muted")


def _approval_step_tone(status: DepartmentRequestStatus) -> tuple[str, str]:
    if status == DepartmentRequestStatus.APPROVED:
        return "Approved", "success"
    if status == DepartmentRequestStatus.PENDING:
        return "Pending", "warning"
    if status == DepartmentRequestStatus.REJECTED:
        return "Rejected", "error"
    return "Not started", "muted"


def _section_type_label(scenario: SectionTransferScenario) -> str:
    if scenario == SectionTransferScenario.CROSS_COLLEGE:
        return "Outgoing"
    if scenario == SectionTransferScenario.SAME_BATCH_SECTION:
        return "Section"
    return "Programme"


def _build_programme_short_label(code: str | None, prog_by_code: dict[str, AcademicProgramme]) -> str:
    if not code:
        return "—"
    prog = prog_by_code.get(code.upper())
    if prog:
        return _programme_table_label(prog)
    return code


async def _unified_rows(tenant_id, prog_by_code: dict[str, AcademicProgramme]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    section_docs = await DepartmentSectionTransferRequest.find(
        Eq(DepartmentSectionTransferRequest.tenant_id, tenant_id),
    ).sort("-created_at").to_list()

    user_ids: set = set()
    for doc in section_docs:
        user_ids.add(doc.student_user_id)

    student_transfers = await StudentTransfer.find(Eq(StudentTransfer.tenant_id, tenant_id)).sort("-created_at").to_list()
    for doc in student_transfers:
        user_ids.add(doc.user_id)

    users = await User.find(In(User.id, list(user_ids))).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users if u.id is not None}

    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    record_by_user = {r.user_id: r for r in records}

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}

    fee_demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    demands_by_user: dict = {}
    for demand in fee_demands:
        demands_by_user.setdefault(demand.student_user_id, []).append(demand)

    for doc in section_docs:
        user = user_by_id.get(doc.student_user_id)
        record = record_by_user.get(doc.student_user_id)
        profile = profile_by_user.get(doc.student_user_id)
        student_name = user.full_name if user else "—"
        register = _register_number(record, profile) if record else "—"
        from_prog = _build_programme_short_label(doc.programme_code, prog_by_code)
        to_prog = _build_programme_short_label(doc.to_programme_code or doc.programme_code, prog_by_code)
        from_label = f"{from_prog} - {doc.from_section_code}"
        if doc.transfer_scenario == SectionTransferScenario.CROSS_COLLEGE:
            to_label = "Other college"
        else:
            to_label = f"{to_prog} - {doc.to_section_code}"
        type_label = _section_type_label(doc.transfer_scenario)
        tc_issued = doc.status == DepartmentRequestStatus.COMPLETED and doc.transfer_scenario == SectionTransferScenario.CROSS_COLLEGE
        status_label, status_tone = _status_presentation(doc.status, tc_issued=tc_issued)
        key = f"section:{doc.id}"
        req_no = _request_number(doc.created_at, doc.id)
        rows.append(
            {
                "key": key,
                "sort_at": doc.created_at,
                "row": StudentTransferManagementTableRow(
                    request_key=key,
                    request_number=req_no,
                    student_name=student_name,
                    from_label=from_label,
                    to_label=to_label,
                    type_label=type_label,
                    status_label=status_label,
                    status_tone=status_tone,
                ),
                "student_line": f"{student_name} · {register}",
                "transfer_type": "outgoing" if type_label == "Outgoing" else ("section" if type_label == "Section" else "programme"),
                "effective_semester": doc.effective_date.isoformat() if doc.effective_date else "",
                "reason": doc.reason,
                "approval_steps": doc.approval_steps,
                "fee_user_id": doc.student_user_id,
                "kind": "section",
                "doc_id": str(doc.id),
            }
        )

    for doc in student_transfers:
        user = user_by_id.get(doc.user_id)
        record = record_by_user.get(doc.user_id)
        profile = profile_by_user.get(doc.user_id)
        student_name = user.full_name if user else "—"
        register = _register_number(record, profile) if record else "—"
        meta = doc.metadata or {}
        transfer_kind = str(meta.get("transfer_kind") or "programme")
        from_section = meta.get("from_section_code") or (record.section_code if record else "") or "—"
        to_section = meta.get("to_section_code") or "—"
        from_prog = _build_programme_short_label(doc.from_programme_code, prog_by_code)
        to_prog = _build_programme_short_label(doc.to_programme_code, prog_by_code)
        if transfer_kind == "outgoing" or (not doc.to_programme_code and not doc.to_department_id):
            transfer_kind = "outgoing"
            from_label = meta.get("from_label") or f"{from_prog} - {from_section}"
            to_label = meta.get("to_institution_label") or "Other college"
            type_label = "Outgoing"
        elif transfer_kind == "section":
            from_label = meta.get("from_label") or f"{from_prog} - {from_section}"
            to_label = meta.get("to_label") or f"{to_prog} - {to_section}"
            type_label = "Section"
        else:
            from_label = meta.get("from_label") or f"{from_prog} - {from_section}"
            to_label = meta.get("to_label") or f"{to_prog} - {to_section}"
            type_label = "Programme"
        tc_issued = bool(meta.get("tc_issued")) or (
            doc.status == TransferStatus.COMPLETED and transfer_kind == "outgoing"
        )
        status_label, status_tone = _status_presentation(doc.status, tc_issued=tc_issued)
        key = f"student:{doc.id}"
        req_no = str(meta.get("request_number") or _request_number(doc.created_at, doc.id))
        rows.append(
            {
                "key": key,
                "sort_at": doc.created_at,
                "row": StudentTransferManagementTableRow(
                    request_key=key,
                    request_number=req_no,
                    student_name=student_name,
                    from_label=from_label,
                    to_label=to_label,
                    type_label=type_label,
                    status_label=status_label,
                    status_tone=status_tone,
                ),
                "student_line": f"{student_name} · {register}",
                "transfer_type": transfer_kind,
                "effective_semester": str(meta.get("effective_semester_label") or ""),
                "reason": doc.reason,
                "approval_steps": meta.get("approval_steps"),
                "fee_user_id": doc.user_id,
                "kind": "student",
                "doc_id": str(doc.id),
            }
        )

    rows.sort(key=lambda item: item["sort_at"], reverse=True)
    return rows


def _serialize_approval_steps(
    raw_steps,
    *,
    fee_raw: str,
    include_accounts: bool,
) -> list[StudentTransferApprovalStep]:
    steps: list[StudentTransferApprovalStep] = []
    if raw_steps and isinstance(raw_steps, list):
        for item in raw_steps:
            if hasattr(item, "role"):
                label = _ROLE_LABELS.get(item.role, item.role.value.replace("_", " ").title())
                status_label, tone = _approval_step_tone(item.status)
                steps.append(
                    StudentTransferApprovalStep(
                        key=item.role.value,
                        label=label,
                        status_label=status_label,
                        tone=tone,
                    )
                )
            elif isinstance(item, dict):
                label = item.get("label") or item.get("key", "Step")
                status_label = item.get("status_label") or "Pending"
                tone = item.get("tone") or "warning"
                steps.append(
                    StudentTransferApprovalStep(
                        key=str(item.get("key") or label),
                        label=label,
                        status_label=status_label,
                        tone=tone,
                    )
                )
    if not steps:
        steps = [
            StudentTransferApprovalStep(key="department_admin", label="Department Admin", status_label="Approved", tone="success"),
            StudentTransferApprovalStep(key="college_admin", label="College Admin", status_label="Pending", tone="warning"),
        ]
    if include_accounts:
        steps.append(_accounts_step(fee_raw))
    return steps


async def get_student_transfer_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    selected_request_key: str | None = None,
) -> StudentTransferManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    _, semester_label = await _reader.current_academic_term(tenant_id)

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes}

    unified = await _unified_rows(tenant_id, prog_by_code)
    total = len(unified)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_items = unified[start : start + _PAGE_SIZE]

    selected = page_items[0] if page_items else None
    if selected_request_key:
        match = next((item for item in unified if item["key"] == selected_request_key), None)
        if match:
            selected = match

    fee_demands = await StudentFeeDemand.find(Eq(StudentFeeDemand.tenant_id, tenant_id)).to_list()
    demands_by_user: dict = {}
    for demand in fee_demands:
        demands_by_user.setdefault(demand.student_user_id, []).append(demand)

    review_student_line = ""
    review_transfer_type = ""
    review_effective_semester = ""
    review_reason = ""
    approval_steps: list[StudentTransferApprovalStep] = []
    if selected:
        fee_raw, _ = _fee_presentation(demands_by_user.get(selected["fee_user_id"], []))
        include_accounts = selected["transfer_type"] in ("programme", "outgoing")
        approval_steps = _serialize_approval_steps(
            selected["approval_steps"],
            fee_raw=fee_raw,
            include_accounts=include_accounts,
        )
        review_student_line = selected["student_line"]
        review_transfer_type = selected["transfer_type"]
        review_effective_semester = selected["effective_semester"] or (f"Semester {semester_label}" if semester_label else "")
        review_reason = selected["reason"]

    semester_options = [InstitutionFieldOption(value="", label="Effective from")]
    if semester_label:
        semester_options.append(InstitutionFieldOption(value=f"Semester {semester_label}", label=f"Semester {semester_label}"))
    for n in range(1, 9):
        label = f"Semester {n}"
        semester_options.append(InstitutionFieldOption(value=label, label=label))

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return StudentTransferManagementPageRead(
        page_title="Student Transfer Management",
        page_subtitle="Programme, section and college transfers",
        new_transfer_label="New transfer",
        new_transfer_href="/college-admin/students/student-transfer-create",
        requests_section_title="Transfer requests",
        table_headers=["Request", "Student", "From", "To", "Type", "Status"],
        transfer_rows=[item["row"] for item in page_items],
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
        selected_request_key=selected["key"] if selected else None,
        review_section_title="Review request",
        review_student_field_label="Student",
        review_student_line=review_student_line,
        review_transfer_type_field_label="Transfer type",
        review_transfer_type_options=_TRANSFER_TYPE_OPTIONS,
        review_transfer_type=review_transfer_type,
        review_effective_field_label="Effective from",
        review_effective_options=semester_options,
        review_effective_semester=review_effective_semester,
        review_reason_field_label="Reason",
        review_reason=review_reason,
        save_review_label="Save review",
        approve_college_label="Approve (college)",
        approval_route_title="Approval route",
        approval_steps=approval_steps,
        updated_at_label=_fmt_time_label(now),
        footer_disclaimer="Live institutional data · Student transfer workflow · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def save_student_transfer_review(
    scope: AccessScope,
    payload: StudentTransferReviewSavePayload,
) -> StudentTransferManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)

    if ":" not in payload.request_key:
        raise AppError(code="VALIDATION", message="Invalid request key", status_code=422)
    kind, raw_id = payload.request_key.split(":", 1)

    if kind == "section":
        doc = await DepartmentSectionTransferRequest.get(to_object_id(raw_id, "request_id"))
        if doc is None or doc.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Transfer request not found", status_code=404)
        if payload.reason is not None:
            doc.reason = payload.reason[:1000]
        if payload.effective_semester:
            doc.updated_at = utcnow()
        await doc.save()
        if payload.approve_college:
            from app.modules.department_admin.section_transfer_service import review_section_transfer

            admin = await User.get(scope.user_id) if scope.user_id else None
            if admin is None:
                raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
            from app.modules.department_admin.phase3_schemas import SectionTransferReview

            await review_section_transfer(
                scope,
                admin,
                raw_id,
                SectionTransferReview(decision="approve"),
            )
    elif kind == "student":
        doc = await StudentTransfer.get(to_object_id(raw_id, "transfer_id"))
        if doc is None or doc.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Transfer request not found", status_code=404)
        meta = dict(doc.metadata or {})
        if payload.reason is not None:
            doc.reason = payload.reason[:1000]
        if payload.transfer_type:
            meta["transfer_kind"] = payload.transfer_type
        if payload.effective_semester:
            meta["effective_semester_label"] = payload.effective_semester
        if payload.approve_college:
            steps = meta.get("approval_steps") or [
                {"key": "department_admin", "label": "Department Admin", "status_label": "Approved", "tone": "success"},
                {"key": "college_admin", "label": "College Admin", "status_label": "Pending", "tone": "warning"},
            ]
            for step in steps:
                if step.get("key") == "college_admin":
                    step["status_label"] = "Approved"
                    step["tone"] = "success"
            meta["approval_steps"] = steps
            doc.status = TransferStatus.APPROVED
            if meta.get("transfer_kind") == "outgoing":
                meta["tc_issued"] = True
                doc.status = TransferStatus.COMPLETED
                doc.completed_at = utcnow()
        doc.metadata = meta
        await doc.save()
    else:
        raise AppError(code="VALIDATION", message="Unknown transfer kind", status_code=422)

    return await get_student_transfer_management_page(
        scope,
        page=payload.page,
        selected_request_key=payload.request_key,
    )


async def get_student_transfer_create_page(scope: AccessScope) -> StudentTransferCreatePageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    _, semester_label = await _reader.current_academic_term(tenant_id)

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).sort("-updated_at").to_list()
    enrolled = [r for r in records if r.lifecycle_status.value in _ENROLLED_LIFECYCLE]

    users = await User.find(In(User.id, [r.user_id for r in enrolled])).to_list() if enrolled else []
    user_by_id = {u.id: u for u in users if u.id is not None}
    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}

    student_options = [InstitutionFieldOption(value="", label="Select student")]
    for record in enrolled[:200]:
        user = user_by_id.get(record.user_id)
        profile = profile_by_user.get(record.user_id)
        name = (user.full_name if user else None) or "Student"
        register = _register_number(record, profile)
        student_options.append(
            InstitutionFieldOption(
                value=str(record.id),
                label=f"{name} · {register}",
            )
        )

    semester_options = [InstitutionFieldOption(value="", label="Select semester")]
    if semester_label:
        semester_options.append(
            InstitutionFieldOption(value=f"Semester {semester_label}", label=f"Semester {semester_label}")
        )
    for n in range(1, 9):
        label = f"Semester {n}"
        semester_options.append(InstitutionFieldOption(value=label, label=label))

    return StudentTransferCreatePageRead(
        page_title="New transfer request",
        page_subtitle="Create a programme, section, or outgoing transfer for review",
        back_href="/college-admin/students/student-transfer-management",
        back_label="Back to transfers",
        submit_label="Submit request",
        student_field_label="Student",
        transfer_type_field_label="Transfer type",
        programme_field_label="Destination programme",
        section_field_label="Destination section",
        institution_field_label="Destination institution",
        effective_field_label="Effective from",
        reason_field_label="Reason",
        student_options=student_options,
        transfer_type_options=_TRANSFER_TYPE_OPTIONS,
        programme_options=[
            InstitutionFieldOption(value="", label="Select programme"),
            *[
                InstitutionFieldOption(value=p.programme_code, label=p.name or p.programme_code)
                for p in sorted(programmes, key=lambda row: (row.name or row.programme_code).lower())
            ],
        ],
        effective_options=semester_options,
        generated_at=now,
    )


async def create_student_transfer_request(
    scope: AccessScope,
    payload: StudentTransferRequestCreate,
) -> StudentTransferRequestCreateResult:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    record_id = to_object_id(payload.student_record_id, "student_record_id")
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    if record.lifecycle_status.value not in _ENROLLED_LIFECYCLE:
        raise AppError(code="VALIDATION", message="Student must be enrolled to request a transfer", status_code=422)

    programmes = await AcademicProgramme.find(Eq(AcademicProgramme.tenant_id, tenant_id)).to_list()
    prog_by_code = {p.programme_code.upper(): p for p in programmes}

    transfer_kind = payload.transfer_type.strip().lower()
    to_prog_code = payload.to_programme_code.strip().upper() if payload.to_programme_code else None
    if transfer_kind in ("programme", "section") and not to_prog_code:
        raise AppError(code="VALIDATION", message="Destination programme is required", status_code=422)
    if transfer_kind == "section" and not (payload.to_section_code or "").strip():
        raise AppError(code="VALIDATION", message="Destination section is required for section transfers", status_code=422)
    if transfer_kind == "outgoing" and not (payload.to_institution_label or "").strip():
        raise AppError(code="VALIDATION", message="Destination institution is required for outgoing transfers", status_code=422)

    from_prog = _build_programme_short_label(record.programme_code, prog_by_code)
    from_section = (record.section_code or "").strip() or "—"
    from_label = f"{from_prog} - {from_section}"

    if transfer_kind == "outgoing":
        to_label = (payload.to_institution_label or "").strip()
        to_prog_code = None
    elif transfer_kind == "section":
        to_section = (payload.to_section_code or "").strip().upper()
        to_prog_label = _build_programme_short_label(to_prog_code, prog_by_code)
        to_label = f"{to_prog_label} - {to_section}"
    else:
        to_prog_label = _build_programme_short_label(to_prog_code, prog_by_code)
        to_section = (payload.to_section_code or record.section_code or "—").strip()
        to_label = f"{to_prog_label} - {to_section}"

    meta = {
        "transfer_kind": transfer_kind,
        "from_label": from_label,
        "to_label": to_label,
        "from_section_code": from_section if from_section != "—" else "",
        "to_section_code": (payload.to_section_code or "").strip().upper(),
        "to_institution_label": (payload.to_institution_label or "").strip(),
        "effective_semester_label": (payload.effective_semester or "").strip(),
        "approval_steps": [
            {
                "key": "department_admin",
                "label": "Department Admin",
                "status_label": "Pending",
                "tone": "warning",
            },
            {
                "key": "college_admin",
                "label": "College Admin",
                "status_label": "Pending",
                "tone": "warning",
            },
        ],
    }

    transfer = StudentTransfer(
        tenant_id=tenant_id,
        user_id=record.user_id,
        from_department_id=record.department_id,
        to_department_id=None,
        from_programme_code=record.programme_code,
        to_programme_code=to_prog_code,
        reason=payload.reason.strip(),
        status=TransferStatus.REQUESTED,
        actor_id=scope.user_id,
        metadata=meta,
    )
    await transfer.insert()
    meta["request_number"] = _request_number(now, transfer.id)
    transfer.metadata = meta
    await transfer.save()

    request_key = f"student:{transfer.id}"
    return StudentTransferRequestCreateResult(
        request_key=request_key,
        transfer_href=f"/college-admin/students/student-transfer-management?selected_request_key={request_key}",
    )