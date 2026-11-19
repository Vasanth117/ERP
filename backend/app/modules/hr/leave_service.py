"""Leave administration — types, balances, applications, adjustments."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.hr_admin_models import EmployeeLeavePolicy
from app.modules.hr.employee_sync import log_hr_activity
from app.modules.hr.enums import HrStaffActivityType, LeaveDayPortion, LeaveRequestStatus
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.leave_attendance_sync import apply_leave_to_attendance
from app.modules.hr.leave_balance_service import get_or_create_balance, post_balance_transaction
from app.modules.hr.leave_models import HrLeaveBalance, HrLeaveTypeConfig
from app.modules.hr.leave_schemas import (
    LeaveAdjustmentCreate,
    LeaveApplicationCreate,
    LeaveApplicationReview,
    LeaveBalanceRead,
    LeaveOverviewStats,
    LeavePolicyUpsert,
    LeaveReports,
    LeaveRequestRead,
    LeaveTypeConfigRead,
    LeaveTypeConfigUpsert,
)
from app.modules.hr.leave_working_days import count_working_leave_days
from app.modules.hr.models import LeaveRequest
from app.modules.hr.policy import authorize_hr_leave_manage, authorize_hr_leave_read, require_hr_tenant_scope


async def leave_overview(scope: AccessScope) -> LeaveOverviewStats:
    authorize_hr_leave_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    stats = LeaveOverviewStats()
    rows = await LeaveRequest.find(Eq(LeaveRequest.tenant_id, tenant_id)).to_list()
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    dept_by_user = {str(e.user_id): str(e.department_id) if e.department_id else "unassigned" for e in employees}
    today = date.today()
    for row in rows:
        stats.total_requests += 1
        if row.status in {
            LeaveRequestStatus.SUBMITTED,
            LeaveRequestStatus.PENDING_MANAGER,
            LeaveRequestStatus.PENDING_HR,
            LeaveRequestStatus.CLARIFICATION_REQUESTED,
        }:
            stats.pending += 1
            stats.immediate_action += 1
        elif row.status == LeaveRequestStatus.APPROVED:
            stats.approved += 1
            if row.start_date <= today <= row.end_date:
                stats.currently_on_leave += 1
            elif row.start_date > today:
                stats.upcoming_approved += 1
        elif row.status == LeaveRequestStatus.REJECTED:
            stats.rejected += 1
        elif row.status == LeaveRequestStatus.CANCELLED:
            stats.cancelled += 1
        if row.status == LeaveRequestStatus.APPROVED:
            dept = dept_by_user.get(str(row.employee_user_id), "unassigned")
            stats.department_usage[dept] = stats.department_usage.get(dept, 0) + int(row.working_days or 1)
    return stats


async def upsert_leave_type(scope: AccessScope, payload: LeaveTypeConfigUpsert) -> LeaveTypeConfigRead:
    authorize_hr_leave_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrLeaveTypeConfig.find_one(
        Eq(HrLeaveTypeConfig.tenant_id, tenant_id),
        Eq(HrLeaveTypeConfig.leave_type_code, payload.leave_type_code),
    )
    if doc:
        doc.title = payload.title
        doc.rules = payload.rules
        doc.employee_categories = payload.employee_categories
        doc.effective_from = payload.effective_from
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrLeaveTypeConfig(
            tenant_id=tenant_id,
            leave_type_code=payload.leave_type_code,
            title=payload.title,
            rules=payload.rules,
            employee_categories=payload.employee_categories,
            effective_from=payload.effective_from,
            actor_id=scope.user_id,
        )
        await doc.insert()
    return LeaveTypeConfigRead.from_document(doc)


async def list_leave_types(scope: AccessScope) -> list[LeaveTypeConfigRead]:
    authorize_hr_leave_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrLeaveTypeConfig.find(Eq(HrLeaveTypeConfig.tenant_id, tenant_id), Eq(HrLeaveTypeConfig.is_active, True)).to_list()
    return [LeaveTypeConfigRead.from_document(r) for r in rows]


async def create_leave_application(scope: AccessScope, payload: LeaveApplicationCreate) -> LeaveRequestRead:
    authorize_hr_leave_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    if payload.end_date < payload.start_date:
        raise AppError(code="VALIDATION_ERROR", message="Leave end date must be on or after start date", status_code=422)
    working_days = await count_working_leave_days(tenant_id, payload.start_date, payload.end_date, payload.day_portion)
    policy = await EmployeeLeavePolicy.find_one(
        Eq(EmployeeLeavePolicy.tenant_id, tenant_id),
        Eq(EmployeeLeavePolicy.leave_type, payload.leave_type),
    )
    period_year = payload.start_date.year
    type_cfg = await HrLeaveTypeConfig.find_one(
        Eq(HrLeaveTypeConfig.tenant_id, tenant_id),
        Eq(HrLeaveTypeConfig.leave_type_code, payload.leave_type),
    )
    if policy:
        entitlement = policy.annual_quota_days
    elif type_cfg:
        entitlement = float(type_cfg.rules.get("annual_entitlement", 12.0))
    else:
        entitlement = 12.0
    bal = await get_or_create_balance(tenant_id, uid, payload.leave_type, period_year, annual_entitlement=entitlement)
    if bal.available < working_days:
        raise AppError(code="VALIDATION_ERROR", message="Insufficient leave balance", status_code=422)

    requires_manager = True
    if policy and policy.rules.get("requires_manager_approval") is False:
        requires_manager = False
    status = LeaveRequestStatus.PENDING_MANAGER if requires_manager else LeaveRequestStatus.PENDING_HR

    req = LeaveRequest(
        tenant_id=tenant_id,
        employee_user_id=uid,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        day_portion=payload.day_portion,
        working_days=working_days,
        reason=payload.reason,
        document_refs=payload.document_refs,
        contact_during_leave=payload.contact_during_leave,
        alternate_arrangement=payload.alternate_arrangement,
        status=status,
    )
    await req.insert()
    await post_balance_transaction(
        tenant_id=tenant_id,
        employee_user_id=uid,
        leave_type=payload.leave_type,
        period_year=period_year,
        transaction_type="pending_reserve",
        amount_days=-working_days,
        reason=f"Reserved for leave {req.id}",
        actor_id=scope.user_id,
        reference_type="leave_request",
        reference_id=str(req.id),
    )
    return LeaveRequestRead.from_document(req)


async def _finalize_approval(scope: AccessScope, req: LeaveRequest) -> None:
    period_year = req.start_date.year
    if req.balance_days_deducted:
        return
    if req.working_days <= 0:
        req.working_days = await count_working_leave_days(req.tenant_id, req.start_date, req.end_date, req.day_portion)
    await post_balance_transaction(
        tenant_id=req.tenant_id,
        employee_user_id=req.employee_user_id,
        leave_type=req.leave_type,
        period_year=period_year,
        transaction_type="pending_release",
        amount_days=req.working_days,
        reason=f"Release pending for approved leave {req.id}",
        actor_id=scope.user_id,
        reference_type="leave_request",
        reference_id=str(req.id),
    )
    await post_balance_transaction(
        tenant_id=req.tenant_id,
        employee_user_id=req.employee_user_id,
        leave_type=req.leave_type,
        period_year=period_year,
        transaction_type="usage",
        amount_days=-req.working_days,
        reason=f"Leave approved {req.id}",
        actor_id=scope.user_id,
        reference_type="leave_request",
        reference_id=str(req.id),
    )
    req.balance_days_deducted = req.working_days
    await apply_leave_to_attendance(req)
    await enqueue_hr_notification(
        req.tenant_id,
        event_type="hr.leave.approved",
        aggregate_type="leave_request",
        aggregate_id=str(req.id),
        title="Leave approved",
        body=f"Your {req.leave_type} leave from {req.start_date} to {req.end_date} was approved",
        recipient_user_id=req.employee_user_id,
        dedupe_key=f"hr:leave_approved:{req.id}",
    )


async def review_leave_application(scope: AccessScope, leave_id: str, payload: LeaveApplicationReview) -> LeaveRequestRead:
    authorize_hr_leave_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    lid = to_object_id(leave_id, "leave_id")
    req = await LeaveRequest.get(lid)
    if req is None or req.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Leave request not found", status_code=404)

    if payload.decision == "manager_approve" and req.status in {LeaveRequestStatus.SUBMITTED, LeaveRequestStatus.PENDING_MANAGER}:
        req.status = LeaveRequestStatus.PENDING_HR
        req.manager_reviewer_id = scope.user_id
    elif payload.decision == "hr_approve" and req.status in {LeaveRequestStatus.PENDING_HR, LeaveRequestStatus.SUBMITTED}:
        req.status = LeaveRequestStatus.APPROVED
        req.hr_reviewer_id = scope.user_id
        await _finalize_approval(scope, req)
    elif payload.decision == "approve":
        req.status = LeaveRequestStatus.APPROVED
        req.hr_reviewer_id = scope.user_id
        await _finalize_approval(scope, req)
    elif payload.decision == "reject":
        req.status = LeaveRequestStatus.REJECTED
        await post_balance_transaction(
            tenant_id=tenant_id,
            employee_user_id=req.employee_user_id,
            leave_type=req.leave_type,
            period_year=req.start_date.year,
            transaction_type="pending_release",
            amount_days=req.working_days,
            reason=f"Rejected leave {req.id}",
            actor_id=scope.user_id,
            reference_type="leave_request",
            reference_id=str(req.id),
        )
    elif payload.decision == "request_clarification":
        req.status = LeaveRequestStatus.CLARIFICATION_REQUESTED
    elif payload.decision == "cancel":
        if req.status != LeaveRequestStatus.APPROVED:
            req.status = LeaveRequestStatus.CANCELLED
            await post_balance_transaction(
                tenant_id=tenant_id,
                employee_user_id=req.employee_user_id,
                leave_type=req.leave_type,
                period_year=req.start_date.year,
                transaction_type="pending_release",
                amount_days=req.working_days,
                reason=f"Cancelled leave {req.id}",
                actor_id=scope.user_id,
                reference_type="leave_request",
                reference_id=str(req.id),
            )
        else:
            req.status = LeaveRequestStatus.CANCELLED
            await post_balance_transaction(
                tenant_id=tenant_id,
                employee_user_id=req.employee_user_id,
                leave_type=req.leave_type,
                period_year=req.start_date.year,
                transaction_type="credit",
                amount_days=req.balance_days_deducted or req.working_days,
                reason=f"Reversal for cancelled leave {req.id}",
                actor_id=scope.user_id,
                reference_type="leave_request",
                reference_id=str(req.id),
            )
            req.cancellation_reason = payload.note
    else:
        raise AppError(code="CONFLICT", message="Invalid leave decision", status_code=409)

    req.approver_note = payload.note
    req.updated_at = utcnow()
    await req.save()
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.LEAVE_APPLICATION,
        f"Leave request {req.status.value}",
        actor_id=scope.user_id,
        employee_user_id=req.employee_user_id,
        resource_type="leave_request",
        resource_id=str(req.id),
        status_label=req.status.value,
    )
    return LeaveRequestRead.from_document(req)


async def apply_leave_adjustment(scope: AccessScope, payload: LeaveAdjustmentCreate) -> LeaveBalanceRead:
    authorize_hr_leave_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    await post_balance_transaction(
        tenant_id=tenant_id,
        employee_user_id=uid,
        leave_type=payload.leave_type,
        period_year=payload.period_year,
        transaction_type="credit" if payload.amount_days >= 0 else "usage",
        amount_days=payload.amount_days,
        reason=payload.reason,
        actor_id=scope.user_id,
        reference_type="leave_adjustment",
        reference_id=None,
    )
    bal = await HrLeaveBalance.find_one(
        Eq(HrLeaveBalance.tenant_id, tenant_id),
        Eq(HrLeaveBalance.employee_user_id, uid),
        Eq(HrLeaveBalance.leave_type, payload.leave_type),
        Eq(HrLeaveBalance.period_year, payload.period_year),
    )
    assert bal is not None
    return LeaveBalanceRead.from_document(bal)


async def list_leave_requests(scope: AccessScope, pagination: Pagination, status: LeaveRequestStatus | None = None) -> Page[LeaveRequestRead]:
    authorize_hr_leave_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(LeaveRequest.tenant_id, tenant_id)]
    if status:
        filters.append(Eq(LeaveRequest.status, status))
    q = LeaveRequest.find(*filters)
    total = await q.count()
    rows = await q.sort(-LeaveRequest.created_at).skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[LeaveRequestRead.from_document(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def upsert_leave_policy(scope: AccessScope, payload: LeavePolicyUpsert) -> dict:
    authorize_hr_leave_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await EmployeeLeavePolicy.find_one(
        Eq(EmployeeLeavePolicy.tenant_id, tenant_id),
        Eq(EmployeeLeavePolicy.leave_type, payload.leave_type),
    )
    if doc:
        doc.annual_quota_days = payload.annual_quota_days
        doc.requires_approval = payload.requires_approval
        doc.rules = payload.rules
        doc.version += 1
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = EmployeeLeavePolicy(
            tenant_id=tenant_id,
            leave_type=payload.leave_type,
            annual_quota_days=payload.annual_quota_days,
            requires_approval=payload.requires_approval,
            rules=payload.rules,
            updated_by=scope.user_id,
        )
        await doc.insert()
    return {"leave_type": doc.leave_type, "version": doc.version}


async def leave_reports(scope: AccessScope, period_year: int | None = None) -> LeaveReports:
    authorize_hr_leave_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    year = period_year or date.today().year
    rows = await LeaveRequest.find(Eq(LeaveRequest.tenant_id, tenant_id)).to_list()
    reports = LeaveReports(period_year=year)
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    dept_by_user = {str(e.user_id): str(e.department_id) if e.department_id else "unassigned" for e in employees}
    today = date.today()
    for row in rows:
        if row.start_date.year != year and row.end_date.year != year:
            continue
        reports.leave_type_distribution[row.leave_type] = reports.leave_type_distribution.get(row.leave_type, 0) + 1
        dept = dept_by_user.get(str(row.employee_user_id), "unassigned")
        reports.department_usage[dept] = reports.department_usage.get(dept, 0) + row.working_days or 1
        if row.status in {LeaveRequestStatus.SUBMITTED, LeaveRequestStatus.PENDING_MANAGER, LeaveRequestStatus.PENDING_HR}:
            reports.pending_approvals += 1
        if row.status == LeaveRequestStatus.APPROVED and row.start_date > today:
            reports.upcoming_leaves += 1
        if row.status == LeaveRequestStatus.APPROVED:
            reports.approved_count += 1
    balances = await HrLeaveBalance.find(Eq(HrLeaveBalance.tenant_id, tenant_id), Eq(HrLeaveBalance.period_year, year)).to_list()
    for bal in balances:
        reports.balance_snapshots.append(
            LeaveBalanceRead.from_document(bal),
        )
    return reports


async def get_employee_balances(scope: AccessScope, employee_user_id: str, period_year: int) -> list[LeaveBalanceRead]:
    authorize_hr_leave_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(employee_user_id, "employee_user_id")
    rows = await HrLeaveBalance.find(
        Eq(HrLeaveBalance.tenant_id, tenant_id),
        Eq(HrLeaveBalance.employee_user_id, uid),
        Eq(HrLeaveBalance.period_year, period_year),
    ).to_list()
    return [LeaveBalanceRead.from_document(r) for r in rows]