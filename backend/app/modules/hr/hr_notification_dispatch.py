"""HR recruitment/onboarding notification enqueue via domain outbox."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def enqueue_hr_notification(
    tenant_id: PydanticObjectId,
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    title: str,
    body: str,
    recipient_email: str | None = None,
    recipient_user_id: PydanticObjectId | None = None,
    dedupe_key: str,
) -> bool:
    """Returns True if a new outbox event was created."""
    if await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id),
        Eq(DomainOutboxEvent.idempotency_key, dedupe_key),
    ):
        return False
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type=event_type,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        payload={
            "title": title,
            "body": body,
            "recipient_email": recipient_email,
            "recipient_user_id": str(recipient_user_id) if recipient_user_id else None,
            "notification_id": f"hrn_{uuid4().hex[:12]}",
        },
        idempotency_key=dedupe_key,
        status=OutboxEventStatus.PENDING,
    ).insert()
    return True