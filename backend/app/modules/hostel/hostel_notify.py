"""Hostel notification dispatch (domain outbox)."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def notify_hostel_student(
    tenant_id: PydanticObjectId,
    *,
    student_user_id: PydanticObjectId,
    event_type: str,
    title: str,
    body: str,
    aggregate_id: str,
) -> None:
    dedupe = f"hostel:{event_type}:{aggregate_id}:{student_user_id}"
    existing = await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id),
        Eq(DomainOutboxEvent.idempotency_key, dedupe),
    )
    if existing:
        return
    await DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type=f"hostel.{event_type}",
        aggregate_type="hostel_application",
        aggregate_id=aggregate_id,
        payload={
            "recipient_user_id": str(student_user_id),
            "title": title,
            "body": body,
        },
        idempotency_key=dedupe,
        status=OutboxEventStatus.PENDING,
    ).insert()
    try:
        from app.modules.hostel.communication_models import HostelNotificationPriority
        from app.modules.hostel.communication_service import deliver_hostel_notification

        category = event_type.split(".", 1)[0] if "." in event_type else "operations"
        await deliver_hostel_notification(
            tenant_id=tenant_id,
            sender_id=None,
            recipient_user_id=student_user_id,
            title=title,
            body=body,
            category=category,
            priority=HostelNotificationPriority.NORMAL,
            channels=["in_app"],
            requires_acknowledgement=False,
            source_type="operational",
            source_id=aggregate_id,
            dedupe_suffix=dedupe,
            related_record_type="hostel_event",
            related_record_id=aggregate_id,
        )
    except Exception:
        pass