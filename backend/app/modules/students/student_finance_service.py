"""Student fees, payments, scholarships and financial aid."""

from __future__ import annotations

from uuid import uuid4

from beanie import PydanticObjectId

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.finance.finance_enums import FeeDemandStatus, PaymentTransactionStatus, ScholarshipApplicationStatus
from app.modules.finance.finance_models import (
    OfficialScholarshipApplication,
    PaymentTransaction,
    ScholarshipProgram,
)
from app.modules.finance.payment_reconciliation import reconcile_successful_payment
from app.modules.students.integrations.data_reader import StudentDataReader
from app.modules.students.integrations.student_finance_reader import (
    concessions_for_student,
    demands_for_student,
    fee_structures_for_student,
    installment_schedules,
    invoices_for_student,
    ledger_for_student,
    official_scholarship_application,
    payments_for_student,
    receipts_for_student,
    refunds_for_student,
    scholarship_eligibility_rows,
)
from app.modules.students.policy import require_student_scope
from app.modules.students.student_finance_models import (
    StudentFinancialDocumentReference,
    StudentPaymentAttempt,
    StudentPaymentNotificationLog,
    StudentScholarshipApplication,
)
from app.modules.students.student_finance_schemas import (
    ConcessionRead,
    FeeDemandRead,
    FeeStructureRead,
    InstallmentScheduleRead,
    LedgerEntryRead,
    OutstandingDuesRead,
    PaymentHistoryRead,
    PaymentInitiateInput,
    PaymentInitiateRead,
    PaymentStatusRead,
    ReceiptRead,
    RefundStatusRead,
    ScholarshipApplicationInput,
    ScholarshipApplicationRead,
    ScholarshipEligibilityRead,
)

_reader = StudentDataReader()
_OPEN_STATUSES = frozenset({FeeDemandStatus.OPEN, FeeDemandStatus.PARTIALLY_PAID, FeeDemandStatus.OVERDUE})


async def _term(tenant_id: PydanticObjectId) -> tuple[str, str]:
    context = await _reader.current_academic_context(tenant_id)
    if context is None:
        raise AppError(code="ACADEMIC_CONTEXT_MISSING", message="Academic year not configured", status_code=503)
    return context.academic_year_label, context.semester_label


async def get_fee_structure(scope: AccessScope, user: User) -> list[FeeStructureRead]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    year, semester = await _term(tenant_id)
    rows = await fee_structures_for_student(tenant_id, user.id, year=year, semester=semester)
    return [
        FeeStructureRead(
            structure_id=r.structure_id,
            academic_year_label=r.academic_year_label,
            semester_label=r.semester_label,
            line_items=r.line_items,
            total_amount=r.total_amount,
        )
        for r in rows
    ]


async def get_fee_demands(scope: AccessScope, user: User) -> list[FeeDemandRead]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await demands_for_student(tenant_id, user.id)
    return [
        FeeDemandRead(
            demand_id=r.demand_id,
            description=r.description,
            amount=r.amount,
            due_date=r.due_date,
            status=r.status.value,
            late_fee=r.late_fee,
        )
        for r in rows
    ]


async def get_invoices(scope: AccessScope, user: User) -> list[dict]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await invoices_for_student(tenant_id, user.id)
    return [
        {
            "invoice_id": r.invoice_id,
            "demand_id": r.demand_id,
            "amount": r.amount,
            "issued_at": r.issued_at,
            "due_date": r.due_date,
        }
        for r in rows
    ]


async def get_outstanding_dues(scope: AccessScope, user: User) -> OutstandingDuesRead:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = [r for r in await demands_for_student(tenant_id, user.id) if r.status in _OPEN_STATUSES]
    total = sum(r.amount + r.late_fee for r in rows)
    return OutstandingDuesRead(
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
            for r in rows
        ],
    )


