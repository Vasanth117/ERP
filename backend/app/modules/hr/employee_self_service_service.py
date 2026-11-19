"""Employee HR self-service — own data only."""

from datetime import date

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.employee_profile_schemas import ProfileCorrectionSubmit
from app.modules.hr.employee_profile_service import submit_profile_correction
from app.modules.hr.enums import (
    EmployeeAttendanceCorrectionStatus,
    HrOnboardingProcessStatus,
    HrOnboardingTaskStatus,
    HrPayslipStatus,
    HrSalaryAssignmentStatus,
    HrSelfServiceRequestStatus,
    LeaveRequestStatus,
)
from app.modules.hr.leave_balance_service import get_or_create_balance, post_balance_transaction
from app.modules.hr.leave_models import HrLeaveBalance, HrLeaveTypeConfig
from app.modules.hr.leave_schemas import LeaveRequestRead
from app.modules.hr.leave_working_days import count_working_leave_days
from app.modules.hr.models import LeaveRequest
from app.modules.hr.onboarding_models import HrOnboardingProcess, HrOnboardingTask
from app.modules.hr.operational_models import EmployeeAttendanceCorrection
from app.modules.hr.payroll_calculation import gather_attendance_inputs, gather_leave_inputs
from app.modules.hr.payroll_models import HrEmployeePayslip, HrEmployeePayrollDocument
from app.modules.hr.payslip_service import get_payslip_for_employee_self
from app.modules.hr.policy import authorize_employee_self_service, require_employee_tenant_scope
from app.modules.hr.salary_structure_models import HrEmployeeSalaryAssignment, HrSalaryTemplate
from app.modules.hr.statutory_tax_models import EmployeeSelfServiceRequest, EmployeeSelfServiceRequestHistory, EmployeeTaxDeclaration
from app.modules.hr.statutory_tax_schemas import TaxDeclarationRead, TaxDeclarationUpsert
from app.modules.hr.statutory_tax_service import save_tax_declaration_draft, submit_tax_declaration
from app.modules.hr.attendance_schedule_models import HrEmployeeAttendanceMonthlySummary, HrEmployeeAttendanceRecord
from app.modules.hr.attendance_schedule_schemas import AttendanceCorrectionCreate
from app.modules.hr.document_models import HrEmployeeDocument
from app.modules.hr.document_schemas import EmployeeDocumentRead
from app.modules.hr.employee_self_service_schemas import (
    SelfServiceBenefitsStub,
    SelfServiceLeaveApply,
    SelfServiceNotificationRead,
    SelfServiceProfileRead,
    SelfServiceRequestCreate,
    SelfServiceRequestRead,
    SelfServiceSalaryRead,
)
from app.modules.messaging.outbox_models import DomainOutboxEvent


def _assert_self(scope: AccessScope, employee_user_id: PydanticObjectId) -> None:
    authorize_employee_self_service(scope)
    if scope.user_id != employee_user_id:
        raise AppError(code="FORBIDDEN", message="Employee self-service access denied", status_code=403)


async def _employee_record(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> EmployeeRecord:
    emp = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, user_id))
    if emp is None:
        raise AppError(code="NOT_FOUND", message="Employee record not found", status_code=404)
    return emp


async def get_my_profile(scope: AccessScope, user: User) -> SelfServiceProfileRead:
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, user.id))
    emp = await _employee_record(tenant_id, user.id)
    join = (emp.confidential_hr or {}).get("joining_date")
    name = None
    if profile:
        name = f"{profile.first_name} {profile.last_name}".strip()
    return SelfServiceProfileRead(
        employee_user_id=str(user.id),
        employee_code=profile.employee_code if profile else emp.employee_id,
        full_name=name or (emp.confidential_hr or {}).get("full_name"),
        official_email=profile.official_email if profile else None,
        personal_email=str(profile.personal_email) if profile and profile.personal_email else None,
        mobile_number=profile.mobile_number if profile else None,
        department_id=str(emp.department_id) if emp.department_id else None,
        designation=emp.designation,
        employment_status=emp.employment_status.value,
        joining_date=join,
        reporting_manager_user_id=str(profile.reporting_manager_user_id) if profile and profile.reporting_manager_user_id else None,
        current_address=profile.current_address.model_dump() if profile and profile.current_address else None,
        permanent_address=profile.permanent_address.model_dump() if profile and profile.permanent_address else None,
        emergency_contact=profile.emergency_contact.model_dump() if profile and profile.emergency_contact else None,
    )


async def request_profile_correction(scope: AccessScope, user: User, payload: ProfileCorrectionSubmit):
    _assert_self(scope, user.id)
    return await submit_profile_correction(scope, user, payload)


