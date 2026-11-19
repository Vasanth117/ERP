"""Offline payment collection and verification."""

from datetime import date
from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.accounts_finance.money import round_money
from app.modules.accounts_finance.payment_core import demand_outstanding
from app.modules.accounts_finance.phase3_enums import OfflinePaymentMethod, OfflinePaymentStatus
from app.modules.accounts_finance.phase3_models import (
    OfflineCollectionBatch,
    OfflineCollectionHandoverRecord,
    OfflinePaymentInstrument,
    OfflinePaymentRecord,
    OfflinePaymentReversal,
    OfflinePaymentVerificationHistory,
)
from app.modules.accounts_finance.policy import (
    authorize_finance_offline_collect,
    authorize_finance_offline_verify,
    require_finance_tenant_scope,
)
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction, StudentFeeDemand
from app.modules.finance.payment_reconciliation import reconcile_successful_payment


async def record_offline_payment(scope: AccessScope, payload: dict) -> dict:
    authorize_finance_offline_collect(scope)
    tenant_id = require_finance_tenant_scope(scope)
    student_id = to_object_id(payload["student_user_id"], "student_user_id")
    demand_id = payload["demand_id"]
    demand = await StudentFeeDemand.find_one(Eq(StudentFeeDemand.tenant_id, tenant_id), Eq(StudentFeeDemand.demand_id, demand_id))
    if demand is None or demand.student_user_id != student_id:
        raise AppError(code="NOT_FOUND", message="Demand not found", status_code=404)
    amount = round_money(float(payload["amount"]))
    outstanding = await demand_outstanding(tenant_id, demand)
    if amount > outstanding:
        raise AppError(code="VALIDATION_ERROR", message="Amount exceeds outstanding", status_code=422)

    method = OfflinePaymentMethod(payload["payment_method"])
    record_id = f"off_{uuid4().hex[:12]}"
    status = OfflinePaymentStatus.CHEQUE_PENDING if method == OfflinePaymentMethod.CHEQUE else OfflinePaymentStatus.AWAITING_VERIFICATION

    existing = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.idempotency_key, payload["idempotency_key"]),
    )
    if existing:
        if existing.status == PaymentTransactionStatus.SUCCESS:
            raise AppError(code="CONFLICT", message="Duplicate idempotency key", status_code=409)
        transaction_id = existing.transaction_id
    else:
        transaction_id = f"pay_{uuid4().hex}"
        await PaymentTransaction(
            tenant_id=tenant_id,
            student_user_id=student_id,
            transaction_id=transaction_id,
            idempotency_key=payload["idempotency_key"],
            demand_id=demand_id,
            amount=amount,
            status=PaymentTransactionStatus.PENDING,
            gateway="offline",
            payment_mode="offline",
            offline_reference=payload.get("instrument_reference"),
        ).insert()

    record = OfflinePaymentRecord(
        tenant_id=tenant_id,
        record_id=record_id,
        student_user_id=student_id,
        invoice_id=payload.get("invoice_id"),
        demand_id=demand_id,
        transaction_id=transaction_id,
        amount=amount,
        payment_method=method,
        payment_date=payload.get("payment_date") or date.today(),
        status=status,
        instrument_reference=payload.get("instrument_reference"),
        bank_name=payload.get("bank_name"),
        branch=payload.get("branch"),
        collection_location=payload.get("collection_location"),
        collected_by=scope.user_id,
        remarks=payload.get("remarks"),
        document_ref=payload.get("document_ref"),
        batch_id=payload.get("batch_id"),
    )
    await record.insert()
    if method in (OfflinePaymentMethod.CHEQUE, OfflinePaymentMethod.DEMAND_DRAFT):
        await OfflinePaymentInstrument(
            tenant_id=tenant_id,
            instrument_id=f"ins_{uuid4().hex[:10]}",
            record_id=record_id,
            instrument_type=method,
            instrument_number=payload.get("instrument_reference"),
            issue_date=payload.get("issue_date"),
            clearance_status="pending",
        ).insert()
    await OfflinePaymentVerificationHistory(
        tenant_id=tenant_id,
        record_id=record_id,
        action="record",
        to_status=status.value,
        actor_id=scope.user_id,
    ).insert()
    await append_institution_audit(
        tenant_id, actor_id=scope.user_id, action="finance.offline.record", module="accounts_finance", resource_type="offline_payment", resource_id=record_id
    )
    return {"record_id": record_id, "transaction_id": record.transaction_id, "status": record.status.value}


