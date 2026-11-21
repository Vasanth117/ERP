"""Employee status management page (CA 07.12)."""

from __future__ import annotations

import math
from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import (
    EmployeeRecord,
    EmployeeStatusChangeApproval,
    EmployeeStatusChangeRequest,
    FacultyEmploymentHistory,
    FacultyEmploymentStatus,
    FacultyRecord,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    EmployeeStatusChangeSubmitPayload,
    EmployeeStatusManagementMixItem,
    EmployeeStatusManagementPageRead,
    EmployeeStatusManagementTableRow,
    EmployeeStatusPickerOption,
    InstitutionFieldOption,
    PoliciesPagination,
)

_PAGE_SIZE = 10

_STATUS_LABELS: dict[str, str] = {
    FacultyEmploymentStatus.ACTIVE.value: "Active",
    FacultyEmploymentStatus.INACTIVE.value: "Inactive",
    FacultyEmploymentStatus.PROBATION.value: "Probation",
    FacultyEmploymentStatus.AWAITING_CONFIRMATION.value: "Contract",
    FacultyEmploymentStatus.CONFIRMED.value: "Confirmed",
    FacultyEmploymentStatus.ON_LEAVE.value: "On leave",
    FacultyEmploymentStatus.NOTICE_PERIOD.value: "Notice period",
    FacultyEmploymentStatus.TRANSFERRED.value: "Transferred",
    FacultyEmploymentStatus.RESIGNED.value: "Resigned",
    FacultyEmploymentStatus.TERMINATED.value: "Terminated",
    FacultyEmploymentStatus.RETIRED.value: "Retired",
}

_NEW_STATUS_OPTIONS = [
    InstitutionFieldOption(value="", label="Select status"),
    InstitutionFieldOption(value=FacultyEmploymentStatus.CONFIRMED.value, label="Confirmed"),
    InstitutionFieldOption(value=FacultyEmploymentStatus.ACTIVE.value, label="Active"),
    InstitutionFieldOption(value=FacultyEmploymentStatus.PROBATION.value, label="Probation"),
    InstitutionFieldOption(value=FacultyEmploymentStatus.NOTICE_PERIOD.value, label="Notice period"),
    InstitutionFieldOption(value=FacultyEmploymentStatus.ON_LEAVE.value, label="On leave"),
    InstitutionFieldOption(value=FacultyEmploymentStatus.RESIGNED.value, label="Resigned"),
    InstitutionFieldOption(value=FacultyEmploymentStatus.RETIRED.value, label="Retired"),
    InstitutionFieldOption(value=FacultyEmploymentStatus.TERMINATED.value, label="Terminated"),
]

_MIX_KEYS: tuple[tuple[str, str, str], ...] = (
    ("active", "Active", "success"),
    ("probation", "Probation", "info"),
    ("notice_period", "Notice period", "warning"),
    ("contract", "Contract", "muted"),
)


def _page_numbers(total_pages: int) -> list[int]:
    if total_pages <= 0:
        return []
    if total_pages <= 12:
        return list(range(1, total_pages + 1))
    return [1, 2, 3, -1, total_pages]


def _status_label(raw: str | FacultyEmploymentStatus) -> str:
    key = raw.value if isinstance(raw, FacultyEmploymentStatus) else str(raw)
    return _STATUS_LABELS.get(key, key.replace("_", " ").title())


def _mix_bucket(status: FacultyEmploymentStatus, employment_type: str | None) -> str:
    if status == FacultyEmploymentStatus.PROBATION:
        return "probation"
    if status == FacultyEmploymentStatus.NOTICE_PERIOD:
        return "notice_period"
    if status == FacultyEmploymentStatus.AWAITING_CONFIRMATION or (employment_type or "").lower() == "contract":
        return "contract"
    return "active"


def _fmt_effective(when: date | None) -> str:
    if when is None:
        return "—"
    return when.strftime("%d %b %Y")


