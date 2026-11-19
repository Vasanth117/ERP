"""Payroll period, run, calculation, approval and payment services."""

from calendar import monthrange
from decimal import Decimal
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.employee_sync import log_hr_activity
from app.modules.hr.enums import HrPayrollEmployeeStatus, HrPayrollRunStatus, HrStaffActivityType
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.payroll_calculation import calculate_employee_payroll
from app.modules.hr.statutory_calculation import resolve_statutory_rates_for_employee
from app.modules.hr.payroll_models import (
    HrEmployeePayrollRecord,
    HrPayrollAdjustment,
    HrPayrollApprovalHistory,
    HrPayrollPaymentRecord,
    HrPayrollPeriod,
    HrPayrollRun,
)
from app.modules.hr.payroll_schemas import (
    EmployeePayrollPreview,
    PayrollAdjustmentCreate,
    PayrollPeriodCreate,
    PayrollPeriodRead,
    PayrollPreview,
    PayrollReports,
    PayrollRunCreate,
    PayrollRunRead,
    PayrollTransition,
    PaymentConfirm,
)
from app.modules.hr.policy import (
    authorize_hr_payroll_approve,
    authorize_hr_payroll_pay,
    authorize_hr_payroll_prepare,
    authorize_hr_payroll_read,
    require_hr_tenant_scope,
)
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


_ALLOWED_TRANSITIONS: dict[HrPayrollRunStatus, set[HrPayrollRunStatus]] = {
    HrPayrollRunStatus.DRAFT: {HrPayrollRunStatus.CALCULATING, HrPayrollRunStatus.CANCELLED},
    HrPayrollRunStatus.CALCULATING: {HrPayrollRunStatus.VALIDATION_REQUIRED, HrPayrollRunStatus.READY_FOR_REVIEW, HrPayrollRunStatus.FAILED},
    HrPayrollRunStatus.VALIDATION_REQUIRED: {HrPayrollRunStatus.READY_FOR_REVIEW, HrPayrollRunStatus.CALCULATING},
    HrPayrollRunStatus.READY_FOR_REVIEW: {HrPayrollRunStatus.UNDER_REVIEW, HrPayrollRunStatus.CALCULATING},
    HrPayrollRunStatus.UNDER_REVIEW: {HrPayrollRunStatus.APPROVED, HrPayrollRunStatus.READY_FOR_REVIEW, HrPayrollRunStatus.CANCELLED},
    HrPayrollRunStatus.APPROVED: {HrPayrollRunStatus.PAYMENT_PROCESSING, HrPayrollRunStatus.REOPENED},
    HrPayrollRunStatus.PAYMENT_PROCESSING: {HrPayrollRunStatus.PAID, HrPayrollRunStatus.FAILED},
    HrPayrollRunStatus.REOPENED: {HrPayrollRunStatus.CALCULATING},
}


async def _log_transition(tenant_id: PydanticObjectId, run_id: PydanticObjectId, actor_id: PydanticObjectId, from_status: str, to_status: str, note: str | None) -> None:
    await HrPayrollApprovalHistory(
        tenant_id=tenant_id,
        payroll_run_id=run_id,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor_id,
        note=note,
    ).insert()


async def create_payroll_period(scope: AccessScope, payload: PayrollPeriodCreate) -> PayrollPeriodRead:
    authorize_hr_payroll_prepare(scope)
    tenant_id = require_hr_tenant_scope(scope)
    existing = await HrPayrollPeriod.find_one(
        Eq(HrPayrollPeriod.tenant_id, tenant_id),
        Eq(HrPayrollPeriod.period_year, payload.period_year),
        Eq(HrPayrollPeriod.period_month, payload.period_month),
    )
    if existing:
        raise AppError(code="CONFLICT", message="Payroll period already exists", status_code=409)
    code = f"PP-{payload.period_year}{payload.period_month:02d}"
    row = HrPayrollPeriod(
        tenant_id=tenant_id,
        period_code=code,
        period_year=payload.period_year,
        period_month=payload.period_month,
        start_date=payload.start_date,
        end_date=payload.end_date,
        attendance_cutoff=payload.attendance_cutoff,
        processing_date=payload.processing_date,
        expected_payment_date=payload.expected_payment_date,
        actor_id=scope.user_id,
    )
    await row.insert()
    return PayrollPeriodRead.from_document(row)