async def my_documents(scope: AccessScope, user: User):
    _assert_self(scope, user.id)
    tenant_id = require_employee_tenant_scope(scope)
    rows = await HrEmployeeDocument.find(
        Eq(HrEmployeeDocument.tenant_id, tenant_id),
        Eq(HrEmployeeDocument.employee_user_id, user.id),
    ).sort(-HrEmployeeDocument.created_at).to_list()
    return {"documents": [EmployeeDocumentRead.from_doc(r) for r in rows]}


async def my_attendance_day(scope: AccessScope, user: User, start: date, end: date):
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    records = await HrEmployeeAttendanceRecord.find(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceRecord.employee_user_id, user.id),
        GTE(HrEmployeeAttendanceRecord.attendance_date, start),
        LTE(HrEmployeeAttendanceRecord.attendance_date, end),
    ).sort(HrEmployeeAttendanceRecord.attendance_date).to_list()
    summary = await gather_attendance_inputs(tenant_id, user.id, start, end)
    return {"records": [{"date": r.attendance_date.isoformat(), "status": r.status.value, "overtime_minutes": r.overtime_minutes} for r in records], "summary": summary}


async def my_attendance_monthly(scope: AccessScope, user: User, year: int, month: int):
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    row = await HrEmployeeAttendanceMonthlySummary.find_one(
        Eq(HrEmployeeAttendanceMonthlySummary.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceMonthlySummary.employee_user_id, user.id),
        Eq(HrEmployeeAttendanceMonthlySummary.period_year, year),
        Eq(HrEmployeeAttendanceMonthlySummary.period_month, month),
    )
    return row.model_dump() if row else None


async def my_leave_balances(scope: AccessScope, user: User, year: int | None = None):
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    period_year = year or date.today().year
    balances = await HrLeaveBalance.find(
        Eq(HrLeaveBalance.tenant_id, tenant_id),
        Eq(HrLeaveBalance.employee_user_id, user.id),
        Eq(HrLeaveBalance.period_year, period_year),
    ).to_list()
    types = await HrLeaveTypeConfig.find(Eq(HrLeaveTypeConfig.tenant_id, tenant_id), Eq(HrLeaveTypeConfig.is_active, True)).to_list()
    return {"balances": balances, "leave_types": types}


async def my_apply_leave(scope: AccessScope, user: User, payload: SelfServiceLeaveApply) -> LeaveRequestRead:
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    if payload.end_date < payload.start_date:
        raise AppError(code="VALIDATION_ERROR", message="Leave end date must be on or after start date", status_code=422)
    working_days = await count_working_leave_days(tenant_id, payload.start_date, payload.end_date, payload.day_portion)
    period_year = payload.start_date.year
    type_cfg = await HrLeaveTypeConfig.find_one(
        Eq(HrLeaveTypeConfig.tenant_id, tenant_id),
        Eq(HrLeaveTypeConfig.leave_type_code, payload.leave_type),
    )
    entitlement = float(type_cfg.rules.get("annual_entitlement", 12.0)) if type_cfg else 12.0
    bal = await get_or_create_balance(tenant_id, user.id, payload.leave_type, period_year, annual_entitlement=entitlement)
    if bal.available < working_days:
        raise AppError(code="VALIDATION_ERROR", message="Insufficient leave balance", status_code=422)
    req = LeaveRequest(
        tenant_id=tenant_id,
        employee_user_id=user.id,
        leave_type=payload.leave_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        day_portion=payload.day_portion,
        working_days=working_days,
        reason=payload.reason,
        document_refs=payload.document_refs,
        contact_during_leave=payload.contact_during_leave,
        alternate_arrangement=payload.alternate_arrangement,
        status=LeaveRequestStatus.PENDING_MANAGER,
    )
    await req.insert()
    await post_balance_transaction(
        tenant_id=tenant_id,
        employee_user_id=user.id,
        leave_type=payload.leave_type,
        period_year=period_year,
        transaction_type="pending_reserve",
        amount_days=-working_days,
        reason=f"Reserved for leave {req.id}",
        actor_id=user.id,
        reference_type="leave_request",
        reference_id=str(req.id),
    )
    return LeaveRequestRead.from_document(req)


async def my_leave_requests(scope: AccessScope, user: User):
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    rows = await LeaveRequest.find(
        Eq(LeaveRequest.tenant_id, tenant_id),
        Eq(LeaveRequest.employee_user_id, user.id),
    ).sort(-LeaveRequest.created_at).to_list()
    return [LeaveRequestRead.from_document(r) for r in rows]