async def _apply_employment_status(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
    new_status: FacultyEmploymentStatus,
    *,
    actor_id: PydanticObjectId,
    effective: date,
    note: str,
) -> None:
    employee = await EmployeeRecord.find_one(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.user_id, user_id),
    )
    faculty = await FacultyRecord.find_one(
        Eq(FacultyRecord.tenant_id, tenant_id),
        Eq(FacultyRecord.user_id, user_id),
    )
    previous = None
    if employee:
        previous = employee.employment_status
        employee.employment_status = new_status
        employee.updated_at = utcnow()
        employee.updated_by = actor_id
        await employee.save()
    if faculty:
        faculty.employment_status = new_status
        faculty.updated_at = utcnow()
        faculty.updated_by = actor_id
        await faculty.save()
    await FacultyEmploymentHistory(
        tenant_id=tenant_id,
        user_id=user_id,
        event_type="employment_status_change",
        from_status=previous.value if previous else None,
        to_status=new_status.value,
        effective_date=effective,
        note=note,
        actor_id=actor_id,
    ).insert()


async def get_employee_status_management_page(
    scope: AccessScope,
    *,
    page: int = 1,
    selected_request_id: str | None = None,
) -> EmployeeStatusManagementPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    user_ids = list({e.user_id for e in employees})
    users = await User.find(In(User.id, user_ids)).to_list() if user_ids else []
    user_by_id = {u.id: u for u in users if u.id}

    mix_counts = {key: 0 for key, _, _ in _MIX_KEYS}
    picker: list[EmployeeStatusPickerOption] = []
    for emp in employees:
        bucket = _mix_bucket(emp.employment_status, emp.employment_type)
        mix_counts[bucket] = mix_counts.get(bucket, 0) + 1
        user = user_by_id.get(emp.user_id)
        if user and emp.employment_status not in (
            FacultyEmploymentStatus.RESIGNED,
            FacultyEmploymentStatus.TERMINATED,
            FacultyEmploymentStatus.RETIRED,
        ):
            code = emp.employee_id or "—"
            picker.append(
                EmployeeStatusPickerOption(
                    record_id=str(emp.id),
                    label=f"{user.full_name} · {code}",
                )
            )
    picker.sort(key=lambda row: row.label.lower())

    total_staff = len(employees) or 1
    mix_items = [
        EmployeeStatusManagementMixItem(
            status_key=key,
            status_label=label,
            count=mix_counts.get(key, 0),
            bar_percent=round((mix_counts.get(key, 0) / total_staff) * 100, 1),
            tone=tone,
        )
        for key, label, tone in _MIX_KEYS
    ]

    requests = await EmployeeStatusChangeRequest.find(
        Eq(EmployeeStatusChangeRequest.tenant_id, tenant_id)
    ).sort("-created_at").to_list()
    total = len(requests)
    total_pages = math.ceil(total / _PAGE_SIZE) if total else 0
    page = min(max(1, page), total_pages or 1)
    start = (page - 1) * _PAGE_SIZE
    page_requests = requests[start : start + _PAGE_SIZE]

    name_by_user = {
        uid: (user_by_id[uid].full_name if uid in user_by_id else "—") for uid in user_ids
    }
    table_rows: list[EmployeeStatusManagementTableRow] = []
    for req in page_requests:
        if req.approval_status == EmployeeStatusChangeApproval.PENDING:
            approval_label, approval_tone = "Pending", "warning"
        elif req.approval_status == EmployeeStatusChangeApproval.APPROVED:
            approval_label, approval_tone = "Approved", "success"
        else:
            approval_label, approval_tone = "Rejected", "error"
        table_rows.append(
            EmployeeStatusManagementTableRow(
                request_id=str(req.id),
                employee_name=name_by_user.get(req.user_id, "—"),
                current_status_label=req.from_status_label,
                new_status_label=req.to_status_label,
                effective_label=_fmt_effective(req.effective_date),
                reason_label=req.reason,
                approval_status_label=approval_label,
                approval_status_tone=approval_tone,
            )
        )

    form_record_id = ""
    form_new_status = ""
    form_reason = ""
    form_effective = now.date().isoformat()
    if selected_request_id:
        match = next((r for r in requests if str(r.id) == selected_request_id), None)
        if match:
            form_record_id = str(match.employee_record_id)
            form_new_status = match.to_status
            form_reason = match.reason
            form_effective = match.effective_date.isoformat()
    elif page_requests:
        first = page_requests[0]
        form_record_id = str(first.employee_record_id)
        form_new_status = first.to_status
        form_reason = first.reason
        form_effective = first.effective_date.isoformat()
        selected_request_id = str(first.id)

    showing_from = start + 1 if total else 0
    showing_to = min(start + _PAGE_SIZE, total)

    return EmployeeStatusManagementPageRead(
        page_title="Employee Status Management",
        page_subtitle="Active, probation, notice, resigned, retired",
        change_status_label="Change status",
        change_status_href="/college-admin/faculty/employee-status-management#update-status",
        status_changes_section_title="Status changes",
        table_headers=["Employee", "Current", "New status", "Effective", "Reason", "Approval"],
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
        employee_field_label="Employee",
        new_status_field_label="New status",
        reason_field_label="Reason",
        effective_date_field_label="Effective date",
        submit_status_label="Submit change",
        approve_status_label="Approve change",
        employee_picker_options=picker[:200],
        new_status_options=_NEW_STATUS_OPTIONS,
        selected_request_id=selected_request_id,
        form_record_id=form_record_id,
        form_new_status=form_new_status,
        form_reason=form_reason,
        form_effective_date=form_effective,
        updated_at_label=now.astimezone(__import__("zoneinfo").ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %H:%M IST"),
        footer_disclaimer="Live institutional data · Faculty and employee records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def submit_employee_status_change(
    scope: AccessScope,
    payload: EmployeeStatusChangeSubmitPayload,
) -> EmployeeStatusManagementPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    actor_id = scope.user_id
    assert actor_id is not None

    record_id = to_object_id(payload.record_id, "record_id")
    employee = await EmployeeRecord.get(record_id)
    if employee is None or employee.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Employee record not found", status_code=404)
    user = await User.get(employee.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="Employee user not found", status_code=404)

    to_key = (payload.new_status or "").strip().lower()
    try:
        to_status = FacultyEmploymentStatus(to_key)
    except ValueError as exc:
        raise AppError(code="VALIDATION", message="Invalid status", status_code=422) from exc
    if not (payload.reason or "").strip():
        raise AppError(code="VALIDATION", message="Reason is required", status_code=422)

    effective = payload.effective_date or utcnow().date()
    from_status = employee.employment_status
    from_label = _status_label(from_status)
    to_label = _status_label(to_status)

    doc = EmployeeStatusChangeRequest(
        tenant_id=tenant_id,
        employee_record_id=employee.id,
        user_id=employee.user_id,
        from_status=from_status.value,
        from_status_label=from_label,
        to_status=to_status.value,
        to_status_label=to_label,
        reason=payload.reason.strip(),
        effective_date=effective,
        approval_status=EmployeeStatusChangeApproval.PENDING,
        requested_by=actor_id,
    )
    await doc.insert()

    await FacultyEmploymentHistory(
        tenant_id=tenant_id,
        user_id=employee.user_id,
        event_type="status_review",
        from_status=from_status.value,
        to_status=to_status.value,
        note=payload.reason.strip(),
        effective_date=effective,
        actor_id=actor_id,
    ).insert()

    if payload.approve_immediately:
        await _approve_request(scope, doc)

    return await get_employee_status_management_page(
        scope,
        page=payload.page,
        selected_request_id=str(doc.id),
    )


async def _approve_request(scope: AccessScope, doc: EmployeeStatusChangeRequest) -> None:
    if doc.approval_status != EmployeeStatusChangeApproval.PENDING:
        return
    tenant_id = doc.tenant_id
    actor_id = scope.user_id
    assert actor_id is not None

    try:
        new_status = FacultyEmploymentStatus(doc.to_status)
    except ValueError as exc:
        raise AppError(code="VALIDATION", message="Invalid target status", status_code=422) from exc

    await _apply_employment_status(
        tenant_id,
        doc.user_id,
        new_status,
        actor_id=actor_id,
        effective=doc.effective_date,
        note=doc.reason,
    )

    doc.approval_status = EmployeeStatusChangeApproval.APPROVED
    doc.decided_by = actor_id
    doc.decided_at = utcnow()
    await doc.save()


async def approve_employee_status_change(
    scope: AccessScope,
    *,
    request_id: str,
    page: int = 1,
) -> EmployeeStatusManagementPageRead:
    authorize(scope, Permission.FACULTY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await EmployeeStatusChangeRequest.get(to_object_id(request_id, "request_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Status change request not found", status_code=404)
    await _approve_request(scope, doc)
    return await get_employee_status_management_page(scope, page=page, selected_request_id=request_id)