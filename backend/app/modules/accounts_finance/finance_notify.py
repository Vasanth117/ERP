"""Finance staff notification outbox (student / parent invoice issued)."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def enqueue_invoice_issued(
    tenant_id: PydanticObjectId,
    *,
    student_user_id: PydanticObjectId,
    invoice_id: str,
    invoice_number: str,
    amount: float,
) -> None:
    dedupe = f"finance:invoice_issued:{invoice_id}"
    if await DomainOutboxEvent.find_one(Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, dedupe)):
        return
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type="finance.invoice.issued",
        aggregate_type="student_fee_invoice",
        aggregate_id=invoice_id,
        payload={
            "student_user_id": str(student_user_id),
            "invoice_number": invoice_number,
            "amount": amount,
            "notify_parent": True,
        },
        idempotency_key=dedupe,
        status=OutboxEventStatus.PENDING,
    ).insert()


async def enqueue_receipt_issued(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    receipt_id: str,
) -> None:
    dedupe = f"finance:receipt_issued:{receipt_id}"
    if await DomainOutboxEvent.find_one(Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, dedupe)):
        return
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type="finance.receipt.issued",
        aggregate_type="payment_receipt",
        aggregate_id=receipt_id,
        payload={
            "student_user_id": str(student_user_id),
            "receipt_id": receipt_id,
            "notify_parent": True,
        },
        idempotency_key=dedupe,
        status=OutboxEventStatus.PENDING,
    ).insert()


async def enqueue_installment_plan_active(
    tenant_id: PydanticObjectId,
    student_user_id: PydanticObjectId,
    schedule_id: str,
) -> None:
    dedupe = f"finance:installment_active:{schedule_id}"
    if await DomainOutboxEvent.find_one(Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, dedupe)):
        return
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type="finance.installment.activated",
        aggregate_type="student_installment_schedule",
        aggregate_id=schedule_id,
        payload={"student_user_id": str(student_user_id), "schedule_id": schedule_id, "notify_parent": True},
        idempotency_key=dedupe,
        status=OutboxEventStatus.PENDING,
    ).insert()


async def enqueue_late_fee_applied(tenant_id: PydanticObjectId, count: int) -> None:
    dedupe = f"finance:late_fee_batch:{tenant_id}:{utcnow().date().isoformat()}"
    if await DomainOutboxEvent.find_one(Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, dedupe)):
        return
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type="finance.late_fee.batch",
        aggregate_type="late_fee_job",
        aggregate_id=str(tenant_id),
        payload={"generated_count": count},
        idempotency_key=dedupe,
        status=OutboxEventStatus.PENDING,
    ).insert()