async def verify_offline_payment(scope: AccessScope, record_id: str, *, note: str | None = None, cheque_cleared: bool = True) -> dict:
    authorize_finance_offline_verify(scope)
    tenant_id = require_finance_tenant_scope(scope)
    record = await OfflinePaymentRecord.find_one(
        Eq(OfflinePaymentRecord.tenant_id, tenant_id),
        Eq(OfflinePaymentRecord.record_id, record_id),
    )
    if record is None:
        raise AppError(code="NOT_FOUND", message="Offline payment not found", status_code=404)
    if record.status in (OfflinePaymentStatus.POSTED, OfflinePaymentStatus.REJECTED, OfflinePaymentStatus.REVERSED):
        raise AppError(code="CONFLICT", message="Record already finalized", status_code=409)

    if record.payment_method == OfflinePaymentMethod.CHEQUE and not cheque_cleared:
        record.status = OfflinePaymentStatus.CHEQUE_BOUNCED
        await record.save()
        inst = await OfflinePaymentInstrument.find_one(Eq(OfflinePaymentInstrument.tenant_id, tenant_id), Eq(OfflinePaymentInstrument.record_id, record_id))
        if inst:
            inst.clearance_status = "bounced"
            inst.bounce_reason = note
            await inst.save()
        await OfflinePaymentVerificationHistory(
            tenant_id=tenant_id, record_id=record_id, action="bounce", to_status=record.status.value, actor_id=scope.user_id, note=note
        ).insert()
        return {"record_id": record_id, "status": record.status.value}

    record.status = OfflinePaymentStatus.VERIFIED
    if record.payment_method == OfflinePaymentMethod.CHEQUE:
        record.status = OfflinePaymentStatus.CHEQUE_CLEARED
    record.updated_at = utcnow()
    await record.save()

    if not record.transaction_id:
        raise AppError(code="VALIDATION_ERROR", message="Missing transaction link", status_code=422)
    tx = await PaymentTransaction.find_one(
        Eq(PaymentTransaction.tenant_id, tenant_id),
        Eq(PaymentTransaction.transaction_id, record.transaction_id),
    )
    if tx is None:
        raise AppError(code="NOT_FOUND", message="Transaction not found", status_code=404)
    tx.status = PaymentTransactionStatus.SUCCESS
    tx.webhook_verified = True
    tx.updated_at = utcnow()
    await tx.save()
    await reconcile_successful_payment(tx)
    record.status = OfflinePaymentStatus.POSTED
    await record.save()

    await OfflinePaymentVerificationHistory(
        tenant_id=tenant_id, record_id=record_id, action="verify_post", to_status=record.status.value, actor_id=scope.user_id, note=note
    ).insert()
    return {"record_id": record_id, "status": record.status.value, "transaction_id": tx.transaction_id}


async def create_collection_batch(scope: AccessScope, *, batch_date: date, counter_code: str | None = None) -> dict:
    authorize_finance_offline_collect(scope)
    tenant_id = require_finance_tenant_scope(scope)
    batch_id = f"batch_{uuid4().hex[:10]}"
    await OfflineCollectionBatch(
        tenant_id=tenant_id,
        batch_id=batch_id,
        batch_date=batch_date,
        counter_code=counter_code,
        cashier_user_id=scope.user_id,
    ).insert()
    return {"batch_id": batch_id}


