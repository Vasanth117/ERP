"""Parent finance reads, payment initiation, and enquiries."""

from uuid import uuid4

from beanie import PydanticObjectId

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction
from app.modules.parents.enums import ParentDataPermission, ParentFinanceEnquiryStatus
from app.modules.parents.models import (
    ParentFinanceEnquiry,
    ParentFinanceEnquiryHistory,
    ParentPaymentInitiationRecord,
    ParentPaymentTransactionReference,
)
from app.modules.parents.phase3_schemas import (
    ParentFinanceDashboardRead,
    ParentFinanceEnquiryCreate,
    ParentFinanceEnquiryRead,
    ParentFinanceStatementLineRead,
    ParentFinanceStatementRead,
    ParentPaymentInitiateInput,
)
from app.modules.parents.policy import require_parent_scope
from app.modules.parents.relationship_access import require_student_access
from app.modules.parents.student_context import resolve_student_for_parent
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.student_finance_reader import (
    concessions_for_student,
    demands_for_student,
    fee_structures_for_student,
    installment_schedules,
    payments_for_student,
    receipts_for_student,
    scholarship_eligibility_rows,
)
from app.modules.students.student_finance_schemas import (
    FeeDemandRead,
    FeeStructureRead,
    OutstandingDuesRead,
    PaymentHistoryRead,
    PaymentInitiateRead,
    PaymentStatusRead,
    ReceiptRead,
    InstallmentScheduleRead,
    ScholarshipEligibilityRead,
)

_reader = StudentDataReader()
_OPEN_STATUSES = frozenset({FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE})


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def get_finance_dashboard(scope: AccessScope, parent: User, student_user_id: str) -> ParentFinanceDashboardRead:
    authorize(scope, Permission.PARENT_FINANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_FEES)
    year, semester = await _term(tenant_id)
    demands = [r for r in await demands_for_student(tenant_id, sid) if r.status in _OPEN_STATUSES]
    total = sum(r.amount + r.late_fee for r in demands)
    structures = await fee_structures_for_student(tenant_id, sid, year=year, semester=semester)
    payments = await payments_for_student(tenant_id, sid)
    receipts = await receipts_for_student(tenant_id, sid)
    scholarships = await scholarship_eligibility_rows(tenant_id, sid)
    return ParentFinanceDashboardRead(
        outstanding=OutstandingDuesRead(
            total_outstanding=round(total, 2),
            demands=[
                FeeDemandRead(
                    demand_id=r.demand_id,
                    description=r.description,
                    amount=r.amount,
                    due_date=r.due_date,
                    status=r.status.value,
                    late_fee=r.late_fee,
                )
                for r in demands
            ],
        ),
        fee_structures=[
            FeeStructureRead(
                structure_id=r.structure_id,
                academic_year_label=r.academic_year_label,
                semester_label=r.semester_label,
                line_items=r.line_items,
                total_amount=r.total_amount,
            )
            for r in structures
        ],
        recent_payments=[
            PaymentHistoryRead(
                transaction_id=r.transaction_id,
                amount=r.amount,
                status=r.status.value,
                created_at=r.created_at,
            )
            for r in payments[:10]
        ],
        receipt_count=len(receipts),
        scholarships_eligible=sum(1 for s in scholarships if s.eligible),
    )


async def get_fee_statement(scope: AccessScope, parent: User, student_user_id: str) -> ParentFinanceStatementRead:
    authorize(scope, Permission.PARENT_FINANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_FEES)
    demands = await demands_for_student(tenant_id, sid)
    concessions = {c.concession_id: c for c in await concessions_for_student(tenant_id, sid)}
    lines: list[ParentFinanceStatementLineRead] = []
    total_out = 0.0
    total_concession = sum(c.amount for c in concessions.values())
    concession_per = total_concession / len(demands) if demands and total_concession else 0.0
    for d in demands:
        net = max(0.0, d.amount + d.late_fee - concession_per)
        paid = 0.0 if d.status not in {FeeDemandStatus.PAID, FeeDemandStatus.CLOSED} else net
        outstanding = 0.0 if d.status in {FeeDemandStatus.PAID, FeeDemandStatus.CLOSED} else net
        if d.status in _OPEN_STATUSES:
            total_out += outstanding
        lines.append(
            ParentFinanceStatementLineRead(
                demand_id=d.demand_id,
                description=d.description,
                original_amount=d.amount,
                net_payable=net,
                amount_paid=paid,
                outstanding=outstanding,
                due_date=d.due_date,
                status=d.status.value,
            )
        )
    return ParentFinanceStatementRead(lines=lines, total_outstanding=round(total_out, 2))


