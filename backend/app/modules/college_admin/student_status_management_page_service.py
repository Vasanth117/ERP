"""Student status management page (CA 06 — Status tab)."""

from __future__ import annotations

import math

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
    InstitutionFieldOption,
    PoliciesPagination,
    StudentStatusChangeSubmitPayload,
    StudentStatusManagementMixItem,
    StudentStatusManagementPageRead,
    StudentStatusManagementTableRow,
    StudentStatusPickerOption,
)
from app.modules.college_admin.student_admin_models import (
    StudentLifecycleStatus,
    StudentRecord,
    StudentStatusChangeApproval,
    StudentStatusChangeRequest,
    StudentStatusHistory,
)
from app.modules.college_admin.student_administration_dashboard_page_service import _fmt_time_label
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentProfile

_PAGE_SIZE = 10

_STATUS_OPTIONS = [
    InstitutionFieldOption(value="active", label="Active"),
    InstitutionFieldOption(value="on_hold", label="On hold"),
    InstitutionFieldOption(value="suspended", label="Suspended"),
    InstitutionFieldOption(value="alumni", label="Alumni"),
]

_BUCKET_LABELS = {opt.value: opt.label for opt in _STATUS_OPTIONS}

_MIX_TONES = {
    "active": "success",
    "on_hold": "warning",
    "suspended": "error",
    "alumni": "info",
}


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _status_bucket(record: StudentRecord, user: User | None) -> tuple[str, str]:
    if record.lifecycle_status == StudentLifecycleStatus.GRADUATED:
        return "alumni", _BUCKET_LABELS["alumni"]
    if record.lifecycle_status == StudentLifecycleStatus.ON_LEAVE:
        return "on_hold", _BUCKET_LABELS["on_hold"]
    if user is not None and not user.is_active:
        return "suspended", _BUCKET_LABELS["suspended"]
    if record.lifecycle_status in (
        StudentLifecycleStatus.WITHDRAWN,
        StudentLifecycleStatus.DISCONTINUED,
    ):
        return "suspended", _BUCKET_LABELS["suspended"]
    return "active", _BUCKET_LABELS["active"]


async def _apply_status_bucket(record: StudentRecord, user: User, bucket: str) -> None:
    if bucket == "active":
        record.lifecycle_status = StudentLifecycleStatus.ACTIVE
        record.enrollment_status = StudentEnrollmentStatus.ACTIVE
        user.is_active = True
    elif bucket == "on_hold":
        record.lifecycle_status = StudentLifecycleStatus.ON_LEAVE
        user.is_active = True
    elif bucket == "suspended":
        user.is_active = False
        if record.lifecycle_status == StudentLifecycleStatus.GRADUATED:
            record.lifecycle_status = StudentLifecycleStatus.ACTIVE
    elif bucket == "alumni":
        record.lifecycle_status = StudentLifecycleStatus.GRADUATED
        record.enrollment_status = StudentEnrollmentStatus.COMPLETED
        user.is_active = False
    else:
        raise AppError(code="VALIDATION", message="Unknown status", status_code=422)
    record.updated_at = utcnow()
    await record.save()
    user.updated_at = utcnow()
    await user.save()