async def list_payroll_periods(scope: AccessScope) -> list[PayrollPeriodRead]:
    authorize_hr_payroll_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrPayrollPeriod.find(Eq(HrPayrollPeriod.tenant_id, tenant_id)).sort(-HrPayrollPeriod.period_year, -HrPayrollPeriod.period_month).to_list()
    return [PayrollPeriodRead.from_document(r) for r in rows]


async def create_payroll_run(scope: AccessScope, payload: PayrollRunCreate) -> PayrollRunRead:
    authorize_hr_payroll_prepare(scope)
    tenant_id = require_hr_tenant_scope(scope)
    period_id = to_object_id(payload.payroll_period_id, "payroll_period_id")
    period = await HrPayrollPeriod.get(period_id)
    if period is None or period.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payroll period not found", status_code=404)
    active = await HrPayrollRun.find_one(
        Eq(HrPayrollRun.tenant_id, tenant_id),
        Eq(HrPayrollRun.payroll_period_id, period.id),
    )
    revisions = await HrPayrollRun.find(Eq(HrPayrollRun.tenant_id, tenant_id), Eq(HrPayrollRun.payroll_period_id, period.id)).count()
    revision = revisions + 1
    blocking_statuses = {
        HrPayrollRunStatus.DRAFT,
        HrPayrollRunStatus.CALCULATING,
        HrPayrollRunStatus.VALIDATION_REQUIRED,
        HrPayrollRunStatus.READY_FOR_REVIEW,
        HrPayrollRunStatus.UNDER_REVIEW,
        HrPayrollRunStatus.APPROVED,
        HrPayrollRunStatus.PAYMENT_PROCESSING,
    }
    if active and active.status in blocking_statuses and not payload.reopen_reason:
        raise AppError(code="CONFLICT", message="Active payroll run exists for period", status_code=409)
    superseded = active.id if active and payload.reopen_reason else None
    code = f"RUN-{period.period_code}-R{revision}"
    run = HrPayrollRun(
        tenant_id=tenant_id,
        payroll_period_id=period.id,
        run_code=code,
        revision=revision,
        superseded_run_id=superseded,
        reopen_reason=payload.reopen_reason,
        status=HrPayrollRunStatus.DRAFT,
        actor_id=scope.user_id,
    )
    await run.insert()
    return PayrollRunRead.from_document(run)


