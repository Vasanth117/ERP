"""Student withdrawal / discontinuation workflow (CA 06.14 — Status tab)."""

from __future__ import annotations

from datetime import date, datetime

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.all_students_list_page_service import _fee_presentation, _register_number
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import (
    InstitutionFieldOption,
    StudentWithdrawalClearanceRow,
    StudentWithdrawalDiscontinuationPageRead,
    StudentWithdrawalProcessStep,
    StudentWithdrawalSavePayload,
    StudentWithdrawalSubmitPayload,
    StudentWithdrawalWizardStep,
)
from app.modules.college_admin.student_admin_models import (
    StudentLifecycleStatus,
    StudentRecord,
    StudentStatusHistory,
    StudentWithdrawalRequest,
    StudentWithdrawalType,
    StudentWithdrawalWorkflowStatus,
)
from app.modules.finance.finance_models import StudentFeeDemand
from app.modules.hostel.hostel_models import HostelRoomAllocation
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryFineStatus
from app.modules.library.library_models import LibraryCirculation, LibraryFine
from app.modules.students.enums import StudentEnrollmentStatus
from app.modules.students.models import StudentProfile

_CLEARANCE_DEPARTMENTS = (
    ("library", "Library"),
    ("hostel", "Hostel"),
    ("accounts", "Accounts"),
    ("department", "Department"),
)

_WIZARD_STEPS = (
    ("request", "Request", 1),
    ("clearances", "Clearances", 2),
    ("approval", "Approval", 3),
    ("certificates", "Certificates", 4),
)

_WITHDRAWAL_TYPE_OPTIONS = [
    InstitutionFieldOption(value=StudentWithdrawalType.WITHDRAWAL.value, label="Withdrawal"),
    InstitutionFieldOption(value=StudentWithdrawalType.DISCONTINUATION.value, label="Discontinuation"),
]

_CANCEL_HREF = "/college-admin/students/student-status-management"