async def get_student_status_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    selected_request_id: str | None = None,
) -> StudentStatusManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    records = await StudentRecord.find(Eq(StudentRecord.tenant_id, tenant_id)).to_list()
    user_ids = list({r.user_id for r in records})
    users = await User.find(In(User.id, user_ids)).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users if u.id is not None}

    profiles = await StudentProfile.find(Eq(StudentProfile.tenant_id, tenant_id)).to_list()
    profile_by_user = {p.user_id: p for p in profiles}

    mix_counts = {"active": 0, "on_hold": 0, "suspended": 0, "alumni": 0}
    picker_options: list[StudentStatusPickerOption] = []
    for record in records:
        user = user_by_id.get(record.user_id)
        bucket, label = _status_bucket(record, user)
        mix_counts[bucket] = mix_counts.get(bucket, 0) + 1
        if user and record.lifecycle_status in (
            StudentLifecycleStatus.ACTIVE,
            StudentLifecycleStatus.ADMITTED,
            StudentLifecycleStatus.ON_LEAVE,
        ):
            register = _register_number(record, profile_by_user.get(record.user_id))
            picker_options.append(
                StudentStatusPickerOption(
                    record_id=str(record.id),
                    label=f"{user.full_name} · {register}",
                )
            )

    picker_options.sort(key=lambda row: row.label.lower())
    picker_options = picker_options[:200]

    total_students = len(records) or 1
    mix_items = [
        StudentStatusManagementMixItem(
            status_key=key,
            status_label=_BUCKET_LABELS[key],
            count=mix_counts.get(key, 0),
            bar_percent=round((mix_counts.get(key, 0) / total_students) * 100, 1),
            tone=_MIX_TONES[key],
        )
        for key in ("active", "on_hold", "suspended", "alumni")
    ]

    requests = await StudentStatusChangeRequest.find(Eq(StudentStatusChangeRequest.tenant_id, tenant_id)).sort(
        "-created_at"
    ).to_list()
    total = len(requests)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_requests = requests[start : start + _PAGE_SIZE]

    table_rows: list[StudentStatusManagementTableRow] = []
    name_by_user = {uid: (user_by_id[uid].full_name if uid in user_by_id else "—") for uid in user_ids}
    register_by_record = {
        str(r.id): _register_number(r, profile_by_user.get(r.user_id)) for r in records if r.id
    }

    for req in page_requests:
        student_name = name_by_user.get(req.user_id, "—")
        register = register_by_record.get(str(req.student_record_id), "—")
        if req.approval_status == StudentStatusChangeApproval.PENDING:
            approval_label, approval_tone = "Pending", "warning"
        elif req.approval_status == StudentStatusChangeApproval.APPROVED:
            approval_label, approval_tone = "Approved", "success"
        else:
            approval_label, approval_tone = "Rejected", "error"
        table_rows.append(
            StudentStatusManagementTableRow(
                request_id=str(req.id),
                student_name=student_name,
                register_number=register,
                current_status_label=req.from_status_label,
                new_status_label=req.to_status_label,
                reason_label=req.reason,
                approval_status_label=approval_label,
                approval_status_tone=approval_tone,
            )
        )

    selected_record_id = ""
    selected_new_status = ""
    selected_reason = ""
    if selected_request_id:
        match = next((r for r in requests if str(r.id) == selected_request_id), None)
        if match:
            selected_record_id = str(match.student_record_id)
            selected_new_status = match.to_status_bucket
            selected_reason = match.reason
    elif page_requests:
        first = page_requests[0]
        selected_record_id = str(first.student_record_id)
        selected_new_status = first.to_status_bucket
        selected_reason = first.reason
        selected_request_id = str(first.id)

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return StudentStatusManagementPageRead(
        page_title="Student Status Management",
        page_subtitle="Active, on hold, suspended and alumni",
        change_status_label="Withdrawal / discontinue",
        change_status_href="/college-admin/students/student-withdrawal-discontinuation",
        status_changes_section_title="Status changes",
        table_headers=["Student", "Register no.", "Current", "New status", "Reason", "Approval"],
        status_change_rows=table_rows,
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
        status_mix_title="Status mix",
        status_mix_items=mix_items,
        update_status_section_title="Update status",
        student_field_label="Student",
        new_status_field_label="New status",
        reason_field_label="Reason",
        submit_status_label="Submit change",
        approve_status_label="Approve change",
        student_picker_options=picker_options,
        new_status_options=_STATUS_OPTIONS,
        selected_request_id=selected_request_id,
        form_record_id=selected_record_id,
        form_new_status=selected_new_status,
        form_reason=selected_reason,
        updated_at_label=_fmt_time_label(now),
        footer_disclaimer="Live institutional data · Student status and lifecycle records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def submit_student_status_change(
    scope: AccessScope,
    payload: StudentStatusChangeSubmitPayload,
) -> StudentStatusManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    record_id = to_object_id(payload.record_id, "record_id")
    record = await StudentRecord.get(record_id)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    user = await User.get(record.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="Student user not found", status_code=404)

    bucket, from_label = _status_bucket(record, user)
    to_bucket = payload.new_status_bucket.strip().lower()
    if to_bucket not in _BUCKET_LABELS:
        raise AppError(code="VALIDATION", message="Invalid status", status_code=422)
    if not (payload.reason or "").strip():
        raise AppError(code="VALIDATION", message="Reason is required", status_code=422)

    doc = StudentStatusChangeRequest(
        tenant_id=tenant_id,
        student_record_id=record.id,
        user_id=record.user_id,
        from_status_bucket=bucket,
        from_status_label=from_label,
        to_status_bucket=to_bucket,
        to_status_label=_BUCKET_LABELS[to_bucket],
        reason=payload.reason.strip(),
        approval_status=StudentStatusChangeApproval.PENDING,
        requested_by=scope.user_id,
    )
    await doc.insert()

    if payload.approve_immediately:
        await _approve_request(scope, doc)

    return await get_student_status_management_page(
        scope,
        page=payload.page,
        selected_request_id=str(doc.id),
    )


async def _approve_request(scope: AccessScope, doc: StudentStatusChangeRequest) -> None:
    tenant_id = doc.tenant_id
    if doc.approval_status != StudentStatusChangeApproval.PENDING:
        return
    record = await StudentRecord.get(doc.student_record_id)
    user = await User.get(doc.user_id) if record else None
    if record is None or user is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)

    previous_bucket, _ = _status_bucket(record, user)
    await _apply_status_bucket(record, user, doc.to_status_bucket)

    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, record.user_id),
    )
    if profile:
        profile.updated_at = utcnow()
        await profile.save()

    await StudentStatusHistory(
        tenant_id=tenant_id,
        student_record_id=record.id,
        user_id=record.user_id,
        from_status=previous_bucket,
        to_status=doc.to_status_bucket,
        reason=doc.reason,
        actor_id=scope.user_id,
    ).insert()

    doc.approval_status = StudentStatusChangeApproval.APPROVED
    doc.decided_by = scope.user_id
    doc.decided_at = utcnow()
    await doc.save()


async def approve_student_status_change(
    scope: AccessScope,
    *,
    request_id: str,
    page: int = 1,
) -> StudentStatusManagementPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await StudentStatusChangeRequest.get(to_object_id(request_id, "request_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Status change request not found", status_code=404)
    await _approve_request(scope, doc)
    return await get_student_status_management_page(scope, page=page, selected_request_id=request_id)