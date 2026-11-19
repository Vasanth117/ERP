"""Benefits programs, enrollment, claims and finance handoff."""

from decimal import Decimal
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.benefits_eligibility import evaluate_benefit_eligibility, has_active_enrollment
from app.modules.hr.benefits_models import (
    EmployeeBenefitClaim,
    EmployeeBenefitClaimPayment,
    EmployeeBenefitClaimReview,
    EmployeeBenefitEnrollment,
    EmployeeBenefitEnrollmentHistory,
    HrBenefitProgram,
    claim_duplicate_hash,
)
from app.modules.hr.benefits_schemas import (
    BenefitClaimCreate,
    BenefitClaimPaymentConfirm,
    BenefitClaimRead,
    BenefitClaimReview,
    BenefitEligibilityRead,
    BenefitEnrollmentCreate,
    BenefitEnrollmentRead,
    BenefitEnrollmentReview,
    BenefitProgramRead,
    BenefitProgramUpsert,
    BenefitsDashboard,
    BenefitsReports,
)
from app.modules.hr.employee_profile_models import HrEmployeeProfile
from app.modules.hr.enums import (
    HrBenefitClaimStatus,
    HrBenefitEnrollmentStatus,
    HrBenefitProgramStatus,
)
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.policy import (
    authorize_hr_benefits_approve,
    authorize_hr_benefits_manage,
    authorize_hr_benefits_pay,
    authorize_hr_benefits_read,
    require_employee_tenant_scope,
    require_hr_tenant_scope,
)
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def benefits_dashboard(scope: AccessScope) -> BenefitsDashboard:
    authorize_hr_benefits_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    dash = BenefitsDashboard()
    programs = await HrBenefitProgram.find(Eq(HrBenefitProgram.tenant_id, tenant_id)).to_list()
    dash.total_programs = len(programs)
    dash.active_programs = sum(1 for p in programs if p.status == HrBenefitProgramStatus.ACTIVE)
    enrollments = await EmployeeBenefitEnrollment.find(Eq(EmployeeBenefitEnrollment.tenant_id, tenant_id)).to_list()
    dash.enrolled_employees = len({str(e.employee_user_id) for e in enrollments if e.status == HrBenefitEnrollmentStatus.ACTIVE})
    dash.pending_enrollments = sum(1 for e in enrollments if e.status in {HrBenefitEnrollmentStatus.PENDING, HrBenefitEnrollmentStatus.UNDER_REVIEW})
    employees = await EmployeeRecord.find(Eq(EmployeeRecord.tenant_id, tenant_id)).to_list()
    dash.eligible_employees = len(employees)
    claims = await EmployeeBenefitClaim.find(Eq(EmployeeBenefitClaim.tenant_id, tenant_id)).to_list()
    for c in claims:
        if c.status == HrBenefitClaimStatus.AWAITING_REVIEW:
            dash.claims_awaiting_review += 1
        elif c.status in {HrBenefitClaimStatus.APPROVED, HrBenefitClaimStatus.PARTIALLY_APPROVED}:
            dash.approved_claims += 1
        elif c.status == HrBenefitClaimStatus.REJECTED:
            dash.rejected_claims += 1
        elif c.status == HrBenefitClaimStatus.AWAITING_PAYMENT:
            dash.claims_awaiting_payment += 1
        elif c.status == HrBenefitClaimStatus.PAID:
            dash.paid_claims += 1
        elif c.status == HrBenefitClaimStatus.PAYMENT_FAILED:
            dash.failed_claims += 1
    return dash


async def upsert_benefit_program(scope: AccessScope, payload: BenefitProgramUpsert) -> BenefitProgramRead:
    authorize_hr_benefits_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrBenefitProgram.find_one(
        Eq(HrBenefitProgram.tenant_id, tenant_id),
        Eq(HrBenefitProgram.program_code, payload.program_code),
    )
    data = payload.model_dump()
    if doc:
        for k, v in data.items():
            setattr(doc, k, v)
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrBenefitProgram(tenant_id=tenant_id, actor_id=scope.user_id, **data)
        await doc.insert()
    return BenefitProgramRead.from_doc(doc)