def _short_date(value: datetime | date | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        value = value.date()
    return value.strftime("%d %b")


async def _resolve_clearance(
    key: str,
    *,
    tenant_id,
    user_id,
    record: StudentRecord,
    fee_demands: list[StudentFeeDemand],
    snapshots: dict[str, str],
) -> tuple[str, str, str, dict[str, str]]:
    """Return status_label, tone, cleared_on_label, updated_snapshots."""
    snapshots = dict(snapshots or {})
    now_label = _short_date(utcnow())
    pending = ("Pending", "warning", "—")
    cleared = lambda: ("Cleared", "success", snapshots.get(key) or now_label)

    if key == "library":
        active = await LibraryCirculation.find(
            Eq(LibraryCirculation.tenant_id, tenant_id),
            Eq(LibraryCirculation.student_user_id, user_id),
            In(
                LibraryCirculation.status,
                [LibraryCirculationStatus.ACTIVE, LibraryCirculationStatus.OVERDUE],
            ),
        ).count()
        open_fines = await LibraryFine.find(
            Eq(LibraryFine.tenant_id, tenant_id),
            Eq(LibraryFine.student_user_id, user_id),
            In(
                LibraryFine.status,
                [LibraryFineStatus.OPEN, LibraryFineStatus.PENDING_WAIVER, LibraryFineStatus.PENDING_WRITEOFF],
            ),
        ).count()
        if active or open_fines:
            return (*pending, snapshots)
        if key not in snapshots:
            snapshots[key] = now_label
        label, tone, cleared_on = cleared()
        return label, tone, cleared_on, snapshots

    if key == "hostel":
        alloc = await HostelRoomAllocation.find_one(
            Eq(HostelRoomAllocation.tenant_id, tenant_id),
            Eq(HostelRoomAllocation.student_user_id, user_id),
        )
        if alloc is not None:
            return (*pending, snapshots)
        if key not in snapshots:
            snapshots[key] = now_label
        label, tone, cleared_on = cleared()
        return label, tone, cleared_on, snapshots

    if key == "accounts":
        fee_label, _ = _fee_presentation(fee_demands)
        if fee_label in ("Overdue", "Partial"):
            return (*pending, snapshots)
        if key not in snapshots:
            snapshots[key] = now_label
        label, tone, cleared_on = cleared()
        return label, tone, cleared_on, snapshots

    if key == "department":
        if record.department_id is None:
            return (*pending, snapshots)
        if key not in snapshots:
            snapshots[key] = now_label
        label, tone, cleared_on = cleared()
        return label, tone, cleared_on, snapshots

    return "—", "muted", "—", snapshots


def _active_step(
    workflow_status: StudentWithdrawalWorkflowStatus,
    *,
    all_cleared: bool,
    any_pending: bool,
) -> str:
    if workflow_status == StudentWithdrawalWorkflowStatus.DRAFT:
        return "request"
    if workflow_status == StudentWithdrawalWorkflowStatus.SUBMITTED:
        if any_pending:
            return "clearances"
        return "approval"
    if workflow_status in (StudentWithdrawalWorkflowStatus.APPROVED, StudentWithdrawalWorkflowStatus.COMPLETED):
        return "certificates"
    return "approval"


def _process_steps(
    doc: StudentWithdrawalRequest,
    *,
    active_key: str,
    any_pending: bool,
) -> list[StudentWithdrawalProcessStep]:
    steps: list[StudentWithdrawalProcessStep] = []
    received = _short_date(doc.submitted_at or doc.created_at)
    steps.append(
        StudentWithdrawalProcessStep(
            key="request_received",
            label="Request received",
            status_label=received,
            tone="success",
        )
    )
    if doc.workflow_status == StudentWithdrawalWorkflowStatus.DRAFT:
        steps.append(
            StudentWithdrawalProcessStep(
                key="clearances",
                label="Clearances in progress",
                status_label="After submit",
                tone="muted",
            )
        )
    elif active_key == "clearances" or any_pending:
        steps.append(
            StudentWithdrawalProcessStep(
                key="clearances",
                label="Clearances in progress",
                status_label="Now",
                tone="warning",
            )
        )
    else:
        steps.append(
            StudentWithdrawalProcessStep(
                key="clearances",
                label="Clearances in progress",
                status_label="Completed",
                tone="success",
            )
        )

    if doc.workflow_status in (StudentWithdrawalWorkflowStatus.APPROVED, StudentWithdrawalWorkflowStatus.COMPLETED):
        steps.append(
            StudentWithdrawalProcessStep(
                key="approval",
                label="College Admin approval",
                status_label="Approved",
                tone="success",
            )
        )
    elif doc.workflow_status == StudentWithdrawalWorkflowStatus.SUBMITTED and not any_pending:
        steps.append(
            StudentWithdrawalProcessStep(
                key="approval",
                label="College Admin approval",
                status_label="Next",
                tone="info",
            )
        )
    else:
        steps.append(
            StudentWithdrawalProcessStep(
                key="approval",
                label="College Admin approval",
                status_label="Next",
                tone="muted",
            )
        )

    if doc.workflow_status in (StudentWithdrawalWorkflowStatus.APPROVED, StudentWithdrawalWorkflowStatus.COMPLETED):
        steps.append(
            StudentWithdrawalProcessStep(
                key="certificates",
                label="TC and certificates",
                status_label="In progress" if doc.workflow_status == StudentWithdrawalWorkflowStatus.APPROVED else "Completed",
                tone="info" if doc.workflow_status == StudentWithdrawalWorkflowStatus.APPROVED else "success",
            )
        )
    else:
        steps.append(
            StudentWithdrawalProcessStep(
                key="certificates",
                label="TC and certificates",
                status_label="After approval",
                tone="muted",
            )
        )
    return steps


async def _get_or_create_draft(
    scope: AccessScope,
    tenant_id,
    *,
    record_id: str | None,
    request_id: str | None,
) -> tuple[StudentWithdrawalRequest, StudentRecord, User]:
    if request_id:
        doc = await StudentWithdrawalRequest.get(to_object_id(request_id, "request_id"))
        if doc is None or doc.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Withdrawal request not found", status_code=404)
        record = await StudentRecord.get(doc.student_record_id)
        user = await User.get(doc.user_id) if record else None
        if record is None or user is None:
            raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
        return doc, record, user

    if not record_id:
        raise AppError(code="VALIDATION", message="Select a student to start withdrawal", status_code=422)

    rid = to_object_id(record_id, "record_id")
    record = await StudentRecord.get(rid)
    if record is None or record.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Student record not found", status_code=404)
    user = await User.get(record.user_id)
    if user is None:
        raise AppError(code="NOT_FOUND", message="Student user not found", status_code=404)

    existing = await StudentWithdrawalRequest.find_one(
        Eq(StudentWithdrawalRequest.tenant_id, tenant_id),
        Eq(StudentWithdrawalRequest.student_record_id, record.id),
        Eq(StudentWithdrawalRequest.workflow_status, StudentWithdrawalWorkflowStatus.DRAFT),
    )
    if existing:
        return existing, record, user

    doc = StudentWithdrawalRequest(
        tenant_id=tenant_id,
        student_record_id=record.id,
        user_id=record.user_id,
        requested_by=scope.user_id,
    )
    await doc.insert()
    return doc, record, user


async def get_student_withdrawal_discontinuation_page(
    scope: AccessScope,
    *,
    record_id: str | None = None,
    request_id: str | None = None,
) -> StudentWithdrawalDiscontinuationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()

    if not record_id and not request_id:
        return StudentWithdrawalDiscontinuationPageRead(
            page_title="Student Withdrawal / Discontinuation",
            page_subtitle="Controlled exit workflow",
            cancel_label="Cancel",
            cancel_href=_CANCEL_HREF,
            submit_for_approval_label="Submit for approval",
            wizard_steps=[StudentWithdrawalWizardStep(key=k, label=l, step_number=n) for k, l, n in _WIZARD_STEPS],
            active_step_key="request",
            active_step_index=0,
            withdrawal_request_section_title="Withdrawal request",
            student_field_label="Student",
            type_field_label="Type",
            last_attendance_field_label="Last date of attendance",
            reason_field_label="Reason",
            student_line="",
            selected_record_id="",
            withdrawal_type="",
            last_attendance_date="",
            reason="",
            withdrawal_type_options=_WITHDRAWAL_TYPE_OPTIONS,
            clearances_section_title="Clearances",
            clearance_table_headers=["Department", "Status", "Cleared on"],
            clearance_rows=[],
            clearances_summary_label="0 of 0 cleared",
            process_section_title="Process",
            process_steps=[],
            request_id=None,
            can_submit=False,
            footer_disclaimer="Live institutional data · Withdrawal and discontinuation records · All times IST",
            footer_snapshot_label="Snapshot",
            generated_at=now,
        )

    doc, record, user = await _get_or_create_draft(
        scope, tenant_id, record_id=record_id, request_id=request_id
    )
    profile = await StudentProfile.find_one(
        Eq(StudentProfile.tenant_id, tenant_id),
        Eq(StudentProfile.user_id, record.user_id),
    )
    register = _register_number(record, profile)
    student_line = f"{user.full_name} · {register}"

    fee_demands = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        Eq(StudentFeeDemand.student_user_id, record.user_id),
    ).to_list()

    snapshots = dict(doc.clearance_snapshots)
    clearance_rows: list[StudentWithdrawalClearanceRow] = []
    cleared_count = 0
    any_pending = False
    for key, label in _CLEARANCE_DEPARTMENTS:
        status_label, tone, cleared_on, snapshots = await _resolve_clearance(
            key,
            tenant_id=tenant_id,
            user_id=record.user_id,
            record=record,
            fee_demands=fee_demands,
            snapshots=snapshots,
        )
        if status_label == "Cleared":
            cleared_count += 1
        else:
            any_pending = True
        clearance_rows.append(
            StudentWithdrawalClearanceRow(
                department_key=key,
                department_label=label,
                status_label=status_label,
                status_tone=tone,
                cleared_on_label=cleared_on,
            )
        )

    if snapshots != doc.clearance_snapshots:
        doc.clearance_snapshots = snapshots
        doc.updated_at = utcnow()
        await doc.save()

    active_key = _active_step(doc.workflow_status, all_cleared=not any_pending, any_pending=any_pending)
    active_index = next(i for i, (k, _, _) in enumerate(_WIZARD_STEPS) if k == active_key)

    last_attendance = ""
    if doc.last_attendance_date:
        last_attendance = doc.last_attendance_date.isoformat()

    can_submit = doc.workflow_status == StudentWithdrawalWorkflowStatus.DRAFT

    return StudentWithdrawalDiscontinuationPageRead(
        page_title="Student Withdrawal / Discontinuation",
        page_subtitle="Controlled exit workflow",
        cancel_label="Cancel",
        cancel_href=_CANCEL_HREF,
        submit_for_approval_label="Submit for approval",
        wizard_steps=[StudentWithdrawalWizardStep(key=k, label=l, step_number=n) for k, l, n in _WIZARD_STEPS],
        active_step_key=active_key,
        active_step_index=active_index,
        withdrawal_request_section_title="Withdrawal request",
        student_field_label="Student",
        type_field_label="Type",
        last_attendance_field_label="Last date of attendance",
        reason_field_label="Reason",
        student_line=student_line,
        selected_record_id=str(record.id),
        withdrawal_type=doc.withdrawal_type.value,
        last_attendance_date=last_attendance,
        reason=doc.reason,
        withdrawal_type_options=_WITHDRAWAL_TYPE_OPTIONS,
        clearances_section_title="Clearances",
        clearance_table_headers=["Department", "Status", "Cleared on"],
        clearance_rows=clearance_rows,
        clearances_summary_label=f"{cleared_count} of {len(clearance_rows)} cleared",
        process_section_title="Process",
        process_steps=_process_steps(doc, active_key=active_key, any_pending=any_pending),
        request_id=str(doc.id),
        can_submit=can_submit,
        footer_disclaimer="Live institutional data · Withdrawal and discontinuation records · All times IST",
        footer_snapshot_label="Snapshot",
        generated_at=now,
    )


