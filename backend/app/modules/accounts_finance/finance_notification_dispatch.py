"""Finance notifications via domain outbox (reuses central messaging infrastructure)."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.time import utcnow
from app.modules.accounts_finance.phase11_enums import FinanceNotificationStatus
from app.modules.accounts_finance.phase11_models import (
    FinanceNotificationEvent,
    FinanceNotificationFailure,
    FinanceNotificationHistory,
)
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def enqueue_finance_notification(
    tenant_id: PydanticObjectId,
    *,
    category: str,
    recipient_user_id: PydanticObjectId | None,
    title: str,
    body: str,
    reference_type: str | None,
    reference_id: str | None,
    dedupe_key: str,
    channel: str = "in_app",
    metadata: dict | None = None,
) -> FinanceNotificationEvent:
    existing = await FinanceNotificationEvent.find_one(
        Eq(FinanceNotificationEvent.tenant_id, tenant_id),
        Eq(FinanceNotificationEvent.dedupe_key, dedupe_key),
    )
    if existing:
        return existing
    notification_id = f"fn_{uuid4().hex[:12]}"
    event = FinanceNotificationEvent(
        tenant_id=tenant_id,
        notification_id=notification_id,
        category=category,
        recipient_user_id=recipient_user_id,
        title=title,
        body=body,
        reference_type=reference_type,
        reference_id=reference_id,
        dedupe_key=dedupe_key,
        status=FinanceNotificationStatus.QUEUED.value,
        channel=channel,
        metadata=metadata or {},
    )
    await event.insert()
    outbox_key = f"finance:notify:{dedupe_key}:{channel}"
    if not await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id),
        Eq(DomainOutboxEvent.idempotency_key, outbox_key),
    ):
        await DomainOutboxEvent(
            tenant_id=tenant_id,
            event_type="finance.notification.dispatch",
            aggregate_type="finance_notification",
            aggregate_id=notification_id,
            payload={
                "notification_id": notification_id,
                "category": category,
                "recipient_user_id": str(recipient_user_id) if recipient_user_id else None,
                "channel": channel,
                "title": title,
                "body": body,
            },
            idempotency_key=outbox_key,
            status=OutboxEventStatus.PENDING,
        ).insert()
    await FinanceNotificationHistory(
        tenant_id=tenant_id,
        history_id=f"fnh_{uuid4().hex[:12]}",
        notification_id=notification_id,
        status=FinanceNotificationStatus.QUEUED.value,
        detail="Queued to domain outbox",
    ).insert()
    return event


async def mark_finance_notification_sent(tenant_id, notification_id: str) -> None:
    doc = await FinanceNotificationEvent.find_one(
        Eq(FinanceNotificationEvent.tenant_id, tenant_id),
        Eq(FinanceNotificationEvent.notification_id, notification_id),
    )
    if doc is None:
        return
    doc.status = FinanceNotificationStatus.SENT.value
    doc.updated_at = utcnow()
    await doc.save()


async def mark_finance_notification_failed(tenant_id, notification_id: str, error: str) -> None:
    doc = await FinanceNotificationEvent.find_one(
        Eq(FinanceNotificationEvent.tenant_id, tenant_id),
        Eq(FinanceNotificationEvent.notification_id, notification_id),
    )
    if doc:
        doc.status = FinanceNotificationStatus.FAILED.value
        doc.updated_at = utcnow()
        await doc.save()
    await FinanceNotificationFailure(
        tenant_id=tenant_id,
        failure_id=f"fnf_{uuid4().hex[:12]}",
        notification_id=notification_id,
        error=error[:500],
        retry_count=1,
    ).insert()