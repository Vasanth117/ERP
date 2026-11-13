"""Finance administration services."""

from datetime import timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.finance_admin_models import (
    FinancialApprovalRecord,
    FinancialPeriod,
    InstitutionFeeStructure,
    PaymentReconciliationRecord,
    RefundRequest,
    StudentFeeAssessment,
)
from app.modules.college_admin.finance_admin_schemas import (
    ConcessionCreate,
    FeeAssessmentCreate,
    FeeStructureRead,
    FeeStructureUpsert,
    FinancialPeriodUpsert,
    OfflineCollectionCreate,
    ReconciliationConfirm,
    RefundDecision,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus, RefundStatus
from app.modules.finance.finance_models import (
    FeeConcession,
    PaymentTransaction,
    RefundRecord,
    StudentFeeDemand,
    StudentFeeInvoice,
    StudentFeeStructure,
    StudentFinancialLedgerEntry,
)
from app.modules.finance.payment_reconciliation import reconcile_successful_payment
from app.modules.finance.payment_verification import apply_verified_payment


async def _financial_approval(
    scope: AccessScope,
    tenant_id: PydanticObjectId,
    *,
    scope_key: str,
    resource_type: str,
    resource_id: str,
    decision: str,
    note: str | None = None,
) -> None:
    await FinancialApprovalRecord(
        tenant_id=tenant_id,
        scope=scope_key,
        resource_type=resource_type,
        resource_id=resource_id,
        decision=decision,
        actor_id=scope.user_id,
        note=note,
    ).insert()


async def _sync_fee_structure(tenant_id: PydanticObjectId, admin: InstitutionFeeStructure) -> None:
    ref = await StudentFeeStructure.find_one(
        Eq(StudentFeeStructure.tenant_id, tenant_id),
        Eq(StudentFeeStructure.structure_id, admin.structure_id),
    )
    if ref is None:
        ref = StudentFeeStructure(
            tenant_id=tenant_id,
            structure_id=admin.structure_id,
            programme_code=admin.programme_code,
            academic_year_label=admin.academic_year_label,
            semester_label=admin.semester_label,
            line_items=admin.line_items,
            total_amount=admin.total_amount,
        )
    ref.line_items = admin.line_items
    ref.total_amount = admin.total_amount
    ref.published = admin.published
    ref.updated_at = utcnow()
    if ref.id is None:
        await ref.insert()
        admin.authoritative_structure_id = ref.id
        await admin.save()
    else:
        await ref.save()


async def upsert_fee_structure(scope: AccessScope, payload: FeeStructureUpsert) -> FeeStructureRead:
    authorize(scope, Permission.FINANCE_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    sid = payload.structure_id.strip()
    existing = await InstitutionFeeStructure.find_one(
        Eq(InstitutionFeeStructure.tenant_id, tenant_id),
        Eq(InstitutionFeeStructure.structure_id, sid),
    )
    if existing:
        existing.programme_code = payload.programme_code.upper()
        existing.academic_year_label = payload.academic_year_label
        existing.semester_label = payload.semester_label
        existing.line_items = payload.line_items
        existing.total_amount = payload.total_amount
        existing.version += 1
        existing.updated_by = scope.user_id
        existing.updated_at = utcnow()
        await existing.save()
        doc = existing
    else:
        doc = InstitutionFeeStructure(
            tenant_id=tenant_id,
            structure_id=sid,
            programme_code=payload.programme_code.upper(),
            academic_year_label=payload.academic_year_label,
            semester_label=payload.semester_label,
            line_items=payload.line_items,
            total_amount=payload.total_amount,
            updated_by=scope.user_id,
        )
        await doc.insert()
    await _sync_fee_structure(tenant_id, doc)
    return FeeStructureRead.from_document(doc)


async def publish_fee_structure(scope: AccessScope, structure_id: str) -> FeeStructureRead:
    authorize(scope, Permission.FINANCE_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionFeeStructure.find_one(
        Eq(InstitutionFeeStructure.tenant_id, tenant_id),
        Eq(InstitutionFeeStructure.structure_id, structure_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Fee structure not found", status_code=404)
    doc.published = True
    doc.updated_at = utcnow()
    await doc.save()
    await _sync_fee_structure(tenant_id, doc)
    return FeeStructureRead.from_document(doc)


async def create_fee_assessment(scope: AccessScope, payload: FeeAssessmentCreate) -> dict:
    authorize(scope, Permission.FINANCE_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    structure = await InstitutionFeeStructure.find_one(
        Eq(InstitutionFeeStructure.tenant_id, tenant_id),
        Eq(InstitutionFeeStructure.structure_id, payload.structure_id),
    )
    if structure is None:
        structure = await StudentFeeStructure.find_one(
            Eq(StudentFeeStructure.tenant_id, tenant_id),
            Eq(StudentFeeStructure.structure_id, payload.structure_id),
        )
    if structure is None:
        raise AppError(code="NOT_FOUND", message="Fee structure not found", status_code=404)
    total = getattr(structure, "total_amount", 0)
    net = max(0.0, total - payload.concession_amount)
    assessment_id = f"assess_{uuid4().hex}"
    demand_id = f"dem_{uuid4().hex}"
    invoice_id = f"inv_{uuid4().hex}"
    due = utcnow().date() + timedelta(days=30)
    await StudentFeeDemand(
        tenant_id=tenant_id,
        student_user_id=student_id,
        demand_id=demand_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        description=f"Fee assessment {assessment_id}",
        amount=net,
        due_date=due,
        status=FeeDemandStatus.OPEN,
    ).insert()
    await StudentFeeInvoice(
        tenant_id=tenant_id,
        student_user_id=student_id,
        invoice_id=invoice_id,
        demand_id=demand_id,
        amount=net,
        issued_at=utcnow(),
        due_date=due,
        published=False,
    ).insert()
    last = (
        await StudentFinancialLedgerEntry.find(
            Eq(StudentFinancialLedgerEntry.tenant_id, tenant_id),
            Eq(StudentFinancialLedgerEntry.student_user_id, student_id),
        )
        .sort("-posted_at")
        .limit(1)
        .to_list()
    )
    balance = last[0].balance_after if last else 0.0
    balance_after = balance + net
    await StudentFinancialLedgerEntry(
        tenant_id=tenant_id,
        student_user_id=student_id,
        entry_id=f"led_{uuid4().hex}",
        entry_type="fee_assessment",
        description=f"Assessment {assessment_id}",
        debit=net,
        credit=0,
        balance_after=balance_after,
        reference_id=assessment_id,
    ).insert()
    assessment = StudentFeeAssessment(
        tenant_id=tenant_id,
        student_user_id=student_id,
        assessment_id=assessment_id,
        structure_id=payload.structure_id,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        assessed_amount=total,
        concession_amount=payload.concession_amount,
        net_amount=net,
        demand_id=demand_id,
        invoice_id=invoice_id,
        actor_id=scope.user_id,
    )
    await assessment.insert()
    return {"assessment_id": assessment_id, "demand_id": demand_id, "invoice_id": invoice_id, "net_amount": net}


async def record_offline_collection(scope: AccessScope, payload: OfflineCollectionCreate) -> dict:
    authorize(scope, Permission.FINANCE_ADMIN_TRANSACTIONS)
    tenant_id = require_college_tenant_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    existing = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.idempotency_key, payload.idempotency_key),
    )
    if existing:
        if existing.status == PaymentTransactionStatus.SUCCESS:
            return {"transaction_id": existing.transaction_id, "status": existing.status.value, "duplicate": True}
        raise AppError(code="CONFLICT", message="Idempotency key already used", status_code=409)
    transaction_id = f"pay_{uuid4().hex}"
    tx = PaymentTransaction(
        tenant_id=tenant_id,
        student_user_id=student_id,
        transaction_id=transaction_id,
        idempotency_key=payload.idempotency_key,
        demand_id=payload.demand_id,
        amount=payload.amount,
        status=PaymentTransactionStatus.SUCCESS,
        gateway="offline",
        offline_reference=payload.offline_reference,
        payment_mode="offline",
        webhook_verified=True,
    )
    await tx.insert()
    await reconcile_successful_payment(tx)
    await PaymentReconciliationRecord(
        tenant_id=tenant_id,
        transaction_id=transaction_id,
        gateway_reference=payload.offline_reference,
        reconciled=True,
        actor_id=scope.user_id,
    ).insert()
    return {"transaction_id": transaction_id, "status": tx.status.value}


async def list_transactions(scope: AccessScope, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id)).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            {
                "transaction_id": r.transaction_id,
                "student_user_id": str(r.student_user_id),
                "amount": r.amount,
                "status": r.status.value,
                "payment_mode": r.payment_mode,
                "webhook_verified": r.webhook_verified,
            }
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def reconcile_payment(scope: AccessScope, payload: ReconciliationConfirm) -> dict:
    authorize(scope, Permission.FINANCE_ADMIN_RECONCILE)
    tenant_id = require_college_tenant_scope(scope)
    tx = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.transaction_id, payload.transaction_id),
    )
    if tx is None:
        raise AppError(code="NOT_FOUND", message="Transaction not found", status_code=404)
    if tx.status == PaymentTransactionStatus.SUCCESS and tx.webhook_verified:
        rec = await PaymentReconciliationRecord.find_one(
            Eq(PaymentReconciliationRecord.tenant_id, tenant_id),
            Eq(PaymentReconciliationRecord.transaction_id, payload.transaction_id),
        )
        if rec and rec.reconciled:
            return {"transaction_id": tx.transaction_id, "reconciled": True, "duplicate": True}
    if payload.gateway_reference and tx.payment_mode == "online":
        tx = await apply_verified_payment(payload.transaction_id, gateway_reference=payload.gateway_reference)
    rec = await PaymentReconciliationRecord.find_one(
        Eq(PaymentReconciliationRecord.tenant_id, tenant_id),
        Eq(PaymentReconciliationRecord.transaction_id, payload.transaction_id),
    )
    if rec is None:
        rec = PaymentReconciliationRecord(
            tenant_id=tenant_id,
            transaction_id=payload.transaction_id,
            gateway_reference=payload.gateway_reference,
            reconciled=True,
            discrepancy_note=payload.discrepancy_note,
            actor_id=scope.user_id,
        )
        await rec.insert()
    else:
        rec.reconciled = True
        rec.discrepancy_note = payload.discrepancy_note
        await rec.save()
    await _financial_approval(
        scope,
        tenant_id,
        scope_key="reconciliation",
        resource_type="payment_transaction",
        resource_id=payload.transaction_id,
        decision="reconciled",
        note=payload.discrepancy_note,
    )
    return {"transaction_id": tx.transaction_id, "reconciled": True}


async def student_ledger(scope: AccessScope, student_user_id: str, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    sid = to_object_id(student_user_id, "student_user_id")
    query = StudentFinancialLedgerEntry.find(
        Eq(StudentFinancialLedgerEntry.tenant_id, tenant_id),
        Eq(StudentFinancialLedgerEntry.student_user_id, sid),
    ).sort("-posted_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            {
                "entry_id": r.entry_id,
                "entry_type": r.entry_type,
                "debit": r.debit,
                "credit": r.credit,
                "balance_after": r.balance_after,
                "posted_at": r.posted_at.isoformat(),
            }
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def create_concession(scope: AccessScope, payload: ConcessionCreate) -> dict:
    authorize(scope, Permission.FINANCE_ADMIN_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    student_id = to_object_id(payload.student_user_id, "student_user_id")
    concession_id = f"conc_{uuid4().hex}"
    doc = FeeConcession(
        tenant_id=tenant_id,
        student_user_id=student_id,
        concession_id=concession_id,
        title=payload.title,
        amount=payload.amount,
        percent=payload.percent,
        published=False,
    )
    await doc.insert()
    await _financial_approval(
        scope,
        tenant_id,
        scope_key="concession",
        resource_type="fee_concession",
        resource_id=concession_id,
        decision="created",
    )
    return {"concession_id": concession_id}


async def approve_concession(scope: AccessScope, concession_id: str) -> dict:
    authorize(scope, Permission.FINANCE_ADMIN_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await FeeConcession.find_one(
        Eq(FeeConcession.tenant_id, tenant_id),
        Eq(FeeConcession.concession_id, concession_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Concession not found", status_code=404)
    doc.published = True
    await doc.save()
    await _financial_approval(scope, tenant_id, scope_key="concession", resource_type="fee_concession", resource_id=concession_id, decision="approved")
    return {"concession_id": concession_id, "published": True}


async def request_refund(scope: AccessScope, student_user_id: str, transaction_id: str, amount: float) -> dict:
    authorize(scope, Permission.FINANCE_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    student_id = to_object_id(student_user_id, "student_user_id")
    tx = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.transaction_id, transaction_id),
    )
    if tx is None or tx.status != PaymentTransactionStatus.SUCCESS:
        raise AppError(code="VALIDATION_ERROR", message="Successful transaction required", status_code=422)
    refund_id = f"rf_{uuid4().hex}"
    record = RefundRecord(
        tenant_id=tenant_id,
        student_user_id=student_id,
        refund_id=refund_id,
        transaction_id=transaction_id,
        amount=amount,
        status=RefundStatus.REQUESTED,
    )
    await record.insert()
    req = RefundRequest(
        tenant_id=tenant_id,
        student_user_id=student_id,
        refund_id=refund_id,
        refund_record_id=record.id,
        amount=amount,
        actor_id=scope.user_id,
    )
    await req.insert()
    return {"refund_id": refund_id}


async def decide_refund(scope: AccessScope, payload: RefundDecision) -> dict:
    authorize(scope, Permission.FINANCE_ADMIN_APPROVE)
    tenant_id = require_college_tenant_scope(scope)
    if payload.decision not in (RefundStatus.APPROVED, RefundStatus.REJECTED, RefundStatus.PROCESSED):
        raise AppError(code="VALIDATION_ERROR", message="Invalid refund decision", status_code=422)
    record = await RefundRecord.find_one(
        Eq(RefundRecord.tenant_id, tenant_id),
        Eq(RefundRecord.refund_id, payload.refund_id),
    )
    if record is None:
        raise AppError(code="NOT_FOUND", message="Refund not found", status_code=404)
    if record.status in (RefundStatus.PROCESSED, RefundStatus.REJECTED):
        raise AppError(code="CONFLICT", message="Refund already finalized", status_code=409)
    record.status = payload.decision
    record.updated_at = utcnow()
    await record.save()
    req = await RefundRequest.find_one(Eq(RefundRequest.tenant_id, tenant_id), Eq(RefundRequest.refund_id, payload.refund_id))
    if req:
        req.status = payload.decision
        req.updated_at = utcnow()
        await req.save()
    if payload.decision == RefundStatus.PROCESSED and record.transaction_id:
        tx = await PaymentTransaction.find_one(
            Eq(PaymentTransaction.tenant_id, tenant_id),
            Eq(PaymentTransaction.transaction_id, record.transaction_id),
        )
        if tx and tx.status != PaymentTransactionStatus.REFUNDED:
            tx.status = PaymentTransactionStatus.REFUNDED
            tx.updated_at = utcnow()
            await tx.save()
    await _financial_approval(
        scope,
        tenant_id,
        scope_key="refund",
        resource_type="refund_record",
        resource_id=payload.refund_id,
        decision=payload.decision.value,
        note=payload.note,
    )
    return {"refund_id": payload.refund_id, "status": record.status.value}


async def upsert_financial_period(scope: AccessScope, payload: FinancialPeriodUpsert) -> dict:
    authorize(scope, Permission.FINANCE_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.period_code.strip()
    existing = await FinancialPeriod.find_one(Eq(FinancialPeriod.tenant_id, tenant_id), Eq(FinancialPeriod.period_code, code))
    if existing:
        existing.label = payload.label
        existing.start_date = payload.start_date
        existing.end_date = payload.end_date
        existing.updated_by = scope.user_id
        await existing.save()
    else:
        await FinancialPeriod(
            tenant_id=tenant_id,
            period_code=code,
            label=payload.label,
            start_date=payload.start_date,
            end_date=payload.end_date,
            updated_by=scope.user_id,
        ).insert()
    return {"period_code": code}


async def finance_report(scope: AccessScope) -> dict:
    authorize(scope, Permission.FINANCE_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    open_demands = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        Eq(StudentFeeDemand.status, FeeDemandStatus.OPEN),
    ).count()
    overdue = await StudentFeeDemand.find(
        Eq(StudentFeeDemand.tenant_id, tenant_id),
        Eq(StudentFeeDemand.status, FeeDemandStatus.OVERDUE),
    ).count()
    successful_payments = await PaymentTransaction.find(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.status, PaymentTransactionStatus.SUCCESS),
    ).count()
    pending_refunds = await RefundRecord.find(
        Eq(RefundRecord.tenant_id, tenant_id),
        Eq(RefundRecord.status, RefundStatus.REQUESTED),
    ).count()
    return {
        "open_demands": open_demands,
        "overdue_demands": overdue,
        "successful_payments": successful_payments,
        "pending_refunds": pending_refunds,
    }