async def list_installments(scope: AccessScope, parent: User, student_user_id: str) -> list[InstallmentScheduleRead]:
    authorize(scope, Permission.PARENT_FINANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_FEES)
    rows = await installment_schedules(tenant_id, sid)
    return [InstallmentScheduleRead(schedule_id=r.schedule_id, installments=r.installments) for r in rows]


async def list_scholarships(scope: AccessScope, parent: User, student_user_id: str) -> list[ScholarshipEligibilityRead]:
    authorize(scope, Permission.PARENT_FINANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_FEES)
    rows = await scholarship_eligibility_rows(tenant_id, sid)
    return [ScholarshipEligibilityRead(programme_id=r.programme_id, eligible=r.eligible, reasons=r.reasons) for r in rows]


async def list_receipts_parent(scope: AccessScope, parent: User, student_user_id: str) -> list[ReceiptRead]:
    authorize(scope, Permission.PARENT_FINANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_RECEIPTS)
    rows = await receipts_for_student(tenant_id, sid)
    return [
        ReceiptRead(
            receipt_id=r.receipt_id,
            transaction_id=r.transaction_id,
            amount=r.amount,
            issued_at=r.issued_at,
            download_token=r.storage_token,
        )
        for r in rows
    ]


async def payment_history_parent(scope: AccessScope, parent: User, student_user_id: str) -> list[PaymentHistoryRead]:
    authorize(scope, Permission.PARENT_FINANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_FEES)
    rows = await payments_for_student(tenant_id, sid)
    return [
        PaymentHistoryRead(
            transaction_id=r.transaction_id,
            amount=r.amount,
            status=r.status.value,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def initiate_parent_payment(
    scope: AccessScope, parent: User, student_user_id: str, payload: ParentPaymentInitiateInput
) -> PaymentInitiateRead:
    authorize(scope, Permission.PARENT_FINANCE_PAY)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.PAY_FEES)
    rel, _ = await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.PAY_FEES)

    existing_parent = await ParentPaymentInitiationRecord.find_one(
        {"tenant_id": tenant_id, "idempotency_key": payload.idempotency_key}
    )
    if existing_parent is not None:
        tx = await PaymentTransaction.find_one(
            {"tenant_id": tenant_id, "transaction_id": existing_parent.transaction_id, "student_user_id": sid}
        )
        if tx is None:
            raise AppError(code="CONFLICT", message="Payment attempt inconsistent", status_code=409)
        return PaymentInitiateRead(
            transaction_id=tx.transaction_id,
            status=tx.status.value,
            amount=tx.amount,
            gateway=tx.gateway,
        )

    existing_tx = await PaymentTransaction.find_one({"tenant_id": tenant_id, "idempotency_key": payload.idempotency_key})
    if existing_tx is not None:
        return PaymentInitiateRead(
            transaction_id=existing_tx.transaction_id,
            status=existing_tx.status.value,
            amount=existing_tx.amount,
            gateway=existing_tx.gateway,
        )

    demands = await demands_for_student(tenant_id, sid)
    match = next((d for d in demands if d.demand_id == payload.demand_id), None)
    if match is None:
        raise AppError(code="NOT_FOUND", message="Fee demand not found", status_code=404)
    if match.status not in _OPEN_STATUSES:
        raise AppError(code="CONFLICT", message="Fee demand is not payable", status_code=409)

    success_tx = await PaymentTransaction.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": sid,
            "demand_id": payload.demand_id,
            "status": PaymentTransactionStatus.SUCCESS,
            "webhook_verified": True,
        }
    )
    if success_tx is not None:
        raise AppError(code="CONFLICT", message="Demand already paid", status_code=409)

    amount = match.amount + match.late_fee
    transaction_id = f"pay_{uuid4().hex}"
    gateway = "offline" if payload.payment_mode == "offline" else "stub"
    initial_status = (
        PaymentTransactionStatus.PENDING if payload.payment_mode == "offline" else PaymentTransactionStatus.INITIATED
    )
    offline_ref = (payload.offline_reference or "").strip() or None
    tx = PaymentTransaction(
        tenant_id=tenant_id,
        student_user_id=sid,
        transaction_id=transaction_id,
        idempotency_key=payload.idempotency_key,
        demand_id=payload.demand_id,
        amount=amount,
        status=initial_status,
        gateway=gateway,
        payment_mode=payload.payment_mode,
        offline_reference=offline_ref,
        gateway_reference=offline_ref if payload.payment_mode == "offline" else None,
    )
    await tx.insert()
    await ParentPaymentInitiationRecord(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        relationship_id=rel.id,
        transaction_id=transaction_id,
        demand_id=payload.demand_id,
        idempotency_key=payload.idempotency_key,
        amount=amount,
        gateway=gateway,
        status=initial_status.value,
    ).insert()
    await ParentPaymentTransactionReference(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        transaction_id=transaction_id,
    ).insert()
    return PaymentInitiateRead(
        transaction_id=transaction_id,
        status=tx.status.value,
        amount=amount,
        gateway=tx.gateway,
    )


