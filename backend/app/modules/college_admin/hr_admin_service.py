"""HR administration services."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.hr_admin_models import (
    EmployeeBenefitRecord,
    EmployeeLeaveApproval,
    EmployeeLeavePolicy,
    EmployeeOffboardingRecord,
    EmployeeOnboardingRecord,
    EmployeePerformanceRecord,
    HrPolicy,
    PayrollConfiguration,
    RecruitmentRecord,
    RecruitmentStatus,
)
from app.modules.college_admin.hr_admin_schemas import (
    HrPolicyRead,
    HrPolicyUpsert,
    LeaveDecision,
    LeavePolicyUpsert,
    OffboardingCreate,
    OnboardingCreate,
    PayrollConfigRead,
    PayrollConfigUpsert,
    RecruitmentCreate,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.models import LeaveRequest, PayslipReference


async def upsert_hr_policy(scope: AccessScope, payload: HrPolicyUpsert) -> HrPolicyRead:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.policy_code.strip()
    doc = await HrPolicy.find_one(Eq(HrPolicy.tenant_id, tenant_id), Eq(HrPolicy.policy_code, code))
    if doc:
        doc.title = payload.title
        doc.body = payload.body
        doc.version += 1
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrPolicy(tenant_id=tenant_id, policy_code=code, title=payload.title, body=payload.body, updated_by=scope.user_id)
        await doc.insert()
    return HrPolicyRead.from_document(doc)


async def publish_hr_policy(scope: AccessScope, policy_code: str) -> HrPolicyRead:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await HrPolicy.find_one(Eq(HrPolicy.tenant_id, tenant_id), Eq(HrPolicy.policy_code, policy_code))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="HR policy not found", status_code=404)
    doc.published = True
    doc.updated_at = utcnow()
    await doc.save()
    return HrPolicyRead.from_document(doc)


async def create_recruitment(scope: AccessScope, payload: RecruitmentCreate) -> dict:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    if await RecruitmentRecord.find_one(Eq(RecruitmentRecord.tenant_id, tenant_id), Eq(RecruitmentRecord.requisition_id, payload.requisition_id)):
        raise AppError(code="CONFLICT", message="Requisition already exists", status_code=409)
    dept = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    row = RecruitmentRecord(
        tenant_id=tenant_id,
        requisition_id=payload.requisition_id,
        role_title=payload.role_title,
        department_id=dept,
        actor_id=scope.user_id,
    )
    await row.insert()
    return {"requisition_id": row.requisition_id}


async def start_onboarding(scope: AccessScope, payload: OnboardingCreate) -> dict:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    user_id = to_object_id(payload.user_id, "user_id")
    if await EmployeeOnboardingRecord.find_one(Eq(EmployeeOnboardingRecord.tenant_id, tenant_id), Eq(EmployeeOnboardingRecord.user_id, user_id)):
        raise AppError(code="CONFLICT", message="Onboarding already started", status_code=409)
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, user_id))
    row = EmployeeOnboardingRecord(
        tenant_id=tenant_id,
        user_id=user_id,
        employee_record_id=employee.id if employee else None,
        checklist=payload.checklist,
        actor_id=scope.user_id,
    )
    await row.insert()
    return {"onboarding_id": str(row.id)}


async def complete_onboarding(scope: AccessScope, user_id: str) -> dict:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    uid = to_object_id(user_id, "user_id")
    row = await EmployeeOnboardingRecord.find_one(Eq(EmployeeOnboardingRecord.tenant_id, tenant_id), Eq(EmployeeOnboardingRecord.user_id, uid))
    if row is None:
        raise AppError(code="NOT_FOUND", message="Onboarding record not found", status_code=404)
    row.completed = True
    row.completed_at = utcnow()
    await row.save()
    return {"user_id": user_id, "completed": True}


async def record_offboarding(scope: AccessScope, payload: OffboardingCreate) -> dict:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    user_id = to_object_id(payload.user_id, "user_id")
    row = EmployeeOffboardingRecord(
        tenant_id=tenant_id,
        user_id=user_id,
        reason=payload.reason,
        last_working_date=payload.last_working_date,
        actor_id=scope.user_id,
    )
    await row.insert()
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, user_id))
    if employee:
        employee.employment_status = FacultyEmploymentStatus.TERMINATED
        employee.updated_at = utcnow()
        await employee.save()
    return {"offboarding_id": str(row.id)}


async def upsert_leave_policy(scope: AccessScope, payload: LeavePolicyUpsert) -> dict:
    authorize(scope, Permission.HR_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await EmployeeLeavePolicy.find_one(Eq(EmployeeLeavePolicy.tenant_id, tenant_id), Eq(EmployeeLeavePolicy.leave_type, payload.leave_type))
    if doc:
        doc.annual_quota_days = payload.annual_quota_days
        doc.requires_approval = payload.requires_approval
        doc.rules = payload.rules
        doc.version += 1
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await EmployeeLeavePolicy(
            tenant_id=tenant_id,
            leave_type=payload.leave_type,
            annual_quota_days=payload.annual_quota_days,
            requires_approval=payload.requires_approval,
            rules=payload.rules,
            updated_by=scope.user_id,
        ).insert()
    return {"leave_type": payload.leave_type}


async def decide_leave(scope: AccessScope, payload: LeaveDecision) -> dict:
    authorize(scope, Permission.HR_ADMIN_LEAVE_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    if payload.decision not in (LeaveRequestStatus.APPROVED, LeaveRequestStatus.REJECTED):
        raise AppError(code="VALIDATION_ERROR", message="Invalid leave decision", status_code=422)
    leave_id = to_object_id(payload.leave_request_id, "leave_request_id")
    req = await LeaveRequest.get(leave_id)
    if req is None or req.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Leave request not found", status_code=404)
    if req.status != LeaveRequestStatus.SUBMITTED:
        raise AppError(code="CONFLICT", message="Leave request is not pending", status_code=409)
    if await EmployeeLeaveApproval.find_one(Eq(EmployeeLeaveApproval.tenant_id, tenant_id), Eq(EmployeeLeaveApproval.leave_request_id, leave_id)):
        raise AppError(code="CONFLICT", message="Leave already reviewed", status_code=409)
    req.status = payload.decision
    req.approver_note = payload.note
    req.updated_at = utcnow()
    await req.save()
    await EmployeeLeaveApproval(
        tenant_id=tenant_id,
        leave_request_id=leave_id,
        employee_user_id=req.employee_user_id,
        decision=payload.decision,
        reviewer_id=scope.user_id,
        note=payload.note,
    ).insert()
    return {"leave_request_id": str(leave_id), "decision": payload.decision.value}


async def list_pending_leave(scope: AccessScope, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = LeaveRequest.find(Eq(LeaveRequest.tenant_id, tenant_id), Eq(LeaveRequest.status, LeaveRequestStatus.SUBMITTED)).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            {
                "leave_request_id": str(r.id),
                "employee_user_id": str(r.employee_user_id),
                "leave_type": r.leave_type,
                "start_date": r.start_date.isoformat(),
                "end_date": r.end_date.isoformat(),
            }
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def upsert_payroll_config(scope: AccessScope, payload: PayrollConfigUpsert, *, confidential_config: dict | None = None) -> PayrollConfigRead:
    authorize(scope, Permission.HR_ADMIN_PAYROLL_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    doc = await PayrollConfiguration.find_one(Eq(PayrollConfiguration.tenant_id, tenant_id), Eq(PayrollConfiguration.config_id, payload.config_id))
    if doc:
        doc.label = payload.label
        doc.pay_frequency = payload.pay_frequency
        doc.integration_provider = payload.integration_provider
        if confidential_config is not None:
            doc.confidential_config = confidential_config
        doc.version += 1
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = PayrollConfiguration(
            tenant_id=tenant_id,
            config_id=payload.config_id,
            label=payload.label,
            pay_frequency=payload.pay_frequency,
            integration_provider=payload.integration_provider,
            confidential_config=confidential_config or {},
            updated_by=scope.user_id,
        )
        await doc.insert()
    return PayrollConfigRead.from_document(doc)


async def payroll_status(scope: AccessScope) -> dict:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    configs = await PayrollConfiguration.find(Eq(PayrollConfiguration.tenant_id, tenant_id)).to_list()
    payslips = await PayslipReference.find(Eq(PayslipReference.tenant_id, tenant_id)).count()
    return {
        "configurations": [{"config_id": c.config_id, "last_run_status": c.last_run_status} for c in configs],
        "payslip_references": payslips,
    }


async def workforce_statistics(scope: AccessScope) -> dict:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).count()
    active = await EmployeeRecord.find(
        Eq(EmployeeRecord.tenant_id, tenant_id),
        Eq(EmployeeRecord.employment_status, FacultyEmploymentStatus.ACTIVE),
    ).count()
    open_roles = await RecruitmentRecord.find(
        Eq(RecruitmentRecord.tenant_id, tenant_id),
        Eq(RecruitmentRecord.status, RecruitmentStatus.OPEN),
    ).count()
    onboarding = await EmployeeOnboardingRecord.find(
        Eq(EmployeeOnboardingRecord.tenant_id, tenant_id),
        Eq(EmployeeOnboardingRecord.completed, False),
    ).count()
    return {"employees": employees, "active_employees": active, "open_requisitions": open_roles, "in_onboarding": onboarding}


async def hr_report(scope: AccessScope) -> dict:
    authorize(scope, Permission.HR_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    pending_leave = await LeaveRequest.find(Eq(LeaveRequest.tenant_id, tenant_id), Eq(LeaveRequest.status, LeaveRequestStatus.SUBMITTED)).count()
    policies = await HrPolicy.find(Eq(HrPolicy.tenant_id, tenant_id), Eq(HrPolicy.published, True)).count()
    benefits = await EmployeeBenefitRecord.find(Eq(EmployeeBenefitRecord.tenant_id, tenant_id)).count()
    performance = await EmployeePerformanceRecord.find(Eq(EmployeePerformanceRecord.tenant_id, tenant_id)).count()
    return {"pending_leave": pending_leave, "published_policies": policies, "benefit_records": benefits, "performance_records": performance}
