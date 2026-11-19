"""Examination notification delivery via domain outbox and communication logs."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.college_admin.communication_admin_models import CommunicationDeliveryLog, DeliveryStatus
from app.modules.examinations.exam_cell_notification_enums import (
    ExamNotificationChannel,
    ExamNotificationDeliveryStatus,
)
from app.modules.examinations.exam_cell_notification_models import ExamNotificationDeliveryLog
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def enqueue_exam_delivery(
    tenant_id: PydanticObjectId,
    *,
    event_record_id: str,
    recipient_user_id: PydanticObjectId,
    channel: ExamNotificationChannel,
    title: str,
    body: str,
    dedupe_key: str,
) -> ExamNotificationDeliveryLog:
    delivery_id = f"endl_{uuid4().hex[:12]}"
    outbox_id: PydanticObjectId | None = None
    channel_key = f"{dedupe_key}:{channel.value}"
    existing_outbox = await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id),
        Eq(DomainOutboxEvent.idempotency_key, channel_key),
    )
    if existing_outbox is None:
        event = DomainOutboxEvent(
            tenant_id=tenant_id,
            event_type="examination.notification.dispatch",
            aggregate_type="exam_notification",
            aggregate_id=event_record_id,
            payload={
                "event_record_id": event_record_id,
                "recipient_user_id": str(recipient_user_id),
                "channel": channel.value,
                "title": title,
                "body": body,
            },
            idempotency_key=channel_key,
            status=OutboxEventStatus.PENDING,
        )
        await event.insert()
        outbox_id = event.id
    if channel in {ExamNotificationChannel.EMAIL, ExamNotificationChannel.SMS}:
        comm_key = f"exam_comm_{dedupe_key}_{channel.value}"
        if not await CommunicationDeliveryLog.find_one(
            Eq(CommunicationDeliveryLog.tenant_id, tenant_id),
            Eq(CommunicationDeliveryLog.log_id, comm_key),
        ):
            await CommunicationDeliveryLog(
                tenant_id=tenant_id,
                log_id=comm_key,
                announcement_id=event_record_id,
                channel=channel.value,
                recipient_user_id=recipient_user_id,
                status=DeliveryStatus.QUEUED,
            ).insert()
    delivery = ExamNotificationDeliveryLog(
        tenant_id=tenant_id,
        delivery_id=delivery_id,
        event_record_id=event_record_id,
        channel=channel.value,
        status=ExamNotificationDeliveryStatus.QUEUED.value,
        outbox_event_id=outbox_id,
    )
    await delivery.insert()
    return delivery


async def mark_exam_delivery_sent(delivery: ExamNotificationDeliveryLog) -> None:
    delivery.status = ExamNotificationDeliveryStatus.SENT.value
    delivery.updated_at = utcnow()
    await delivery.save()
    if delivery.outbox_event_id:
        event = await DomainOutboxEvent.get(delivery.outbox_event_id)
        if event:
            event.status = OutboxEventStatus.COMPLETED
            event.processed_at = utcnow()
            await event.save()


async def mark_exam_delivery_failed(delivery: ExamNotificationDeliveryLog, error: str) -> None:
    delivery.status = ExamNotificationDeliveryStatus.FAILED.value
    delivery.error = error[:500]
    delivery.retry_count += 1
    delivery.updated_at = utcnow()
    await delivery.save()
    if delivery.outbox_event_id:
        event = await DomainOutboxEvent.get(delivery.outbox_event_id)
        if event:
            event.status = OutboxEventStatus.FAILED
            event.processed_at = utcnow()
            await event.save()


async def process_pending_exam_deliveries(tenant_id: PydanticObjectId, *, limit: int = 50) -> dict[str, int]:
    rows = await ExamNotificationDeliveryLog.find(
        {
            "tenant_id": tenant_id,
            "status": {
                "$in": [
                    ExamNotificationDeliveryStatus.QUEUED.value,
                    ExamNotificationDeliveryStatus.RETRYING.value,
                ]
            },
        }
    ).limit(limit).to_list()
    sent = failed = 0
    for row in rows:
        if row.channel == ExamNotificationChannel.IN_APP.value:
            await mark_exam_delivery_sent(row)
            sent += 1
            continue
        if row.retry_count >= 3:
            await mark_exam_delivery_failed(row, "max_retries_exceeded")
            failed += 1
            continue
        await mark_exam_delivery_sent(row)
        sent += 1
    return {"processed": len(rows), "sent": sent, "failed": failed}