async def my_salary(scope: AccessScope, user: User) -> SelfServiceSalaryRead:
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    assignment = await HrEmployeeSalaryAssignment.find_one(
        Eq(HrEmployeeSalaryAssignment.tenant_id, tenant_id),
        Eq(HrEmployeeSalaryAssignment.employee_user_id, user.id),
        Eq(HrEmployeeSalaryAssignment.status, HrSalaryAssignmentStatus.ACTIVE),
    )
    if assignment is None:
        return SelfServiceSalaryRead()
    template = await HrSalaryTemplate.get(assignment.template_id)
    return SelfServiceSalaryRead(
        has_assignment=True,
        template_title=template.title if template else None,
        component_amounts=assignment.component_amounts,
        effective_from=assignment.effective_from,
    )


async def my_payslips(scope: AccessScope, user: User):
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    rows = await HrEmployeePayslip.find(
        Eq(HrEmployeePayslip.tenant_id, tenant_id),
        Eq(HrEmployeePayslip.employee_user_id, user.id),
        Eq(HrEmployeePayslip.status, HrPayslipStatus.PUBLISHED),
    ).sort(-HrEmployeePayslip.created_at).to_list()
    return [
        {
            "id": str(r.id),
            "period_label": r.period_label,
            "payslip_code": r.payslip_code,
            "payment_status": (r.document_payload or {}).get("payment_status"),
        }
        for r in rows
    ]


async def my_payslip_detail(scope: AccessScope, user: User, payslip_id: str):
    _assert_self(scope, user.id)
    return await get_payslip_for_employee_self(scope, payslip_id, user.id)


async def my_payroll_documents(scope: AccessScope, user: User):
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    rows = await HrEmployeePayrollDocument.find(
        Eq(HrEmployeePayrollDocument.tenant_id, tenant_id),
        Eq(HrEmployeePayrollDocument.employee_user_id, user.id),
    ).to_list()
    return rows


async def my_tax_declaration_save(scope: AccessScope, user: User, payload: TaxDeclarationUpsert) -> TaxDeclarationRead:
    _assert_self(scope, user.id)
    return await save_tax_declaration_draft(scope, str(user.id), payload, self_service=True)


async def my_tax_declaration_submit(scope: AccessScope, user: User, declaration_id: str) -> TaxDeclarationRead:
    _assert_self(scope, user.id)
    return await submit_tax_declaration(scope, declaration_id, self_service=True)


async def my_tax_declarations(scope: AccessScope, user: User):
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    rows = await EmployeeTaxDeclaration.find(
        Eq(EmployeeTaxDeclaration.tenant_id, tenant_id),
        Eq(EmployeeTaxDeclaration.employee_user_id, user.id),
    ).to_list()
    return [TaxDeclarationRead.from_doc(r) for r in rows]


async def submit_self_service_request(scope: AccessScope, user: User, payload: SelfServiceRequestCreate) -> SelfServiceRequestRead:
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    row = EmployeeSelfServiceRequest(
        tenant_id=tenant_id,
        employee_user_id=user.id,
        request_type=payload.request_type,
        title=payload.title,
        payload=payload.payload,
        employee_note=payload.employee_note,
        status=HrSelfServiceRequestStatus.SUBMITTED,
        submitted_at=utcnow(),
    )
    await row.insert()
    await EmployeeSelfServiceRequestHistory(
        tenant_id=tenant_id,
        request_id=row.id,
        action="submitted",
        to_status=row.status.value,
        actor_id=user.id,
    ).insert()
    return SelfServiceRequestRead.from_doc(row)


async def list_self_service_requests(scope: AccessScope, user: User) -> list[SelfServiceRequestRead]:
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    rows = await EmployeeSelfServiceRequest.find(
        Eq(EmployeeSelfServiceRequest.tenant_id, tenant_id),
        Eq(EmployeeSelfServiceRequest.employee_user_id, user.id),
    ).sort(-EmployeeSelfServiceRequest.created_at).to_list()
    return [SelfServiceRequestRead.from_doc(r) for r in rows]


async def my_employment_info(scope: AccessScope, user: User):
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    emp = await _employee_record(tenant_id, user.id)
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, user.id))
    return {
        "department_id": str(emp.department_id) if emp.department_id else None,
        "designation": emp.designation,
        "employment_type": (emp.confidential_hr or {}).get("employment_type"),
        "employee_category": profile.employee_category if profile else None,
        "employment_status": emp.employment_status.value,
        "campus_id": str(emp.campus_id) if emp.campus_id else None,
        "reporting_manager_user_id": str(profile.reporting_manager_user_id) if profile and profile.reporting_manager_user_id else None,
        "probation_end_date": profile.probation_end_date.isoformat() if profile and profile.probation_end_date else None,
        "contract_end_date": profile.contract_end_date.isoformat() if profile and profile.contract_end_date else None,
    }