async def get_payment_status_parent(
    scope: AccessScope, parent: User, student_user_id: str, transaction_id: str
) -> PaymentStatusRead:
    authorize(scope, Permission.PARENT_FINANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_FEES)
    ref = await ParentPaymentTransactionReference.find_one(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "transaction_id": transaction_id}
    )
    tx = await PaymentTransaction.find_one(
        {"tenant_id": tenant_id, "student_user_id": sid, "transaction_id": transaction_id}
    )
    if tx is None or ref is None:
        raise AppError(code="NOT_FOUND", message="Payment not found", status_code=404)
    effective_status = tx.status.value
    if tx.status == PaymentTransactionStatus.SUCCESS and not tx.webhook_verified:
        effective_status = PaymentTransactionStatus.PENDING.value
    return PaymentStatusRead(
        transaction_id=tx.transaction_id,
        status=effective_status,
        webhook_verified=tx.webhook_verified,
        gateway_reference=tx.gateway_reference,
    )


async def submit_finance_enquiry(
    scope: AccessScope, parent: User, student_user_id: str, payload: ParentFinanceEnquiryCreate
) -> ParentFinanceEnquiryRead:
    authorize(scope, Permission.PARENT_FINANCE_ENQUIRY)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_FEES)
    rel, _ = await require_student_access(tenant_id, parent.id, sid, ParentDataPermission.VIEW_FEES)
    doc = ParentFinanceEnquiry(
        tenant_id=tenant_id,
        parent_user_id=parent.id,
        student_user_id=sid,
        relationship_id=rel.id,
        category=payload.category,
        transaction_id=payload.transaction_id,
        receipt_id=payload.receipt_id,
        description=payload.description.strip(),
        status=ParentFinanceEnquiryStatus.SUBMITTED.value,
    )
    await doc.insert()
    await ParentFinanceEnquiryHistory(
        tenant_id=tenant_id,
        enquiry_id=doc.id,
        from_status=None,
        to_status=doc.status,
        note="Submitted by parent",
        changed_by=parent.id,
    ).insert()
    return ParentFinanceEnquiryRead(
        enquiry_id=str(doc.id),
        category=doc.category,
        status=doc.status,
        description=doc.description,
        response_notes=doc.response_notes,
        created_at=doc.created_at,
    )


async def list_finance_enquiries(
    scope: AccessScope, parent: User, student_user_id: str
) -> list[ParentFinanceEnquiryRead]:
    authorize(scope, Permission.PARENT_FINANCE_READ)
    tenant_id = require_parent_scope(scope)
    sid = await resolve_student_for_parent(scope, parent, student_user_id, ParentDataPermission.VIEW_FEES)
    rows = await ParentFinanceEnquiry.find(
        {"tenant_id": tenant_id, "parent_user_id": parent.id, "student_user_id": sid}
    ).sort("-created_at").to_list()
    return [
        ParentFinanceEnquiryRead(
            enquiry_id=str(r.id),
            category=r.category,
            status=r.status,
            description=r.description,
            response_notes=r.response_notes,
            created_at=r.created_at,
        )
        for r in rows
    ]