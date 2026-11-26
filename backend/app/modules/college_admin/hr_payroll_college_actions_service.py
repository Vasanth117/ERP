"""College admin payroll processing actions (wraps HR payroll engine)."""

from __future__ import annotations

import calendar
from datetime import date

from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.hr.enums import HrPayrollRunStatus
from app.modules.hr.payroll_models import HrPayrollPeriod, HrPayrollRun
from app.modules.hr.payroll_schemas import PayrollPeriodCreate, PayrollRunCreate, PayrollTransition, PayslipGenerateRequest
from app.modules.hr.payroll_service import (
    calculate_payroll_run,
    create_payroll_period,
    create_payroll_run,
    submit_payroll_for_payment,
    transition_payroll_run,
)
from app.modules.hr.payslip_service import generate_payslips, publish_payslips_for_run


async def _ensure_period(scope: AccessScope, anchor: date) -> HrPayrollPeriod:
    tenant_id = require_college_tenant_scope(scope)
    period = await HrPayrollPeriod.find_one(
        Eq(HrPayrollPeriod.tenant_id, tenant_id),
        Eq(HrPayrollPeriod.period_year, anchor.year),
        Eq(HrPayrollPeriod.period_month, anchor.month),
    )
    if period:
        return period
    last_day = calendar.monthrange(anchor.year, anchor.month)[1]
    payload = PayrollPeriodCreate(
        period_year=anchor.year,
        period_month=anchor.month,
        start_date=date(anchor.year, anchor.month, 1),
        end_date=date(anchor.year, anchor.month, last_day),
        attendance_cutoff=date(anchor.year, anchor.month, min(28, last_day)),
    )
    created = await create_payroll_period(scope, payload)
    row = await HrPayrollPeriod.get(to_object_id(created.id, "period_id"))
    assert row is not None
    return row


async def _ensure_run(scope: AccessScope, period: HrPayrollPeriod) -> HrPayrollRun:
    tenant_id = require_college_tenant_scope(scope)
    runs = await HrPayrollRun.find(
        Eq(HrPayrollRun.tenant_id, tenant_id),
        Eq(HrPayrollRun.payroll_period_id, period.id),
    ).sort("-revision").to_list()
    if runs:
        return runs[0]
    created = await create_payroll_run(scope, PayrollRunCreate(payroll_period_id=str(period.id)))
    row = await HrPayrollRun.get(to_object_id(created.id, "run_id"))
    assert row is not None
    return row


async def college_admin_validate_payroll(scope: AccessScope, *, payroll_run_id: str | None = None) -> dict:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    anchor = utcnow().date()
    period = await _ensure_period(scope, anchor)
    run = await HrPayrollRun.get(to_object_id(payroll_run_id, "payroll_run_id")) if payroll_run_id else await _ensure_run(scope, period)
    if run is None or run.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payroll run not found", status_code=404)

    if run.status == HrPayrollRunStatus.VALIDATION_REQUIRED:
        if run.exception_count:
            raise AppError(code="CONFLICT", message="Resolve payroll exceptions before validation", status_code=409)
        await transition_payroll_run(scope, str(run.id), PayrollTransition(target_status=HrPayrollRunStatus.READY_FOR_REVIEW))
    elif run.status == HrPayrollRunStatus.READY_FOR_REVIEW:
        await transition_payroll_run(scope, str(run.id), PayrollTransition(target_status=HrPayrollRunStatus.UNDER_REVIEW))
    elif run.status == HrPayrollRunStatus.UNDER_REVIEW:
        await transition_payroll_run(scope, str(run.id), PayrollTransition(target_status=HrPayrollRunStatus.APPROVED))
    else:
        raise AppError(code="CONFLICT", message="Payroll run is not ready for validation", status_code=409)

    refreshed = await HrPayrollRun.get(run.id)
    return {"payroll_run_id": str(run.id), "status": refreshed.status.value if refreshed else run.status.value}


async def college_admin_process_payroll(scope: AccessScope, *, payroll_run_id: str | None = None) -> dict:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    anchor = utcnow().date()
    period = await _ensure_period(scope, anchor)
    run = await HrPayrollRun.get(to_object_id(payroll_run_id, "payroll_run_id")) if payroll_run_id else await _ensure_run(scope, period)
    if run is None or run.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payroll run not found", status_code=404)

    if run.status in {HrPayrollRunStatus.DRAFT, HrPayrollRunStatus.REOPENED}:
        await calculate_payroll_run(scope, str(run.id))

    run = await HrPayrollRun.get(run.id)
    if run is None:
        raise AppError(code="NOT_FOUND", message="Payroll run not found", status_code=404)

    for _ in range(4):
        if run.status == HrPayrollRunStatus.VALIDATION_REQUIRED:
            if run.exception_count:
                raise AppError(code="CONFLICT", message="Resolve exceptions before processing payroll", status_code=409)
            await transition_payroll_run(scope, str(run.id), PayrollTransition(target_status=HrPayrollRunStatus.READY_FOR_REVIEW))
        elif run.status == HrPayrollRunStatus.READY_FOR_REVIEW:
            await transition_payroll_run(scope, str(run.id), PayrollTransition(target_status=HrPayrollRunStatus.UNDER_REVIEW))
        elif run.status == HrPayrollRunStatus.UNDER_REVIEW:
            await transition_payroll_run(scope, str(run.id), PayrollTransition(target_status=HrPayrollRunStatus.APPROVED))
            break
        else:
            break
        run = await HrPayrollRun.get(run.id)
        if run is None:
            break

    run = await HrPayrollRun.get(run.id)
    if run and run.status == HrPayrollRunStatus.APPROVED:
        result = await submit_payroll_for_payment(scope, str(run.id))
        refreshed = await HrPayrollRun.get(run.id)
        return {"payroll_run_id": str(run.id), "status": refreshed.status.value if refreshed else run.status.value, **result}

    if run is None:
        raise AppError(code="NOT_FOUND", message="Payroll run not found", status_code=404)
    return {"payroll_run_id": str(run.id), "status": run.status.value}


async def college_admin_generate_salary_slips(scope: AccessScope, *, payroll_run_id: str | None = None) -> dict:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    if not payroll_run_id:
        raise AppError(code="VALIDATION_ERROR", message="payroll_run_id is required", status_code=422)
    return await generate_payslips(scope, PayslipGenerateRequest(payroll_run_id=payroll_run_id))


async def college_admin_publish_salary_slips(scope: AccessScope, *, payroll_run_id: str | None = None) -> dict:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    if not payroll_run_id:
        raise AppError(code="VALIDATION_ERROR", message="payroll_run_id is required", status_code=422)
    return await publish_payslips_for_run(scope, payroll_run_id)