async def list_benefit_programs(scope: AccessScope) -> list[BenefitProgramRead]:
    authorize_hr_benefits_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrBenefitProgram.find(Eq(HrBenefitProgram.tenant_id, tenant_id)).to_list()
    return [BenefitProgramRead.from_doc(r) for r in rows]


async def check_eligibility(scope: AccessScope, program_id: str, employee_user_id: str) -> BenefitEligibilityRead:
    if Permission_check_hr(scope):
        authorize_hr_benefits_read(scope)
        tenant_id = require_hr_tenant_scope(scope)
    else:
        tenant_id = require_employee_tenant_scope(scope)
    pid = to_object_id(program_id, "program_id")
    uid = to_object_id(employee_user_id, "employee_user_id")
    if not Permission_check_hr(scope) and scope.user_id != uid:
        raise AppError(code="FORBIDDEN", message="Eligibility check denied", status_code=403)
    program = await HrBenefitProgram.get(pid)
    if program is None or program.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Benefit program not found", status_code=404)
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, uid))
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee not found", status_code=404)
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, uid))
    eligible, reason = await evaluate_benefit_eligibility(program=program, employee=employee, profile=profile)
    return BenefitEligibilityRead(eligible=eligible, reason=reason, program_id=str(program.id))


def Permission_check_hr(scope: AccessScope) -> bool:
    from app.authorization.permissions import Permission

    return Permission.HR_BENEFITS_READ in scope.effective_permissions or Permission.HR_BENEFITS_MANAGE in scope.effective_permissions


async def create_enrollment(scope: AccessScope, payload: BenefitEnrollmentCreate, *, self_service: bool) -> BenefitEnrollmentRead:
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    if self_service:
        if scope.user_id != uid:
            raise AppError(code="FORBIDDEN", message="Cannot enroll another employee", status_code=403)
        tenant_id = require_employee_tenant_scope(scope)
    else:
        authorize_hr_benefits_manage(scope)
        tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(payload.benefit_program_id, "benefit_program_id")
    program = await HrBenefitProgram.get(pid)
    if program is None or program.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Benefit program not found", status_code=404)
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.tenant_id, tenant_id), Eq(EmployeeRecord.user_id, uid))
    profile = await HrEmployeeProfile.find_one(Eq(HrEmployeeProfile.tenant_id, tenant_id), Eq(HrEmployeeProfile.user_id, uid))
    if employee is None:
        raise AppError(code="NOT_FOUND", message="Employee not found", status_code=404)
    eligible, reason = await evaluate_benefit_eligibility(program=program, employee=employee, profile=profile)
    if not eligible:
        raise AppError(code="VALIDATION_ERROR", message=reason or "Not eligible", status_code=422)
    if program.required_documents and not payload.document_refs:
        raise AppError(code="VALIDATION_ERROR", message="Required documents missing", status_code=422)
    status = HrBenefitEnrollmentStatus.UNDER_REVIEW if program.requires_approval else HrBenefitEnrollmentStatus.ACTIVE
    row = EmployeeBenefitEnrollment(
        tenant_id=tenant_id,
        benefit_program_id=program.id,
        program_code=program.program_code,
        employee_user_id=uid,
        enrollment_source=payload.enrollment_source,
        dependents=payload.dependents,
        document_refs=payload.document_refs,
        status=status,
        effective_from=program.valid_from,
        effective_to=program.valid_to,
        actor_id=scope.user_id,
    )
    await row.insert()
    await EmployeeBenefitEnrollmentHistory(
        tenant_id=tenant_id,
        enrollment_id=row.id,
        action="created",
        to_status=row.status.value,
        actor_id=scope.user_id,
    ).insert()
    return BenefitEnrollmentRead.from_doc(row)