async def handover_batch(scope: AccessScope, batch_id: str, *, to_user_id: str, amount: float, note: str | None = None) -> dict:
    authorize_finance_offline_verify(scope)
    tenant_id = require_finance_tenant_scope(scope)
    batch = await OfflineCollectionBatch.find_one(Eq(OfflineCollectionBatch.tenant_id, tenant_id), Eq(OfflineCollectionBatch.batch_id, batch_id))
    if batch is None:
        raise AppError(code="NOT_FOUND", message="Batch not found", status_code=404)
    handover_id = f"ho_{uuid4().hex[:10]}"
    await OfflineCollectionHandoverRecord(
        tenant_id=tenant_id,
        handover_id=handover_id,
        batch_id=batch_id,
        from_user_id=scope.user_id,
        to_user_id=to_object_id(to_user_id, "to_user_id"),
        amount=round_money(amount),
        note=note,
    ).insert()
    return {"handover_id": handover_id}


async def reverse_offline_payment(scope: AccessScope, record_id: str, reason: str) -> dict:
    authorize_finance_offline_verify(scope)
    tenant_id = require_finance_tenant_scope(scope)
    record = await OfflinePaymentRecord.find_one(Eq(OfflinePaymentRecord.tenant_id, tenant_id), Eq(OfflinePaymentRecord.record_id, record_id))
    if record is None:
        raise AppError(code="NOT_FOUND", message="Record not found", status_code=404)
    reversal_id = f"rev_{uuid4().hex[:10]}"
    await OfflinePaymentReversal(
        tenant_id=tenant_id,
        reversal_id=reversal_id,
        record_id=record_id,
        transaction_id=record.transaction_id,
        reason=reason,
        actor_id=scope.user_id,
    ).insert()
    record.status = OfflinePaymentStatus.REVERSED
    await record.save()
    return {"reversal_id": reversal_id, "status": record.status.value}


async def offline_daily_report(scope: AccessScope, batch_date: date) -> dict:
    authorize_finance_offline_collect(scope)
    tenant_id = require_finance_tenant_scope(scope)
    records = await OfflinePaymentRecord.find(Eq(OfflinePaymentRecord.tenant_id, tenant_id)).to_list()
    day_rows = [r for r in records if r.payment_date == batch_date]
    return {
        "date": batch_date.isoformat(),
        "total_amount": round_money(sum(r.amount for r in day_rows)),
        "count": len(day_rows),
        "pending_verification": sum(1 for r in day_rows if r.status == OfflinePaymentStatus.AWAITING_VERIFICATION),
        "cheque_pending": sum(1 for r in day_rows if r.status == OfflinePaymentStatus.CHEQUE_PENDING),
    }


async def list_offline_payments(scope: AccessScope, pagination: Pagination, *, status: str | None = None) -> Page[dict]:
    authorize_finance_offline_collect(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query = OfflinePaymentRecord.find(Eq(OfflinePaymentRecord.tenant_id, tenant_id))
    if status:
        query = query.find(Eq(OfflinePaymentRecord.status, status))
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            {
                "record_id": r.record_id,
                "student_user_id": str(r.student_user_id),
                "amount": r.amount,
                "payment_method": r.payment_method.value,
                "status": r.status.value,
                "transaction_id": r.transaction_id,
            }
            for r in rows
        ],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


async def payment_history(scope: AccessScope, pagination: Pagination, *, student_user_id: str | None = None) -> Page[dict]:
    from app.modules.accounts_finance.policy import authorize_finance_payment_read

    authorize_finance_payment_read(scope)
    tenant_id = require_finance_tenant_scope(scope)
    query = PaymentTransaction.find(Eq(PaymentTransaction.tenant_id, tenant_id))
    if student_user_id:
        query = query.find(Eq(PaymentTransaction.student_user_id, to_object_id(student_user_id, "student_user_id")))
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            {
                "transaction_id": r.transaction_id,
                "student_user_id": str(r.student_user_id),
                "amount": r.amount,
                "status": r.status.value,
                "payment_mode": r.payment_mode,
                "gateway_reference": r.gateway_reference,
                "webhook_verified": r.webhook_verified,
                "created_at": r.created_at.isoformat(),
            }
            for r in rows
        ],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )