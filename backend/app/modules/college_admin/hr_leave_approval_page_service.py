"""HR leave approval workflow page (CA 11 — Leave Approval)."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from beanie.odm.operators.find.comparison import Eq, In

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyRecord
from app.modules.college_admin.hr_admin_models import EmployeeLeaveApproval
from app.modules.college_admin.hr_dashboard_page_service import (
    _PENDING_LEAVE,
    _approver_label,
    _format_leave_dates,
    _leave_days,
    _leave_type_label,
)
from app.modules.college_admin.identity_models import InstitutionDepartment
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.schemas import HrLeaveApprovalPageRead, HrLeaveApprovalStep, InstitutionFieldOption
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.leave_models import HrLeaveBalance
from app.modules.hr.models import LeaveRequest

_IST = ZoneInfo("Asia/Kolkata")

_DECISION_OPTIONS = [
    InstitutionFieldOption(value=LeaveRequestStatus.APPROVED.value, label="Approve"),
    InstitutionFieldOption(value=LeaveRequestStatus.REJECTED.value, label="Reject"),
]


def _fmt_snapshot(now: datetime) -> str:
    return now.astimezone(_IST).strftime("Snapshot · %d %b %Y, %H:%M IST")


def _fmt_step_date(dt: datetime | None) -> str:
    if dt is None:
        return "Pending"
    return dt.astimezone(_IST).strftime("%d %b")


def _employee_display_code(
    user: User | None,
    emp: EmployeeRecord | None,
    faculty: FacultyRecord | None,
) -> str:
    code = None
    if emp and emp.employee_id:
        code = emp.employee_id
    elif faculty and faculty.faculty_code:
        code = faculty.faculty_code
    name = user.full_name if user and user.full_name else "—"
    if code:
        return f"{name} · {code}"
    return name


async def _balance_after_label(
    tenant_id,
    req: LeaveRequest,
    period_year: int,
) -> str:
    bal = await HrLeaveBalance.find_one(
        Eq(HrLeaveBalance.tenant_id, tenant_id),
        Eq(HrLeaveBalance.employee_user_id, req.employee_user_id),
        Eq(HrLeaveBalance.leave_type, req.leave_type),
        Eq(HrLeaveBalance.period_year, period_year),
    )
    if bal is None:
        return "—"
    days = _leave_days(req)
    remaining = bal.available - days
    if req.status == LeaveRequestStatus.APPROVED and req.balance_days_deducted is not None:
        remaining = bal.available
    label = f"{max(0, round(remaining, 1))} days"
    return label


def _build_timeline(
    req: LeaveRequest | None,
    dept: InstitutionDepartment | None,
    *,
    has_hr_decision: bool,
) -> list[HrLeaveApprovalStep]:
    if req is None:
        return []

    hod_label = _approver_label(dept)
    steps: list[HrLeaveApprovalStep] = [
        HrLeaveApprovalStep(
            key="applied",
            label="Applied",
            status_label=_fmt_step_date(req.created_at),
            tone="success",
        ),
    ]

    manager_done = req.status not in (LeaveRequestStatus.DRAFT, LeaveRequestStatus.SUBMITTED) or req.manager_reviewer_id
    steps.append(
        HrLeaveApprovalStep(
            key="hod",
            label=hod_label,
            status_label=_fmt_step_date(req.updated_at) if manager_done else "Pending",
            tone="success" if manager_done and req.status != LeaveRequestStatus.REJECTED else "warning",
        ),
    )

    hr_pending = req.status in _PENDING_LEAVE or req.status == LeaveRequestStatus.SUBMITTED
    if req.status == LeaveRequestStatus.APPROVED:
        hr_status = _fmt_step_date(req.updated_at)
        hr_tone = "success"
    elif req.status == LeaveRequestStatus.REJECTED:
        hr_status = _fmt_step_date(req.updated_at)
        hr_tone = "error"
    elif hr_pending:
        hr_status = "Pending"
        hr_tone = "warning"
    else:
        hr_status = _fmt_step_date(req.updated_at)
        hr_tone = "info"

    steps.append(
        HrLeaveApprovalStep(
            key="college_hr",
            label="College Admin / HR",
            status_label=hr_status,
            tone=hr_tone,
        ),
    )

    if req.status == LeaveRequestStatus.APPROVED and has_hr_decision:
        balance_status = "Complete"
        balance_tone = "success"
    elif req.status == LeaveRequestStatus.APPROVED:
        balance_status = "Pending"
        balance_tone = "warning"
    else:
        balance_status = "Not started"
        balance_tone = "muted"

    steps.append(
        HrLeaveApprovalStep(
            key="balance",
            label="Balance updated",
            status_label=balance_status,
            tone=balance_tone,
        ),
    )
    return steps


async def get_hr_leave_approval_page(
    scope: AccessScope,
    *,
    leave_request_id: str | None = None,
) -> HrLeaveApprovalPageRead:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    now = utcnow()
    today = now.astimezone(_IST).date()

    pending = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        In(LeaveRequest.status, list(_PENDING_LEAVE)),
    ).sort("-created_at").to_list()

    selected: LeaveRequest | None = None
    if leave_request_id:
        oid = to_object_id(leave_request_id, "leave_request_id")
        selected = await LeaveRequest.get(oid)
        if selected is None or selected.tenant_id != tenant_id:
            raise AppError(code="NOT_FOUND", message="Leave request not found", status_code=404)
    elif pending:
        selected = pending[0]

    empty_shell = HrLeaveApprovalPageRead(
        page_title="Leave Approval",
        page_subtitle="Review and decide on a leave application",
        selected_leave_request_id=None,
        back_href="/college-admin/hr/leave-management",
        back_label="Leave Management",
        return_label="Return",
        return_href="/college-admin/hr/leave-management",
        reject_label="Reject",
        approve_label="Approve",
        application_card_title="Application",
        employee_field_label="Employee",
        employee_label="—",
        leave_type_field_label="Leave type",
        leave_type_label="—",
        dates_field_label="Dates",
        dates_label="—",
        balance_after_field_label="Balance after",
        balance_after_label="—",
        cover_field_label="Cover arranged",
        cover_label="—",
        decision_card_title="Decision",
        decision_field_label="Decision",
        decision_required=True,
        decision_options=_DECISION_OPTIONS,
        selected_decision=LeaveRequestStatus.APPROVED.value,
        remarks_field_label="Remarks",
        remarks_placeholder="Add remarks for this decision",
        remarks_value="",
        approval_timeline_title="Approval timeline",
        approval_steps=[],
        can_decide=False,
        decide_blocked_message="No pending leave applications",
        footer_disclaimer="Live institutional data · Leave approval · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )

    if selected is None:
        return empty_shell

    user = await User.get(selected.employee_user_id)
    emp = await EmployeeRecord.find_one(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.user_id, selected.employee_user_id),
    )
    faculty = await FacultyRecord.find_one(
        Eq(FacultyRecord.tenant_id, tenant_id),
        Eq(FacultyRecord.user_id, selected.employee_user_id),
    )

    dept_id = emp.department_id if emp and emp.department_id else (faculty.department_id if faculty else None)
    dept = await InstitutionDepartment.get(dept_id) if dept_id else None

    existing_approval = await EmployeeLeaveApproval.find_one(
        Eq(EmployeeLeaveApproval.tenant_id, tenant_id),
        Eq(EmployeeLeaveApproval.leave_request_id, selected.id),
    )

    can_decide = selected.status == LeaveRequestStatus.SUBMITTED and existing_approval is None
    blocked: str | None = None
    if not can_decide:
        if existing_approval:
            blocked = "This leave request has already been reviewed."
        elif selected.status != LeaveRequestStatus.SUBMITTED:
            blocked = "This leave request is not awaiting college HR approval."

    dates_label = f"{_format_leave_dates(selected.start_date, selected.end_date)} · {_leave_days(selected)} days"
    subtitle = f"{user.full_name if user else '—'} · {_leave_type_label(selected.leave_type)} · {dates_label}"

    balance_after = await _balance_after_label(tenant_id, selected, today.year)
    cover = (selected.alternate_arrangement or "—").strip() or "—"

    return HrLeaveApprovalPageRead(
        page_title="Leave Approval",
        page_subtitle=subtitle,
        selected_leave_request_id=str(selected.id),
        back_href="/college-admin/hr/leave-management",
        back_label="Leave Management",
        return_label="Return",
        return_href="/college-admin/hr/leave-management",
        reject_label="Reject",
        approve_label="Approve",
        application_card_title="Application",
        employee_field_label="Employee",
        employee_label=_employee_display_code(user, emp, faculty),
        leave_type_field_label="Leave type",
        leave_type_label=_leave_type_label(selected.leave_type),
        dates_field_label="Dates",
        dates_label=dates_label,
        balance_after_field_label="Balance after",
        balance_after_label=balance_after,
        cover_field_label="Cover arranged",
        cover_label=cover,
        decision_card_title="Decision",
        decision_field_label="Decision",
        decision_required=True,
        decision_options=_DECISION_OPTIONS,
        selected_decision=LeaveRequestStatus.APPROVED.value,
        remarks_field_label="Remarks",
        remarks_placeholder="Add remarks for this decision",
        remarks_value=selected.approver_note or "",
        approval_timeline_title="Approval timeline",
        approval_steps=_build_timeline(selected, dept, has_hr_decision=existing_approval is not None),
        can_decide=can_decide,
        decide_blocked_message=blocked,
        footer_disclaimer="Live institutional data · Leave approval · All times IST",
        footer_snapshot_label=_fmt_snapshot(now),
        generated_at=now,
    )