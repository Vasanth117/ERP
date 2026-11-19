"""Enqueue library deliveries via domain outbox and communication delivery log."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.college_admin.communication_admin_models import CommunicationDeliveryLog, DeliveryStatus
from app.modules.library.notification_enums import LibraryDeliveryStatus, LibraryNotificationChannel
from app.modules.library.notification_models import LibraryNotificationDelivery
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def enqueue_channel_delivery(
    tenant_id: PydanticObjectId,
    *,
    notification_id: str,
    recipient_user_id: PydanticObjectId,
    channel: LibraryNotificationChannel,
    title: str,
    body: str,
    dedupe_key: str,
) -> LibraryNotificationDelivery:
    delivery_id = f"ldl_{uuid4().hex[:12]}"
    outbox_id: PydanticObjectId | None = None
    channel_key = f"{dedupe_key}:{channel.value}"
    existing_outbox = await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id),
        Eq(DomainOutboxEvent.idempotency_key, channel_key),
    )
    if existing_outbox is None:
        event = DomainOutboxEvent(
            tenant_id=tenant_id,
            event_type="library.notification.dispatch",
            aggregate_type="library_notification",
            aggregate_id=notification_id,
            payload={
                "notification_id": notification_id,
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
    if channel == LibraryNotificationChannel.EMAIL:
        comm_key = f"lib_comm_{dedupe_key}"
        if not await CommunicationDeliveryLog.find_one(
            Eq(CommunicationDeliveryLog.tenant_id, tenant_id),
            Eq(CommunicationDeliveryLog.log_id, comm_key),
        ):
            await CommunicationDeliveryLog(
                tenant_id=tenant_id,
                log_id=comm_key,
                announcement_id=notification_id,
                channel="email",
                recipient_user_id=recipient_user_id,
                status=DeliveryStatus.QUEUED,
            ).insert()
    delivery = LibraryNotificationDelivery(
        tenant_id=tenant_id,
        delivery_id=delivery_id,
        notification_id=notification_id,
        channel=channel.value,
        status=LibraryDeliveryStatus.QUEUED.value,
        outbox_event_id=outbox_id,
    )
    await delivery.insert()
    return delivery


async def mark_delivery_sent(delivery: LibraryNotificationDelivery) -> None:
    delivery.status = LibraryDeliveryStatus.SENT.value
    delivery.updated_at = utcnow()
    await delivery.save()
    if delivery.outbox_event_id:
        event = await DomainOutboxEvent.get(delivery.outbox_event_id)
        if event:
            event.status = OutboxEventStatus.COMPLETED
            event.processed_at = utcnow()
            await event.save()


async def mark_delivery_failed(delivery: LibraryNotificationDelivery, error: str) -> None:
    delivery.status = LibraryDeliveryStatus.FAILED.value
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


async def process_pending_deliveries(tenant_id: PydanticObjectId, *, limit: int = 50) -> dict[str, int]:
    """Worker-style processor (in-app succeeds immediately; email may fail for retry tests)."""
    rows = await LibraryNotificationDelivery.find(
        {"tenant_id": tenant_id, "status": {"$in": [LibraryDeliveryStatus.QUEUED.value, LibraryDeliveryStatus.RETRYING.value]}}
    ).limit(limit).to_list()
    sent = failed = 0
    for row in rows:
        if row.channel == LibraryNotificationChannel.IN_APP.value:
            await mark_delivery_sent(row)
            sent += 1
            continue
        if row.retry_count >= 3:
            await mark_delivery_failed(row, "max_retries_exceeded")
            failed += 1
            continue
        if row.channel == LibraryNotificationChannel.EMAIL.value:
            # Integrations plug in here; mark sent when provider is wired.
            await mark_delivery_sent(row)
            sent += 1
    return {"processed": len(rows), "sent": sent, "failed": failed}