"""Payslip generation, publication and revision."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.enums import HrPayrollRunStatus, HrPayslipStatus
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.models import PayslipReference
from app.modules.hr.payroll_models import HrEmployeePayrollRecord, HrEmployeePayslip, HrEmployeePayslipVersion, HrPayrollPeriod, HrPayrollRun
from app.modules.hr.payroll_schemas import PayslipGenerateRequest, PayslipRead, PayslipRevise
from app.modules.hr.policy import authorize_hr_payslip_manage, authorize_hr_payslip_read, require_hr_tenant_scope


def _period_label(period: HrPayrollPeriod) -> str:
    return f"{period.period_year}-{period.period_month:02d}"


async def generate_payslips(scope: AccessScope, payload: PayslipGenerateRequest) -> dict:
    authorize_hr_payslip_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    run_id = to_object_id(payload.payroll_run_id, "payroll_run_id")
    run = await HrPayrollRun.get(run_id)
    if run is None or run.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payroll run not found", status_code=404)
    if run.status not in {HrPayrollRunStatus.APPROVED, HrPayrollRunStatus.PAYMENT_PROCESSING, HrPayrollRunStatus.PAID}:
        raise AppError(code="CONFLICT", message="Payslips require approved payroll", status_code=409)
    period = await HrPayrollPeriod.get(run.payroll_period_id)
    if period is None:
        raise AppError(code="NOT_FOUND", message="Payroll period not found", status_code=404)
    label = _period_label(period)
    filters = [Eq(HrEmployeePayrollRecord.tenant_id, tenant_id), Eq(HrEmployeePayrollRecord.payroll_run_id, run.id)]
    records = await HrEmployeePayrollRecord.find(*filters).to_list()
    if payload.employee_user_ids:
        allowed = {to_object_id(x, "employee_user_id") for x in payload.employee_user_ids}
        records = [r for r in records if r.employee_user_id in allowed]
    generated = 0
    for rec in records:
        if rec.exclusion_reason:
            continue
        employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, rec.employee_user_id))
        code = f"PS-{label}-{uuid4().hex[:8].upper()}"
        storage_key = f"tenant/{tenant_id}/payslips/{code}.json"
        payload_doc = {
            "employee_code": employee.employee_id if employee else None,
            "employee_name": (employee.confidential_hr or {}).get("full_name") if employee else None,
            "designation": employee.designation if employee else None,
            "period_label": label,
            "earnings": rec.earnings,
            "deductions": rec.deductions,
            "employer_contributions": rec.employer_contributions,
            "gross_salary": rec.gross_salary,
            "net_payable": rec.net_payable,
            "payment_status": rec.payment_status,
            "calculation_version": run.calculation_version,
        }
        existing = await HrEmployeePayslip.find_one(
            Eq(HrEmployeePayslip.tenant_id, tenant_id),
            Eq(HrEmployeePayslip.employee_user_id, rec.employee_user_id),
            Eq(HrEmployeePayslip.period_label, label),
            Eq(HrEmployeePayslip.status, HrPayslipStatus.PUBLISHED),
        )
        if existing:
            continue
        slip = HrEmployeePayslip(
            tenant_id=tenant_id,
            employee_user_id=rec.employee_user_id,
            payroll_run_id=run.id,
            employee_payroll_record_id=rec.id,
            period_label=label,
            payslip_code=code,
            status=HrPayslipStatus.GENERATED,
            storage_key=storage_key,
            document_payload=payload_doc,
            actor_id=scope.user_id,
        )
        await slip.insert()
        await HrEmployeePayslipVersion(
            tenant_id=tenant_id,
            payslip_id=slip.id,
            version=1,
            document_payload=payload_doc,
            storage_key=storage_key,
            actor_id=scope.user_id,
        ).insert()
        generated += 1
    return {"generated": generated}


async def publish_payslip(scope: AccessScope, payslip_id: str) -> PayslipRead:
    authorize_hr_payslip_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    slip = await HrEmployeePayslip.get(to_object_id(payslip_id, "payslip_id"))
    if slip is None or slip.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payslip not found", status_code=404)
    if slip.status == HrPayslipStatus.PUBLISHED:
        return PayslipRead.from_record(str(slip.employee_user_id), slip.period_label, slip)
    slip.status = HrPayslipStatus.PUBLISHED
    slip.published_at = utcnow()
    slip.updated_at = utcnow()
    await slip.save()
    ref = await PayslipReference.find_one(
        Eq(PayslipReference.tenant_id, tenant_id),
        Eq(PayslipReference.employee_user_id, slip.employee_user_id),
        Eq(PayslipReference.period_label, slip.period_label),
    )
    if ref is None:
        await PayslipReference(
            tenant_id=tenant_id,
            employee_user_id=slip.employee_user_id,
            period_label=slip.period_label,
            storage_key=slip.storage_key or f"payslip/{slip.id}",
            payroll_provider="hr_phase6",
        ).insert()
    await enqueue_hr_notification(
        tenant_id,
        event_type="hr.payslip.published",
        aggregate_type="employee_payslip",
        aggregate_id=str(slip.id),
        title="Salary slip available",
        body=f"Your payslip for {slip.period_label} is now available",
        recipient_user_id=slip.employee_user_id,
        dedupe_key=f"hr:payslip_pub:{slip.id}",
    )
    return PayslipRead.from_record(str(slip.employee_user_id), slip.period_label, slip)


async def revise_payslip(scope: AccessScope, payslip_id: str, payload: PayslipRevise) -> PayslipRead:
    authorize_hr_payslip_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    slip = await HrEmployeePayslip.get(to_object_id(payslip_id, "payslip_id"))
    if slip is None or slip.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payslip not found", status_code=404)
    slip.status = HrPayslipStatus.SUPERSEDED
    slip.updated_at = utcnow()
    await slip.save()
    rec = await HrEmployeePayrollRecord.get(slip.employee_payroll_record_id)
    new_version = slip.current_version + 1
    new_code = f"{slip.payslip_code}-R{new_version}"
    document = dict(slip.document_payload)
    if rec:
        document.update({"net_payable": rec.net_payable, "gross_salary": rec.gross_salary, "revised": True})
    revised = HrEmployeePayslip(
        tenant_id=tenant_id,
        employee_user_id=slip.employee_user_id,
        payroll_run_id=slip.payroll_run_id,
        employee_payroll_record_id=slip.employee_payroll_record_id,
        period_label=slip.period_label,
        payslip_code=new_code,
        status=HrPayslipStatus.GENERATED,
        storage_key=slip.storage_key,
        document_payload=document,
        current_version=new_version,
        actor_id=scope.user_id,
    )
    await revised.insert()
    await HrEmployeePayslipVersion(
        tenant_id=tenant_id,
        payslip_id=revised.id,
        version=new_version,
        revision_reason=payload.revision_reason,
        document_payload=document,
        storage_key=slip.storage_key,
        actor_id=scope.user_id,
    ).insert()
    return PayslipRead.from_record(str(revised.employee_user_id), revised.period_label, revised)


async def publish_payslips_for_run(scope: AccessScope, payroll_run_id: str) -> dict:
    authorize_hr_payslip_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    run_id = to_object_id(payroll_run_id, "payroll_run_id")
    run = await HrPayrollRun.get(run_id)
    if run is None or run.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Payroll run not found", status_code=404)
    rows = await HrEmployeePayslip.find(
        Eq(HrEmployeePayslip.tenant_id, tenant_id),
        Eq(HrEmployeePayslip.payroll_run_id, run.id),
        Eq(HrEmployeePayslip.status, HrPayslipStatus.GENERATED),
    ).to_list()
    published = 0
    for slip in rows:
        await publish_payslip(scope, str(slip.id))
        published += 1
    return {"published": published, "payroll_run_id": str(run.id)}


async def list_payslips(scope: AccessScope, period_label: str | None = None, employee_user_id: str | None = None) -> list[PayslipRead]:
    authorize_hr_payslip_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(HrEmployeePayslip.tenant_id, tenant_id)]
    if period_label:
        filters.append(Eq(HrEmployeePayslip.period_label, period_label))
    if employee_user_id:
        filters.append(Eq(HrEmployeePayslip.employee_user_id, to_object_id(employee_user_id, "employee_user_id")))
    rows = await HrEmployeePayslip.find(*filters).sort(-HrEmployeePayslip.created_at).to_list()
    return [PayslipRead.from_record(str(r.employee_user_id), r.period_label, r) for r in rows]


async def get_payslip_for_employee_self(scope: AccessScope, payslip_id: str, viewer_user_id: PydanticObjectId) -> dict:
    from app.authorization.permissions import Permission
    from app.modules.hr.policy import authorize_employee_self_service, authorize_hr_payslip_read, require_employee_tenant_scope

    if Permission.HR_PAYSLIP_READ in scope.effective_permissions:
        authorize_hr_payslip_read(scope)
        tenant_id = require_hr_tenant_scope(scope)
    else:
        authorize_employee_self_service(scope)
        tenant_id = require_employee_tenant_scope(scope)
    slip = await HrEmployeePayslip.get(to_object_id(payslip_id, "payslip_id"))
    if slip is None or slip.tenant_id != tenant_id or slip.employee_user_id != viewer_user_id:
        raise AppError(code="FORBIDDEN", message="Payslip access denied", status_code=403)
    if slip.status != HrPayslipStatus.PUBLISHED:
        raise AppError(code="NOT_FOUND", message="Payslip not published", status_code=404)
    return slip.document_payload