async def initiate_payment(scope: AccessScope, user: User, payload: PaymentInitiateInput) -> PaymentInitiateRead:
    authorize(scope, Permission.STUDENT_FINANCE_MANAGE)
    tenant_id = require_student_scope(scope)
    attempt = await StudentPaymentAttempt.find_one({"tenant_id": tenant_id, "idempotency_key": payload.idempotency_key})
    if attempt is not None:
        tx = await PaymentTransaction.find_one(
            {"tenant_id": tenant_id, "transaction_id": attempt.transaction_id, "student_user_id": user.id}
        )
        if tx is None:
            raise AppError(code="CONFLICT", message="Payment attempt inconsistent", status_code=409)
        return PaymentInitiateRead(
            transaction_id=tx.transaction_id,
            status=tx.status.value,
            amount=tx.amount,
            gateway=tx.gateway,
        )
    existing_tx = await PaymentTransaction.find_one(
        {"tenant_id": tenant_id, "idempotency_key": payload.idempotency_key}
    )
    if existing_tx is not None:
        return PaymentInitiateRead(
            transaction_id=existing_tx.transaction_id,
            status=existing_tx.status.value,
            amount=existing_tx.amount,
            gateway=existing_tx.gateway,
        )
    demand = await demands_for_student(tenant_id, user.id)
    match = next((d for d in demand if d.demand_id == payload.demand_id), None)
    if match is None:
        raise AppError(code="NOT_FOUND", message="Fee demand not found", status_code=404)
    if match.status not in _OPEN_STATUSES:
        raise AppError(code="CONFLICT", message="Fee demand is not payable", status_code=409)
    success_tx = await PaymentTransaction.find_one(
        {
            "tenant_id": tenant_id,
            "student_user_id": user.id,
            "demand_id": payload.demand_id,
            "status": PaymentTransactionStatus.SUCCESS,
            "webhook_verified": True,
        }
    )
    if success_tx is not None:
        raise AppError(code="CONFLICT", message="Demand already paid", status_code=409)
    if payload.payment_mode == "offline":
        ref = (payload.offline_reference or "").strip()
        if len(ref) < 4:
            raise AppError(
                code="VALIDATION_ERROR",
                message="offline_reference is required for offline payments",
                status_code=422,
            )
    amount = match.amount + match.late_fee
    transaction_id = f"pay_{uuid4().hex}"
    offline_ref = (payload.offline_reference or "").strip() or None
    gateway = "offline" if payload.payment_mode == "offline" else "stub"
    initial_status = (
        PaymentTransactionStatus.PENDING if payload.payment_mode == "offline" else PaymentTransactionStatus.INITIATED
    )
    tx = PaymentTransaction(
        tenant_id=tenant_id,
        student_user_id=user.id,
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
    await StudentPaymentAttempt(
        tenant_id=tenant_id,
        user_id=user.id,
        idempotency_key=payload.idempotency_key,
        transaction_id=transaction_id,
        demand_id=payload.demand_id,
    ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.finance.payment_initiated",
        resource_type="payment_transaction",
        resource_id=transaction_id,
        tenant_id=tenant_id,
    )
    return PaymentInitiateRead(
        transaction_id=transaction_id,
        status=tx.status.value,
        amount=amount,
        gateway=tx.gateway,
    )


async def get_payment_status(scope: AccessScope, user: User, transaction_id: str) -> PaymentStatusRead:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    tx = await PaymentTransaction.find_one(
        {"tenant_id": tenant_id, "student_user_id": user.id, "transaction_id": transaction_id}
    )
    if tx is None:
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


async def payment_history(scope: AccessScope, user: User) -> list[PaymentHistoryRead]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await payments_for_student(tenant_id, user.id)
    return [
        PaymentHistoryRead(
            transaction_id=r.transaction_id,
            amount=r.amount,
            status=r.status.value if not (r.status == PaymentTransactionStatus.SUCCESS and not r.webhook_verified) else PaymentTransactionStatus.PENDING.value,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def list_receipts(scope: AccessScope, user: User) -> list[ReceiptRead]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await receipts_for_student(tenant_id, user.id)
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


async def installment_schedule(scope: AccessScope, user: User) -> list[InstallmentScheduleRead]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await installment_schedules(tenant_id, user.id)
    return [
        InstallmentScheduleRead(schedule_id=r.schedule_id, installments=r.installments)
        for r in rows
    ]


async def scholarship_eligibility(scope: AccessScope, user: User) -> list[ScholarshipEligibilityRead]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await scholarship_eligibility_rows(tenant_id, user.id)
    return [
        ScholarshipEligibilityRead(programme_id=r.programme_id, eligible=r.eligible, reasons=r.reasons)
        for r in rows
    ]


async def submit_scholarship(scope: AccessScope, user: User, payload: ScholarshipApplicationInput) -> ScholarshipApplicationRead:
    authorize(scope, Permission.STUDENT_FINANCE_MANAGE)
    tenant_id = require_student_scope(scope)
    programme = await ScholarshipProgram.find_one({"tenant_id": tenant_id, "programme_id": payload.programme_id})
    if programme is None or not programme.applications_open:
        raise AppError(code="FORBIDDEN", message="Scholarship applications are not open", status_code=403)
    elig = next(
        (e for e in await scholarship_eligibility_rows(tenant_id, user.id) if e.programme_id == payload.programme_id),
        None,
    )
    if elig is None or not elig.eligible:
        raise AppError(code="FORBIDDEN", message="Not eligible for this scholarship programme", status_code=403)
    application_id = f"sch_{uuid4().hex}"
    await StudentScholarshipApplication(
        tenant_id=tenant_id,
        user_id=user.id,
        application_id=application_id,
        programme_id=payload.programme_id,
        statement=payload.statement,
        status=ScholarshipApplicationStatus.SUBMITTED.value,
    ).insert()
    await OfficialScholarshipApplication(
        tenant_id=tenant_id,
        student_user_id=user.id,
        application_id=application_id,
        programme_id=payload.programme_id,
        status=ScholarshipApplicationStatus.SUBMITTED,
    ).insert()
    await record_audit(
        actor_id=scope.user_id,
        action="student.finance.scholarship_submitted",
        resource_type="scholarship_application",
        resource_id=application_id,
        tenant_id=tenant_id,
    )
    now = utcnow()
    return ScholarshipApplicationRead(
        application_id=application_id,
        programme_id=payload.programme_id,
        status=ScholarshipApplicationStatus.SUBMITTED.value,
        created_at=now,
    )


async def scholarship_status(scope: AccessScope, user: User, application_id: str) -> ScholarshipApplicationRead:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    portal = await StudentScholarshipApplication.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "application_id": application_id}
    )
    if portal is None:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    official = await official_scholarship_application(tenant_id, user.id, application_id)
    status = official.status.value if official else portal.status
    return ScholarshipApplicationRead(
        application_id=portal.application_id,
        programme_id=portal.programme_id,
        status=status,
        created_at=portal.created_at,
    )


async def list_concessions(scope: AccessScope, user: User) -> list[ConcessionRead]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await concessions_for_student(tenant_id, user.id)
    return [
        ConcessionRead(concession_id=r.concession_id, title=r.title, amount=r.amount, percent=r.percent)
        for r in rows
    ]


async def list_refunds(scope: AccessScope, user: User) -> list[RefundStatusRead]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await refunds_for_student(tenant_id, user.id)
    return [
        RefundStatusRead(
            refund_id=r.refund_id,
            amount=r.amount,
            status=r.status.value,
            transaction_id=r.transaction_id,
        )
        for r in rows
    ]


async def financial_ledger(scope: AccessScope, user: User) -> list[LedgerEntryRead]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await ledger_for_student(tenant_id, user.id)
    return [
        LedgerEntryRead(
            entry_id=r.entry_id,
            entry_type=r.entry_type,
            description=r.description,
            debit=r.debit,
            credit=r.credit,
            balance_after=r.balance_after,
            posted_at=r.posted_at,
        )
        for r in rows
    ]


async def get_fee_view_preferences(scope: AccessScope, user: User) -> dict:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    from app.modules.students.student_finance_models import StudentFeeViewPreferences

    row = await StudentFeeViewPreferences.find_one({"tenant_id": tenant_id, "user_id": user.id})
    if row is None:
        return {"show_installments": True}
    return {"show_installments": row.show_installments}


async def update_fee_view_preferences(scope: AccessScope, user: User, *, show_installments: bool) -> dict:
    authorize(scope, Permission.STUDENT_FINANCE_MANAGE)
    tenant_id = require_student_scope(scope)
    from app.modules.students.student_finance_models import StudentFeeViewPreferences

    row = await StudentFeeViewPreferences.find_one({"tenant_id": tenant_id, "user_id": user.id})
    if row is None:
        row = StudentFeeViewPreferences(tenant_id=tenant_id, user_id=user.id, show_installments=show_installments)
        await row.insert()
    else:
        row.show_installments = show_installments
        row.updated_at = utcnow()
        await row.save()
    return await get_fee_view_preferences(scope, user)


async def payment_reminders(scope: AccessScope, user: User) -> list[dict]:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    logs = (
        await StudentPaymentNotificationLog.find({"tenant_id": tenant_id, "user_id": user.id})
        .sort("-created_at")
        .limit(50)
        .to_list()
    )
    if logs:
        return [
            {
                "title": l.title,
                "body": l.body,
                "demand_id": l.demand_id,
                "created_at": l.created_at,
                "read_at": l.read_at,
            }
            for l in logs
        ]
    overdue = [d for d in await demands_for_student(tenant_id, user.id) if d.status == FeeDemandStatus.OVERDUE]
    generated: list[dict] = []
    for d in overdue[:10]:
        await StudentPaymentNotificationLog(
            tenant_id=tenant_id,
            user_id=user.id,
            title="Fee payment reminder",
            body=f"Outstanding: {d.description} (due {d.due_date})",
            demand_id=d.demand_id,
        ).insert()
        generated.append(
            {
                "title": "Fee payment reminder",
                "body": f"Outstanding: {d.description} (due {d.due_date})",
                "demand_id": d.demand_id,
                "created_at": utcnow(),
                "read_at": None,
            }
        )
    return generated


async def track_receipt_view(scope: AccessScope, user: User, receipt_id: str) -> None:
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    rows = await receipts_for_student(tenant_id, user.id)
    if not any(r.receipt_id == receipt_id for r in rows):
        raise AppError(code="NOT_FOUND", message="Receipt not found", status_code=404)
    ref = await StudentFinancialDocumentReference.find_one(
        {"tenant_id": tenant_id, "user_id": user.id, "document_id": receipt_id}
    )
    if ref is None:
        ref = StudentFinancialDocumentReference(
            tenant_id=tenant_id,
            user_id=user.id,
            document_id=receipt_id,
            document_type="receipt",
        )
        await ref.insert()
    else:
        ref.last_viewed_at = utcnow()
        ref.updated_at = utcnow()
        await ref.save()
    await record_audit(
        actor_id=scope.user_id,
        action="student.finance.receipt_viewed",
        resource_type="payment_receipt",
        resource_id=receipt_id,
        tenant_id=tenant_id,
    )


async def refresh_payment_reconciliation(scope: AccessScope, user: User, transaction_id: str) -> PaymentStatusRead:
    """Reload status after webhook processing (does not trust client success)."""
    authorize(scope, Permission.STUDENT_FINANCE_READ)
    tenant_id = require_student_scope(scope)
    tx = await PaymentTransaction.find_one(
        {"tenant_id": tenant_id, "student_user_id": user.id, "transaction_id": transaction_id}
    )
    if tx is None:
        raise AppError(code="NOT_FOUND", message="Payment not found", status_code=404)
    if tx.status == PaymentTransactionStatus.SUCCESS and tx.webhook_verified:
        await reconcile_successful_payment(tx)
    return await get_payment_status(scope, user, transaction_id)