async def review_enrollment(scope: AccessScope, enrollment_id: str, payload: BenefitEnrollmentReview) -> BenefitEnrollmentRead:
    authorize_hr_benefits_approve(scope)
    tenant_id = require_hr_tenant_scope(scope)
    eid = to_object_id(enrollment_id, "enrollment_id")
    row = await EmployeeBenefitEnrollment.get(eid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Enrollment not found", status_code=404)
    prev = row.status.value
    if payload.action == "approve":
        row.status = HrBenefitEnrollmentStatus.ACTIVE
        row.effective_from = payload.effective_from or row.effective_from
        row.effective_to = payload.effective_to or row.effective_to
    else:
        row.status = HrBenefitEnrollmentStatus.REJECTED
    row.reviewer_id = scope.user_id
    row.reviewer_note = payload.reviewer_note
    row.updated_at = utcnow()
    await row.save()
    await EmployeeBenefitEnrollmentHistory(
        tenant_id=tenant_id,
        enrollment_id=row.id,
        action=payload.action,
        from_status=prev,
        to_status=row.status.value,
        note=payload.reviewer_note,
        actor_id=scope.user_id,
    ).insert()
    await enqueue_hr_notification(
        tenant_id,
        event_type="hr.benefit.enrollment_reviewed",
        aggregate_type="employee_benefit_enrollment",
        aggregate_id=str(row.id),
        title="Benefit enrollment update",
        body=f"Your enrollment for {row.program_code} is {row.status.value}",
        recipient_user_id=row.employee_user_id,
        dedupe_key=f"hr:benefit_enroll:{row.id}:{row.status.value}",
    )
    return BenefitEnrollmentRead.from_doc(row)


async def create_claim(scope: AccessScope, payload: BenefitClaimCreate, *, self_service: bool) -> BenefitClaimRead:
    uid = to_object_id(payload.employee_user_id, "employee_user_id")
    if self_service:
        if scope.user_id != uid:
            raise AppError(code="FORBIDDEN", message="Cannot file claim for another employee", status_code=403)
        tenant_id = require_employee_tenant_scope(scope)
    else:
        authorize_hr_benefits_manage(scope)
        tenant_id = require_hr_tenant_scope(scope)
    pid = to_object_id(payload.benefit_program_id, "benefit_program_id")
    program = await HrBenefitProgram.get(pid)
    if program is None or program.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Benefit program not found", status_code=404)
    if not await has_active_enrollment(tenant_id, uid, program.id):
        raise AppError(code="VALIDATION_ERROR", message="Active enrollment required", status_code=422)
    dup = claim_duplicate_hash(uid, program.id, payload.claim_date, payload.requested_amount)
    existing = await EmployeeBenefitClaim.find_one(
        Eq(EmployeeBenefitClaim.tenant_id, tenant_id),
        Eq(EmployeeBenefitClaim.duplicate_hash, dup),
        In(
            EmployeeBenefitClaim.status,
            [
                HrBenefitClaimStatus.AWAITING_REVIEW,
                HrBenefitClaimStatus.UNDER_REVIEW,
                HrBenefitClaimStatus.APPROVED,
                HrBenefitClaimStatus.PARTIALLY_APPROVED,
                HrBenefitClaimStatus.AWAITING_PAYMENT,
            ],
        ),
    )
    if existing:
        raise AppError(code="CONFLICT", message="Duplicate claim detected", status_code=409)
    limit = Decimal(program.coverage_limit or "0")
    if limit > 0 and Decimal(payload.requested_amount) > limit:
        raise AppError(code="VALIDATION_ERROR", message="Requested amount exceeds benefit limit", status_code=422)
    if program.required_documents and not payload.document_refs:
        raise AppError(code="VALIDATION_ERROR", message="Required documents missing for claim", status_code=422)
    code = f"CLM-{uuid4().hex[:10].upper()}"
    row = EmployeeBenefitClaim(
        tenant_id=tenant_id,
        claim_code=code,
        benefit_program_id=program.id,
        enrollment_id=to_object_id(payload.enrollment_id, "enrollment_id") if payload.enrollment_id else None,
        employee_user_id=uid,
        claim_category=payload.claim_category,
        claim_date=payload.claim_date,
        description=payload.description,
        expense_amount=payload.expense_amount,
        requested_amount=payload.requested_amount,
        document_refs=payload.document_refs,
        duplicate_hash=dup,
        status=HrBenefitClaimStatus.AWAITING_REVIEW,
        submitted_at=utcnow(),
        actor_id=scope.user_id,
    )
    await row.insert()
    return BenefitClaimRead.from_doc(row)


async def review_claim(scope: AccessScope, claim_id: str, payload: BenefitClaimReview) -> BenefitClaimRead:
    authorize_hr_benefits_approve(scope)
    tenant_id = require_hr_tenant_scope(scope)
    cid = to_object_id(claim_id, "claim_id")
    row = await EmployeeBenefitClaim.get(cid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Claim not found", status_code=404)
    if row.status not in {
        HrBenefitClaimStatus.AWAITING_REVIEW,
        HrBenefitClaimStatus.UNDER_REVIEW,
        HrBenefitClaimStatus.RETURNED,
    }:
        raise AppError(code="CONFLICT", message="Claim not reviewable", status_code=409)
    if payload.action == "approve":
        row.status = HrBenefitClaimStatus.APPROVED
        row.approved_amount = payload.approved_amount or row.requested_amount
    elif payload.action == "partial":
        row.status = HrBenefitClaimStatus.PARTIALLY_APPROVED
        if not payload.approved_amount:
            raise AppError(code="VALIDATION_ERROR", message="approved_amount required for partial approval", status_code=422)
        row.approved_amount = payload.approved_amount
    elif payload.action == "reject":
        row.status = HrBenefitClaimStatus.REJECTED
        row.approved_amount = "0"
    else:
        row.status = HrBenefitClaimStatus.RETURNED
    row.reviewer_id = scope.user_id
    row.reviewer_note = payload.reviewer_note
    row.updated_at = utcnow()
    await row.save()
    await EmployeeBenefitClaimReview(
        tenant_id=tenant_id,
        claim_id=row.id,
        stage=payload.stage,
        action=payload.action,
        approved_amount=row.approved_amount,
        note=payload.reviewer_note,
        actor_id=scope.user_id,
    ).insert()
    if row.status in {HrBenefitClaimStatus.APPROVED, HrBenefitClaimStatus.PARTIALLY_APPROVED}:
        row.status = HrBenefitClaimStatus.AWAITING_PAYMENT
        row.updated_at = utcnow()
        await row.save()
    await enqueue_hr_notification(
        tenant_id,
        event_type="hr.benefit.claim_reviewed",
        aggregate_type="employee_benefit_claim",
        aggregate_id=str(row.id),
        title="Benefit claim update",
        body=f"Claim {row.claim_code} is now {row.status.value}",
        recipient_user_id=row.employee_user_id,
        dedupe_key=f"hr:benefit_claim:{row.id}:{row.status.value}",
    )
    return BenefitClaimRead.from_doc(row)


async def submit_claim_for_payment(scope: AccessScope, claim_id: str) -> dict:
    authorize_hr_benefits_pay(scope)
    tenant_id = require_hr_tenant_scope(scope)
    cid = to_object_id(claim_id, "claim_id")
    row = await EmployeeBenefitClaim.get(cid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Claim not found", status_code=404)
    if row.status != HrBenefitClaimStatus.AWAITING_PAYMENT:
        raise AppError(code="CONFLICT", message="Claim is not awaiting payment", status_code=409)
    idem = f"benefit_claim:{row.id}"
    if await EmployeeBenefitClaimPayment.find_one(
        Eq(EmployeeBenefitClaimPayment.tenant_id, tenant_id),
        Eq(EmployeeBenefitClaimPayment.idempotency_key, idem),
    ):
        raise AppError(code="CONFLICT", message="Payment already submitted", status_code=409)
    await EmployeeBenefitClaimPayment(
        tenant_id=tenant_id,
        claim_id=row.id,
        employee_user_id=row.employee_user_id,
        amount=row.approved_amount,
        idempotency_key=idem,
        status="submitted",
        actor_id=scope.user_id,
    ).insert()
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type="finance.benefit.claim_payment_requested",
        aggregate_type="employee_benefit_claim",
        aggregate_id=str(row.id),
        payload={"claim_code": row.claim_code, "amount": row.approved_amount},
        idempotency_key=f"finance:benefit:{row.id}",
        status=OutboxEventStatus.PENDING,
    ).insert()
    row.payment_status = "submitted"
    row.updated_at = utcnow()
    await row.save()
    return {"submitted": True, "claim_id": str(row.id)}


async def confirm_claim_payment(scope: AccessScope, claim_id: str, payload: BenefitClaimPaymentConfirm) -> BenefitClaimRead:
    authorize_hr_benefits_pay(scope)
    tenant_id = require_hr_tenant_scope(scope)
    cid = to_object_id(claim_id, "claim_id")
    row = await EmployeeBenefitClaim.get(cid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Claim not found", status_code=404)
    pay = await EmployeeBenefitClaimPayment.find_one(
        Eq(EmployeeBenefitClaimPayment.tenant_id, tenant_id),
        Eq(EmployeeBenefitClaimPayment.claim_id, row.id),
    )
    if pay is None:
        raise AppError(code="NOT_FOUND", message="Payment record not found", status_code=404)
    if pay.status == "reconciled":
        raise AppError(code="CONFLICT", message="Payment already reconciled", status_code=409)
    pay.payment_reference = payload.payment_reference
    pay.status = "reconciled"
    pay.reconciled_at = utcnow()
    pay.updated_at = utcnow()
    await pay.save()
    row.status = HrBenefitClaimStatus.PAID
    row.payment_status = "paid"
    row.payment_reference = payload.payment_reference
    row.updated_at = utcnow()
    await row.save()
    return BenefitClaimRead.from_doc(row)


async def list_claims(scope: AccessScope, employee_user_id: str | None = None) -> list[BenefitClaimRead]:
    authorize_hr_benefits_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(EmployeeBenefitClaim.tenant_id, tenant_id)]
    if employee_user_id:
        filters.append(Eq(EmployeeBenefitClaim.employee_user_id, to_object_id(employee_user_id, "employee_user_id")))
    rows = await EmployeeBenefitClaim.find(*filters).sort(-EmployeeBenefitClaim.created_at).to_list()
    return [BenefitClaimRead.from_doc(r) for r in rows]


async def benefits_reports(scope: AccessScope) -> BenefitsReports:
    authorize_hr_benefits_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    report = BenefitsReports()
    enrollments = await EmployeeBenefitEnrollment.find(Eq(EmployeeBenefitEnrollment.tenant_id, tenant_id)).to_list()
    for e in enrollments:
        report.enrollments_by_program[e.program_code] = report.enrollments_by_program.get(e.program_code, 0) + 1
    claims = await EmployeeBenefitClaim.find(Eq(EmployeeBenefitClaim.tenant_id, tenant_id)).to_list()
    total = Decimal("0")
    for c in claims:
        report.claims_by_category[c.claim_category] = report.claims_by_category.get(c.claim_category, 0) + 1
        if c.status == HrBenefitClaimStatus.AWAITING_REVIEW:
            report.pending_claims += 1
        elif c.status in {HrBenefitClaimStatus.APPROVED, HrBenefitClaimStatus.PARTIALLY_APPROVED}:
            report.approved_claims += 1
        elif c.status == HrBenefitClaimStatus.REJECTED:
            report.rejected_claims += 1
        elif c.status == HrBenefitClaimStatus.AWAITING_PAYMENT:
            report.awaiting_payment += 1
        elif c.status == HrBenefitClaimStatus.PAID:
            report.paid_claims += 1
            total += Decimal(c.approved_amount or "0")
    report.utilization_total = str(total.quantize(Decimal("0.01")))
    return report