async def save_student_withdrawal_draft(
    scope: AccessScope,
    payload: StudentWithdrawalSavePayload,
) -> StudentWithdrawalDiscontinuationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc, _, _ = await _get_or_create_draft(
        scope,
        tenant_id,
        record_id=payload.record_id,
        request_id=payload.request_id,
    )
    if doc.workflow_status != StudentWithdrawalWorkflowStatus.DRAFT:
        raise AppError(code="VALIDATION", message="Only draft requests can be edited", status_code=422)

    wtype = (payload.withdrawal_type or "").strip().lower()
    if wtype in (StudentWithdrawalType.WITHDRAWAL.value, StudentWithdrawalType.DISCONTINUATION.value):
        doc.withdrawal_type = StudentWithdrawalType(wtype)
    if payload.last_attendance_date:
        try:
            doc.last_attendance_date = date.fromisoformat(payload.last_attendance_date)
        except ValueError as exc:
            raise AppError(code="VALIDATION", message="Invalid attendance date", status_code=422) from exc
    if payload.reason is not None:
        doc.reason = payload.reason.strip()
    doc.updated_at = utcnow()
    await doc.save()

    return await get_student_withdrawal_discontinuation_page(
        scope,
        request_id=str(doc.id),
    )


async def submit_student_withdrawal_for_approval(
    scope: AccessScope,
    payload: StudentWithdrawalSubmitPayload,
) -> StudentWithdrawalDiscontinuationPageRead:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc, record, user = await _get_or_create_draft(
        scope,
        tenant_id,
        record_id=payload.record_id,
        request_id=payload.request_id,
    )
    if doc.workflow_status != StudentWithdrawalWorkflowStatus.DRAFT:
        raise AppError(code="VALIDATION", message="Request already submitted", status_code=422)

    await save_student_withdrawal_draft(
        scope,
        StudentWithdrawalSavePayload(
            record_id=str(record.id),
            request_id=str(doc.id),
            withdrawal_type=payload.withdrawal_type or doc.withdrawal_type.value,
            last_attendance_date=payload.last_attendance_date
            or (doc.last_attendance_date.isoformat() if doc.last_attendance_date else None),
            reason=payload.reason if payload.reason is not None else doc.reason,
        ),
    )

    doc = await StudentWithdrawalRequest.get(doc.id)
    assert doc is not None
    if not (doc.reason or "").strip():
        raise AppError(code="VALIDATION", message="Reason is required", status_code=422)

    doc.workflow_status = StudentWithdrawalWorkflowStatus.SUBMITTED
    doc.submitted_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()

    fee_demands = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        Eq(StudentFeeDemand.student_user_id, record.user_id),
    ).to_list()
    snapshots = dict(doc.clearance_snapshots)
    any_pending = False
    for key, _ in _CLEARANCE_DEPARTMENTS:
        status_label, _, _, snapshots = await _resolve_clearance(
            key,
            tenant_id=tenant_id,
            user_id=record.user_id,
            record=record,
            fee_demands=fee_demands,
            snapshots=snapshots,
        )
        if status_label != "Cleared":
            any_pending = True
    doc.clearance_snapshots = snapshots
    await doc.save()

    if not any_pending:
        target = (
            StudentLifecycleStatus.WITHDRAWN
            if doc.withdrawal_type == StudentWithdrawalType.WITHDRAWAL
            else StudentLifecycleStatus.DISCONTINUED
        )
        previous = record.lifecycle_status.value
        record.lifecycle_status = target
        record.enrollment_status = StudentEnrollmentStatus.WITHDRAWN
        record.updated_at = utcnow()
        await record.save()
        user.is_active = False
        user.updated_at = utcnow()
        await user.save()
        doc.workflow_status = StudentWithdrawalWorkflowStatus.APPROVED
        doc.approved_at = utcnow()
        doc.approved_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
        await StudentStatusHistory(
            tenant_id=tenant_id,
            student_record_id=record.id,
            user_id=record.user_id,
            from_status=previous,
            to_status=target.value,
            reason=doc.reason,
            actor_id=scope.user_id,
        ).insert()

    return await get_student_withdrawal_discontinuation_page(scope, request_id=str(doc.id))


async def cancel_student_withdrawal_draft(
    scope: AccessScope,
    *,
    request_id: str,
) -> None:
    authorize(scope, Permission.STUDENT_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await StudentWithdrawalRequest.get(to_object_id(request_id, "request_id"))
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Withdrawal request not found", status_code=404)
    if doc.workflow_status == StudentWithdrawalWorkflowStatus.DRAFT:
        await doc.delete()