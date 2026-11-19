"""Payment plans, installment schedules and payment allocation."""

from datetime import date, timedelta
from typing import Any
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.phase6_enums import AssignmentStatus, InstallmentStatus, PaymentPlanStatus
from app.modules.accounts_finance.phase6_models import (
    StudentInstallmentHistory,
    StudentInstallmentPayment,
    StudentInstallmentRescheduleRequest,
    StudentInstallmentSchedule,
    StudentPaymentPlan,
    StudentPaymentPlanAssignment,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_installment_approve,
    authorize_finance_installment_manage,
    authorize_finance_installment_read,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_models import FeeInstallmentSchedule, StudentFeeInvoice


def _build_installments(total: float, defs: list[dict], start_date: date) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not defs:
        rows.append(
            {
                "installment_id": f"inst_{uuid4().hex[:10]}",
                "installment_number": 1,
                "due_date": start_date.isoformat(),
                "amount": round_money(total),
                "paid_amount": 0.0,
                "remaining_amount": round_money(total),
                "status": InstallmentStatus.UNPAID.value,
            }
        )
        return rows
    allocated = 0.0
    for idx, item in enumerate(defs, start=1):
        inst_id = f"inst_{uuid4().hex[:8]}{idx}"
        if item.get("amount") is not None:
            amt = round_money(float(item["amount"]))
        elif item.get("percent") is not None:
            amt = round_money(total * float(item["percent"]) / 100)
        else:
            amt = round_money(total / len(defs))
        days = int(item.get("days_offset", (idx - 1) * 30))
        due = start_date + timedelta(days=days)
        allocated += amt
        rows.append(
            {
                "installment_id": inst_id,
                "installment_number": idx,
                "due_date": due.isoformat(),
                "amount": amt,
                "paid_amount": 0.0,
                "remaining_amount": amt,
                "status": InstallmentStatus.UNPAID.value,
            }
        )
    diff = round_money(total - allocated)
    if rows and diff != 0:
        rows[-1]["amount"] = round_money(rows[-1]["amount"] + diff)
        rows[-1]["remaining_amount"] = rows[-1]["amount"]
    return rows


async def upsert_payment_plan(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_installment_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    plan_id = payload.get("plan_id") or f"plan_{uuid4().hex[:12]}"
    row = await StudentPaymentPlan.find_one(
        Eq(StudentPaymentPlan.tenant_id, tenant_id),
        Eq(StudentPaymentPlan.plan_id, plan_id),
    )
    data = {
        "plan_code": payload["plan_code"],
        "plan_name": payload["plan_name"],
        "description": payload.get("description"),
        "academic_year_label": payload.get("academic_year_label"),
        "applicable_programmes": payload.get("applicable_programmes") or [],
        "applicable_fee_categories": payload.get("applicable_fee_categories") or [],
        "applicable_student_categories": payload.get("applicable_student_categories") or [],
        "number_of_installments": int(payload.get("number_of_installments") or len(payload.get("installment_definitions") or []) or 1),
        "installment_definitions": payload.get("installment_definitions") or [],
        "initial_payment_percent": float(payload.get("initial_payment_percent") or 0),
        "requires_approval": bool(payload.get("requires_approval", False)),
        "effective_from": payload.get("effective_from"),
        "effective_to": payload.get("effective_to"),
        "plan_status": PaymentPlanStatus(payload.get("plan_status", PaymentPlanStatus.DRAFT.value)),
        "updated_at": utcnow(),
    }
    if row:
        for k, v in data.items():
            setattr(row, k, v)
        await row.save()
    else:
        row = await StudentPaymentPlan(tenant_id=tenant_id, plan_id=plan_id, created_at=utcnow(), **data).insert()
    return {"plan_id": row.plan_id, "plan_code": row.plan_code, "plan_name": row.plan_name, "plan_status": row.plan_status.value}


async def list_payment_plans(scope: AccessScope, pagination: Pagination) -> Page[dict[str, Any]]:
    authorize_finance_installment_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    total = await StudentPaymentPlan.find(Eq(StudentPaymentPlan.tenant_id, tenant_id)).count()
    rows = (
        await StudentPaymentPlan.find(Eq(StudentPaymentPlan.tenant_id, tenant_id))
        .sort("-updated_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [{"plan_id": r.plan_id, "plan_code": r.plan_code, "plan_name": r.plan_name, "plan_status": r.plan_status.value} for r in rows]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def assign_payment_plan(scope: AccessScope, payload: dict[str, Any]) -> dict[str, Any]:
    authorize_finance_installment_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    student_user_id = to_object_id(payload["student_user_id"], "student_user_id")
    plan = await StudentPaymentPlan.find_one(
        Eq(StudentPaymentPlan.tenant_id, tenant_id),
        Eq(StudentPaymentPlan.plan_id, payload["plan_id"]),
    )
    plan_status = plan.plan_status.value if plan and hasattr(plan.plan_status, "value") else (plan.plan_status if plan else None)
    if plan is None or plan_status != PaymentPlanStatus.ACTIVE.value:
        raise AppError(code="NOT_FOUND", message="Active payment plan not found", status_code=404)

    invoice_id = payload.get("invoice_id")
    total = round_money(float(payload.get("total_obligation", 0)))
    if invoice_id:
        invoice = await StudentFeeInvoice.find_one(
            Eq(StudentFeeInvoice.tenant_id, tenant_id),
            Eq(StudentFeeInvoice.invoice_id, invoice_id),
        )
        if invoice is None or invoice.student_user_id != student_user_id:
            raise AppError(code="NOT_FOUND", message="Invoice not found for student", status_code=404)
        total = round_money(invoice.amount)

    assignment_id = f"asg_{uuid4().hex[:12]}"
    status = AssignmentStatus.PENDING_APPROVAL if plan.requires_approval or payload.get("special_arrangement") else AssignmentStatus.ACTIVE
    assignment = await StudentPaymentPlanAssignment(
        tenant_id=tenant_id,
        assignment_id=assignment_id,
        plan_id=plan.plan_id,
        student_user_id=student_user_id,
        invoice_id=invoice_id,
        demand_id=payload.get("demand_id"),
        total_obligation=total,
        academic_year_label=payload.get("academic_year_label"),
        semester_label=payload.get("semester_label"),
        status=status,
        effective_from=payload.get("effective_from"),
        special_arrangement=bool(payload.get("special_arrangement")),
        special_reason=payload.get("special_reason"),
    ).insert()

    start = payload.get("effective_from") or date.today()
    if isinstance(start, str):
        start = date.fromisoformat(start)
    installment_rows = _build_installments(total, plan.installment_definitions, start)
    schedule_id = f"sch_{uuid4().hex[:12]}"
    schedule = await StudentInstallmentSchedule(
        tenant_id=tenant_id,
        schedule_id=schedule_id,
        assignment_id=assignment_id,
        student_user_id=student_user_id,
        invoice_id=invoice_id,
        demand_id=payload.get("demand_id"),
        academic_year_label=payload.get("academic_year_label"),
        semester_label=payload.get("semester_label"),
        installments=installment_rows,
        active=status == AssignmentStatus.ACTIVE,
        published=status == AssignmentStatus.ACTIVE,
    ).insert()
    assignment.schedule_id = schedule_id
    await assignment.save()

    if status == AssignmentStatus.ACTIVE:
        await _publish_student_schedule(tenant_id, schedule)
        try:
            from app.modules.accounts_finance.finance_notify import enqueue_installment_plan_active

            await enqueue_installment_plan_active(tenant_id, student_user_id, schedule_id)
        except Exception:
            pass

    return {"assignment_id": assignment_id, "schedule_id": schedule_id, "status": assignment.status.value, "installments": installment_rows}


async def _publish_student_schedule(tenant_id, schedule: StudentInstallmentSchedule) -> None:
    legacy_id = schedule.schedule_id
    existing = await FeeInstallmentSchedule.find_one(
        Eq(FeeInstallmentSchedule.tenant_id, tenant_id),
        Eq(FeeInstallmentSchedule.schedule_id, legacy_id),
    )
    payload_installments = [
        {
            "installment_id": i["installment_id"],
            "due_date": i["due_date"],
            "amount": i["amount"],
            "status": i["status"],
        }
        for i in schedule.installments
    ]
    if existing:
        existing.installments = payload_installments
        existing.updated_at = utcnow()
        await existing.save()
    else:
        await FeeInstallmentSchedule(
            tenant_id=tenant_id,
            student_user_id=schedule.student_user_id,
            schedule_id=legacy_id,
            academic_year_label=schedule.academic_year_label or "",
            semester_label=schedule.semester_label or "",
            installments=payload_installments,
            published=True,
        ).insert()


async def approve_assignment(scope: AccessScope, assignment_id: str) -> dict[str, Any]:
    authorize_finance_installment_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    assignment = await StudentPaymentPlanAssignment.find_one(
        Eq(StudentPaymentPlanAssignment.tenant_id, tenant_id),
        Eq(StudentPaymentPlanAssignment.assignment_id, assignment_id),
    )
    if assignment is None:
        raise AppError(code="NOT_FOUND", message="Assignment not found", status_code=404)
    assignment.status = AssignmentStatus.ACTIVE
    assignment.approved_by = scope.user_id
    assignment.updated_at = utcnow()
    await assignment.save()
    schedule = await StudentInstallmentSchedule.find_one(
        Eq(StudentInstallmentSchedule.tenant_id, tenant_id),
        Eq(StudentInstallmentSchedule.schedule_id, assignment.schedule_id),
    )
    if schedule:
        schedule.active = True
        schedule.published = True
        schedule.updated_at = utcnow()
        await schedule.save()
        await _publish_student_schedule(tenant_id, schedule)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="installment_plan_approved",
        module="accounts_finance",
        resource_type="payment_plan_assignment",
        resource_id=assignment_id,
    )
    return {"assignment_id": assignment_id, "status": assignment.status.value}


async def apply_payment_to_installments(
    tenant_id,
    *,
    student_user_id,
    transaction_id: str,
    amount: float,
    demand_id: str | None = None,
) -> None:
    """Allocate verified payment across active installment schedules (FIFO)."""
    amount_left = round_money(amount)
    if amount_left <= 0:
        return
    query: dict[str, Any] = {"tenant_id": tenant_id, "student_user_id": student_user_id, "active": True}
    schedules = await StudentInstallmentSchedule.find(query).to_list()
    if demand_id:
        schedules = [s for s in schedules if not s.demand_id or s.demand_id == demand_id]
    for schedule in schedules:
        changed = False
        for inst in schedule.installments:
            if amount_left <= 0:
                break
            status = inst.get("status")
            if status in (InstallmentStatus.PAID.value, InstallmentStatus.CANCELLED.value, InstallmentStatus.WAIVED.value):
                continue
            remaining = round_money(inst.get("remaining_amount", inst.get("amount", 0)))
            if remaining <= 0:
                continue
            pay = min(remaining, amount_left)
            inst["paid_amount"] = round_money(inst.get("paid_amount", 0) + pay)
            inst["remaining_amount"] = round_money(remaining - pay)
            amount_left = round_money(amount_left - pay)
            if inst["remaining_amount"] <= 0:
                inst["status"] = InstallmentStatus.PAID.value
            else:
                inst["status"] = InstallmentStatus.PARTIALLY_PAID.value
            alloc_id = f"ipa_{uuid4().hex[:12]}"
            await StudentInstallmentPayment(
                tenant_id=tenant_id,
                allocation_id=alloc_id,
                schedule_id=schedule.schedule_id,
                installment_id=inst["installment_id"],
                transaction_id=transaction_id,
                amount=pay,
            ).insert()
            changed = True
        if changed:
            schedule.updated_at = utcnow()
            await schedule.save()
            if schedule.published:
                await _publish_student_schedule(tenant_id, schedule)
        if amount_left <= 0:
            break


async def mark_overdue_installments(tenant_id) -> int:
    today = date.today()
    count = 0
    schedules = await StudentInstallmentSchedule.find({"tenant_id": tenant_id, "active": True}).to_list()
    for schedule in schedules:
        changed = False
        for inst in schedule.installments:
            if inst.get("status") in (InstallmentStatus.PAID.value, InstallmentStatus.CANCELLED.value):
                continue
            due = date.fromisoformat(inst["due_date"])
            if due < today and float(inst.get("remaining_amount", 0)) > 0:
                if inst.get("status") != InstallmentStatus.OVERDUE.value:
                    inst["status"] = InstallmentStatus.OVERDUE.value
                    changed = True
                    count += 1
        if changed:
            schedule.updated_at = utcnow()
            await schedule.save()
    return count


async def submit_reschedule(scope: AccessScope, schedule_id: str, reason: str, proposed: list[dict]) -> dict[str, Any]:
    authorize_finance_installment_manage(scope)
    tenant_id = require_finance_tenant_scope(scope)
    schedule = await StudentInstallmentSchedule.find_one(
        Eq(StudentInstallmentSchedule.tenant_id, tenant_id),
        Eq(StudentInstallmentSchedule.schedule_id, schedule_id),
    )
    if schedule is None:
        raise AppError(code="NOT_FOUND", message="Schedule not found", status_code=404)
    request_id = f"rs_{uuid4().hex[:12]}"
    row = await StudentInstallmentRescheduleRequest(
        tenant_id=tenant_id,
        request_id=request_id,
        schedule_id=schedule_id,
        student_user_id=schedule.student_user_id,
        reason=reason,
        proposed_installments=proposed,
    ).insert()
    return {"request_id": row.request_id, "status": row.status}


async def approve_reschedule(scope: AccessScope, request_id: str) -> dict[str, Any]:
    authorize_finance_installment_approve(scope)
    tenant_id = require_finance_tenant_scope(scope)
    req = await StudentInstallmentRescheduleRequest.find_one(
        Eq(StudentInstallmentRescheduleRequest.tenant_id, tenant_id),
        Eq(StudentInstallmentRescheduleRequest.request_id, request_id),
    )
    if req is None:
        raise AppError(code="NOT_FOUND", message="Reschedule request not found", status_code=404)
    schedule = await StudentInstallmentSchedule.find_one(
        Eq(StudentInstallmentSchedule.tenant_id, tenant_id),
        Eq(StudentInstallmentSchedule.schedule_id, req.schedule_id),
    )
    if schedule is None:
        raise AppError(code="NOT_FOUND", message="Schedule not found", status_code=404)
    await StudentInstallmentHistory(
        tenant_id=tenant_id,
        history_id=f"ih_{uuid4().hex[:10]}",
        schedule_id=schedule.schedule_id,
        action="reschedule",
        actor_id=scope.user_id,
        previous_snapshot=list(schedule.installments),
        note=req.reason,
    ).insert()
    for old in schedule.installments:
        if old.get("status") not in (InstallmentStatus.PAID.value,):
            old["status"] = InstallmentStatus.RESCHEDULED.value
    schedule.installments = schedule.installments + req.proposed_installments
    schedule.version += 1
    schedule.updated_at = utcnow()
    await schedule.save()
    req.status = "approved"
    req.approved_by = scope.user_id
    await req.save()
    await _publish_student_schedule(tenant_id, schedule)
    return {"request_id": request_id, "schedule_id": schedule.schedule_id, "version": schedule.version}


async def installment_reports(scope: AccessScope) -> dict[str, Any]:
    authorize_finance_installment_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    schedules = await StudentInstallmentSchedule.find({"tenant_id": tenant_id, "active": True}).to_list()
    upcoming = overdue = partial = unpaid = 0
    for s in schedules:
        for inst in s.installments:
            st = inst.get("status")
            if st == InstallmentStatus.OVERDUE.value:
                overdue += 1
            elif st == InstallmentStatus.PARTIALLY_PAID.value:
                partial += 1
            elif st == InstallmentStatus.UNPAID.value:
                unpaid += 1
            due = date.fromisoformat(inst["due_date"])
            if st in (InstallmentStatus.UNPAID.value, InstallmentStatus.PARTIALLY_PAID.value) and due >= date.today():
                upcoming += 1
    assignments = await StudentPaymentPlanAssignment.find(
        Eq(StudentPaymentPlanAssignment.tenant_id, tenant_id),
        Eq(StudentPaymentPlanAssignment.status, AssignmentStatus.ACTIVE),
    ).count()
    return {
        "active_assignments": assignments,
        "unpaid_installments": unpaid,
        "partially_paid_installments": partial,
        "overdue_installments": overdue,
        "upcoming_due": upcoming,
    }