async def calculate_payroll_run(scope: AccessScope, run_id: str) -> PayrollRunRead:
    authorize_hr_payroll_prepare(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(run_id, "run_id")
    run = await HrPayrollRun.get(rid)
    if run is None or run.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payroll run not found", status_code=404)
    if run.status not in {HrPayrollRunStatus.DRAFT, HrPayrollRunStatus.REOPENED, HrPayrollRunStatus.CALCULATING, HrPayrollRunStatus.VALIDATION_REQUIRED}:
        raise AppError(code="CONFLICT", message="Payroll run cannot be recalculated", status_code=409)

    prev_status = run.status.value
    run.status = HrPayrollRunStatus.CALCULATING
    await run.save()
    period = await HrPayrollPeriod.get(run.payroll_period_id)
    assert period is not None
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    adjustments = await HrPayrollAdjustment.find(
        Eq(HrPayrollAdjustment.tenant_id, tenant_id),
        Eq(HrPayrollAdjustment.payroll_period_id, period.id),
        Eq(HrPayrollAdjustment.approved, True),
    ).to_list()
    adj_by_user: dict[str, list[dict]] = {}
    for adj in adjustments:
        key = str(adj.employee_user_id)
        adj_by_user.setdefault(key, []).append({"component_code": adj.component_code, "amount": adj.amount})

    gross_total = Decimal("0")
    net_total = Decimal("0")
    employer_total = Decimal("0")
    exception_count = 0

    for emp in employees:
        profile = await HrEmployeeProfile.find_one(
            Eq(HrEmployeeProfile.tenant_id, tenant_id),
            Eq(HrEmployeeProfile.user_id, emp.user_id),
        )
        category = profile.employee_category if profile else None
        statutory, stat_warnings, statutory_meta = await resolve_statutory_rates_for_employee(
            tenant_id=tenant_id,
            as_of=period.end_date,
            employee_category=category,
            employee_user_id=emp.user_id,
        )
        calc = await calculate_employee_payroll(
            tenant_id=tenant_id,
            employee=emp,
            period_start=period.start_date,
            period_end=period.end_date,
            adjustments=adj_by_user.get(str(emp.user_id), []),
            statutory_rates=statutory,
            statutory_meta=statutory_meta,
        )
        if stat_warnings:
            calc.setdefault("warnings", []).extend(stat_warnings)
        record = await HrEmployeePayrollRecord.find_one(
            Eq(HrEmployeePayrollRecord.tenant_id, tenant_id),
            Eq(HrEmployeePayrollRecord.payroll_run_id, run.id),
            Eq(HrEmployeePayrollRecord.employee_user_id, emp.user_id),
        )
        if record is None:
            record = HrEmployeePayrollRecord(tenant_id=tenant_id, payroll_run_id=run.id, employee_user_id=emp.user_id)
        if not calc.get("eligible"):
            record.status = HrPayrollEmployeeStatus.EXCLUDED
            record.exclusion_reason = calc.get("exclusion_reason")
            record.exceptions = calc.get("exceptions", [])
        else:
            record.status = HrPayrollEmployeeStatus.EXCEPTION if calc.get("exceptions") else HrPayrollEmployeeStatus.CALCULATED
            record.salary_assignment_id = calc.get("salary_assignment_id")
            record.input_snapshot = calc.get("input_snapshot", {})
            record.earnings = calc.get("earnings", {})
            record.deductions = calc.get("deductions", {})
            record.employer_contributions = calc.get("employer_contributions", {})
            record.gross_salary = calc.get("gross_salary", "0")
            record.total_employee_deductions = calc.get("total_employee_deductions", "0")
            record.net_payable = calc.get("net_payable", "0")
            record.employer_cost = calc.get("employer_cost", "0")
            record.warnings = calc.get("warnings", [])
            record.exceptions = calc.get("exceptions", [])
            gross_total += Decimal(record.gross_salary)
            net_total += Decimal(record.net_payable)
            employer_total += Decimal(record.employer_cost)
            if record.exceptions:
                exception_count += 1
        record.updated_at = utcnow()
        if record.id:
            await record.save()
        else:
            await record.insert()

    run.summary = {
        "gross_total": str(gross_total),
        "net_total": str(net_total),
        "employer_cost_total": str(employer_total),
    }
    run.exception_count = exception_count
    run.status = HrPayrollRunStatus.VALIDATION_REQUIRED if exception_count else HrPayrollRunStatus.READY_FOR_REVIEW
    run.calculation_version = f"v{run.revision}-{uuid4().hex[:6]}"
    run.updated_at = utcnow()
    await run.save()
    await _log_transition(tenant_id, run.id, scope.user_id, prev_status, run.status.value, "Calculated")
    return PayrollRunRead.from_document(run)


async def get_payroll_preview(scope: AccessScope, run_id: str) -> PayrollPreview:
    authorize_hr_payroll_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(run_id, "run_id")
    run = await HrPayrollRun.get(rid)
    if run is None or run.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payroll run not found", status_code=404)
    rows = await HrEmployeePayrollRecord.find(Eq(HrEmployeePayrollRecord.tenant_id, tenant_id), Eq(HrEmployeePayrollRecord.payroll_run_id, run.id)).to_list()
    employees = [
        EmployeePayrollPreview(
            employee_user_id=str(r.employee_user_id),
            status=r.status.value,
            gross_salary=r.gross_salary,
            net_payable=r.net_payable,
            warnings=r.warnings,
            exceptions=r.exceptions,
            input_snapshot=r.input_snapshot,
        )
        for r in rows
    ]
    return PayrollPreview(run_id=str(run.id), status=run.status, employees=employees, summary=run.summary, exception_count=run.exception_count)


async def transition_payroll_run(scope: AccessScope, run_id: str, payload: PayrollTransition) -> PayrollRunRead:
    if payload.target_status == HrPayrollRunStatus.APPROVED:
        authorize_hr_payroll_approve(scope)
    elif payload.target_status == HrPayrollRunStatus.PAYMENT_PROCESSING:
        authorize_hr_payroll_pay(scope)
    else:
        authorize_hr_payroll_prepare(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(run_id, "run_id")
    run = await HrPayrollRun.get(rid)
    if run is None or run.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payroll run not found", status_code=404)
    allowed = _ALLOWED_TRANSITIONS.get(run.status, set())
    if payload.target_status not in allowed:
        raise AppError(code="CONFLICT", message=f"Cannot transition {run.status.value} -> {payload.target_status.value}", status_code=409)
    prev = run.status.value
    run.status = payload.target_status
    if payload.target_status == HrPayrollRunStatus.APPROVED:
        run.approved_by = scope.user_id
        run.approved_at = utcnow()
    run.updated_at = utcnow()
    await run.save()
    await _log_transition(tenant_id, run.id, scope.user_id, prev, run.status.value, payload.note)
    return PayrollRunRead.from_document(run)


async def submit_payroll_for_payment(scope: AccessScope, run_id: str) -> dict:
    authorize_hr_payroll_pay(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(run_id, "run_id")
    run = await HrPayrollRun.get(rid)
    if run is None or run.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payroll run not found", status_code=404)
    if run.status != HrPayrollRunStatus.APPROVED:
        raise AppError(code="CONFLICT", message="Payroll must be approved before payment", status_code=409)
    rows = await HrEmployeePayrollRecord.find(
        Eq(HrEmployeePayrollRecord.tenant_id, tenant_id),
        Eq(HrEmployeePayrollRecord.payroll_run_id, run.id),
        Eq(HrEmployeePayrollRecord.status, HrPayrollEmployeeStatus.CALCULATED),
    ).to_list()
    submitted = 0
    for row in rows:
        idem = f"payroll:{run.id}:{row.employee_user_id}"
        if await HrPayrollPaymentRecord.find_one(Eq(HrPayrollPaymentRecord.tenant_id, tenant_id), Eq(HrPayrollPaymentRecord.idempotency_key, idem)):
            continue
        await HrPayrollPaymentRecord(
            tenant_id=tenant_id,
            payroll_run_id=run.id,
            employee_user_id=row.employee_user_id,
            employee_payroll_record_id=row.id,
            amount=row.net_payable,
            idempotency_key=idem,
            status="submitted",
        ).insert()
        submitted += 1
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type="finance.payroll.payment_batch_requested",
        aggregate_type="hr_payroll_run",
        aggregate_id=str(run.id),
        payload={"run_code": run.run_code, "payment_count": submitted},
        idempotency_key=f"finance:payroll:{run.id}",
        status=OutboxEventStatus.PENDING,
    ).insert()
    run.status = HrPayrollRunStatus.PAYMENT_PROCESSING
    run.payment_submitted_at = utcnow()
    run.updated_at = utcnow()
    await run.save()
    return {"submitted_payments": submitted}


async def confirm_employee_payment(scope: AccessScope, run_id: str, payload: PaymentConfirm) -> dict:
    authorize_hr_payroll_pay(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(run_id, "run_id")
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    pay = await HrPayrollPaymentRecord.find_one(
        Eq(HrPayrollPaymentRecord.tenant_id, tenant_id),
        Eq(HrPayrollPaymentRecord.payroll_run_id, rid),
        Eq(HrPayrollPaymentRecord.employee_user_id, uid),
    )
    if pay is None:
        raise AppError(code="NOT_FOUND", message="Payment record not found", status_code=404)
    if pay.status == "reconciled":
        raise AppError(code="CONFLICT", message="Payment already reconciled", status_code=409)
    pay.payment_reference = payload.payment_reference
    pay.finance_batch_id = payload.finance_batch_id
    pay.status = "reconciled"
    pay.reconciled_at = utcnow()
    pay.updated_at = utcnow()
    await pay.save()
    emp_record = await HrEmployeePayrollRecord.get(pay.employee_payroll_record_id)
    if emp_record:
        emp_record.payment_status = "paid"
        emp_record.payment_reference = payload.payment_reference
        emp_record.paid_at = utcnow()
        emp_record.status = HrPayrollEmployeeStatus.PAID
        await emp_record.save()
    all_payments = await HrPayrollPaymentRecord.find(Eq(HrPayrollPaymentRecord.tenant_id, tenant_id), Eq(HrPayrollPaymentRecord.payroll_run_id, rid)).to_list()
    if all(p.status == "reconciled" for p in all_payments):
        run = await HrPayrollRun.get(rid)
        if run:
            run.status = HrPayrollRunStatus.PAID
            run.updated_at = utcnow()
            await run.save()
    return {"payment_reference": payload.payment_reference, "status": "reconciled"}


async def create_payroll_adjustment(scope: AccessScope, payload: PayrollAdjustmentCreate) -> dict:
    authorize_hr_payroll_prepare(scope)
    tenant_id = require_hr_tenant_scope(scope)
    row = HrPayrollAdjustment(
        tenant_id=tenant_id,
        payroll_period_id=to_object_id(payload.payroll_period_id, "payroll_period_id"),
        employee_user_id=to_object_id(payload.employee_user_id, "employee_user_id"),
        adjustment_code=f"ADJ-{uuid4().hex[:10].upper()}",
        component_code=payload.component_code,
        amount=payload.amount,
        reason=payload.reason,
        approved=True,
        actor_id=scope.user_id,
    )
    await row.insert()
    return {"adjustment_id": str(row.id)}


async def payroll_reports(scope: AccessScope, run_id: str) -> PayrollReports:
    authorize_hr_payroll_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(run_id, "run_id")
    rows = await HrEmployeePayrollRecord.find(Eq(HrEmployeePayrollRecord.tenant_id, tenant_id), Eq(HrEmployeePayrollRecord.payroll_run_id, rid)).to_list()
    dept_totals: dict[str, str] = {}
    failed = 0
    gross = Decimal("0")
    net = Decimal("0")
    employer = Decimal("0")
    exceptions = 0
    for row in rows:
        gross += Decimal(row.gross_salary or "0")
        net += Decimal(row.net_payable or "0")
        employer += Decimal(row.employer_cost or "0")
        if row.status == HrPayrollEmployeeStatus.PAYMENT_FAILED:
            failed += 1
        if row.exceptions:
            exceptions += 1
        employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.user_id, row.employee_user_id))
        dept = str(employee.department_id) if employee and employee.department_id else "unassigned"
        dept_totals[dept] = str(Decimal(dept_totals.get(dept, "0")) + Decimal(row.net_payable or "0"))
    return PayrollReports(
        gross_total=str(gross),
        net_total=str(net),
        employer_cost_total=str(employer),
        department_totals=dept_totals,
        failed_payments=failed,
        exception_count=exceptions,
    )