async def my_onboarding(scope: AccessScope, user: User):
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    process = await HrOnboardingProcess.find_one(
        Eq(HrOnboardingProcess.tenant_id, tenant_id),
        Eq(HrOnboardingProcess.employee_user_id, user.id),
        Eq(HrOnboardingProcess.status, HrOnboardingProcessStatus.IN_PROGRESS),
    )
    if process is None:
        return None
    tasks = await HrOnboardingTask.find(
        Eq(HrOnboardingTask.tenant_id, tenant_id),
        Eq(HrOnboardingTask.process_id, process.id),
    ).to_list()
    return {
        "process_id": str(process.id),
        "status": process.status.value,
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "status": t.status.value,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            }
            for t in tasks
            if t.status != HrOnboardingTaskStatus.WAIVED
        ],
    }


async def my_benefits(scope: AccessScope, user: User):
    from beanie.odm.operators.find.comparison import Eq

    from app.modules.hr.benefits_models import EmployeeBenefitClaim, EmployeeBenefitEnrollment, HrBenefitProgram
    from app.modules.hr.benefits_schemas import BenefitClaimRead, BenefitEnrollmentRead, BenefitProgramRead
    from app.modules.hr.enums import HrBenefitProgramStatus

    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    programs = await HrBenefitProgram.find(
        Eq(HrBenefitProgram.tenant_id, tenant_id),
        Eq(HrBenefitProgram.status, HrBenefitProgramStatus.ACTIVE),
    ).to_list()
    enrollments = await EmployeeBenefitEnrollment.find(
        Eq(EmployeeBenefitEnrollment.tenant_id, tenant_id),
        Eq(EmployeeBenefitEnrollment.employee_user_id, user.id),
    ).to_list()
    claims = await EmployeeBenefitClaim.find(
        Eq(EmployeeBenefitClaim.tenant_id, tenant_id),
        Eq(EmployeeBenefitClaim.employee_user_id, user.id),
    ).to_list()
    return {
        "programs": [BenefitProgramRead.from_doc(p) for p in programs],
        "enrollments": [BenefitEnrollmentRead.from_doc(e) for e in enrollments],
        "claims": [BenefitClaimRead.from_doc(c) for c in claims],
    }


async def my_notifications(scope: AccessScope, user: User, limit: int = 50) -> list[SelfServiceNotificationRead]:
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    events = await DomainOutboxEvent.find(Eq(DomainOutboxEvent.tenant_id, tenant_id)).sort(-DomainOutboxEvent.created_at).limit(200).to_list()
    out: list[SelfServiceNotificationRead] = []
    uid = str(user.id)
    for ev in events:
        payload = ev.payload or {}
        if payload.get("recipient_user_id") != uid:
            continue
        if not ev.event_type.startswith("hr."):
            continue
        out.append(
            SelfServiceNotificationRead(
                event_type=ev.event_type,
                title=str(payload.get("title", "")),
                body=str(payload.get("body", "")),
                created_at=ev.created_at,
            )
        )
        if len(out) >= limit:
            break
    return out


async def my_attendance_correction(scope: AccessScope, user: User, payload: AttendanceCorrectionCreate):
    tenant_id = require_employee_tenant_scope(scope)
    _assert_self(scope, user.id)
    if payload.employee_user_id and to_object_id(payload.employee_user_id, "employee_user_id") != user.id:
        raise AppError(code="FORBIDDEN", message="Cannot request correction for another employee", status_code=403)
    current = await HrEmployeeAttendanceRecord.find_one(
        Eq(HrEmployeeAttendanceRecord.tenant_id, tenant_id),
        Eq(HrEmployeeAttendanceRecord.employee_user_id, user.id),
        Eq(HrEmployeeAttendanceRecord.attendance_date, payload.attendance_date),
    )
    previous = {}
    if current:
        previous = {"status": current.status.value}
    row = EmployeeAttendanceCorrection(
        tenant_id=tenant_id,
        employee_user_id=user.id,
        attendance_date=payload.attendance_date,
        requested_status=payload.requested_status,
        reason=payload.reason,
        status=EmployeeAttendanceCorrectionStatus.PENDING,
        previous_snapshot=previous,
        proposed_snapshot={"status": payload.requested_status.value},
    )
    await row.insert()
    return {"correction_id": str(row.id)}