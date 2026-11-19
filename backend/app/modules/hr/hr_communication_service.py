"""HR notifications, announcements and delivery tracking."""

from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.hr.enums import HrAnnouncementStatus, HrNotificationDeliveryStatus
from app.modules.hr.hr_audience_resolver import resolve_hr_audience
from app.modules.hr.hr_communication_models import (
    HrAnnouncement,
    HrAnnouncementAudience,
    HrNotificationDeliveryHistory,
    HrNotificationPreference,
    HrNotificationTemplate,
)
from app.modules.hr.hr_communication_schemas import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementTransition,
    AudiencePreview,
    HrBroadcastCreate,
    InboxItemRead,
    NotificationDashboard,
    NotificationPreferenceUpsert,
    NotificationTemplateRead,
    NotificationTemplateUpsert,
)
from app.modules.hr.policy import (
    authorize_hr_notify_manage,
    authorize_hr_notify_read,
    require_employee_tenant_scope,
    require_hr_tenant_scope,
)
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def notification_dashboard(scope: AccessScope) -> NotificationDashboard:
    authorize_hr_notify_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    dash = NotificationDashboard()
    inbox = await HrNotificationDeliveryHistory.find(Eq(HrNotificationDeliveryHistory.tenant_id, tenant_id)).to_list()
    dash.total_notifications = len(inbox)
    dash.unread_notifications = sum(1 for n in inbox if n.status in {HrNotificationDeliveryStatus.QUEUED, HrNotificationDeliveryStatus.SENT, HrNotificationDeliveryStatus.DELIVERED})
    dash.sent_notifications = sum(1 for n in inbox if n.status in {HrNotificationDeliveryStatus.SENT, HrNotificationDeliveryStatus.DELIVERED, HrNotificationDeliveryStatus.READ})
    dash.failed_notifications = sum(1 for n in inbox if n.status == HrNotificationDeliveryStatus.FAILED)
    dash.pending_acknowledgements = sum(
        1 for n in inbox if n.requires_acknowledgement and n.status != HrNotificationDeliveryStatus.ACKNOWLEDGED
    )
    announcements = await HrAnnouncement.find(Eq(HrAnnouncement.tenant_id, tenant_id)).to_list()
    dash.published_announcements = sum(1 for a in announcements if a.status == HrAnnouncementStatus.PUBLISHED)
    dash.pending_announcements = sum(
        1 for a in announcements if a.status in {HrAnnouncementStatus.DRAFT, HrAnnouncementStatus.PENDING_REVIEW, HrAnnouncementStatus.APPROVED, HrAnnouncementStatus.SCHEDULED}
    )
    dash.scheduled_notifications = sum(1 for a in announcements if a.status == HrAnnouncementStatus.SCHEDULED)
    return dash


async def preview_audience(scope: AccessScope, audience: dict) -> AudiencePreview:
    authorize_hr_notify_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    users = await resolve_hr_audience(tenant_id, audience)
    return AudiencePreview(recipient_count=len(users), sample_user_ids=[str(u) for u in users[:20]])


async def upsert_template(scope: AccessScope, payload: NotificationTemplateUpsert) -> NotificationTemplateRead:
    authorize_hr_notify_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await HrNotificationTemplate.find_one(
        Eq(HrNotificationTemplate.tenant_id, tenant_id),
        Eq(HrNotificationTemplate.template_code, payload.template_code),
    )
    if doc:
        for k, v in payload.model_dump().items():
            setattr(doc, k, v)
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrNotificationTemplate(tenant_id=tenant_id, actor_id=scope.user_id, **payload.model_dump())
        await doc.insert()
    return NotificationTemplateRead.from_doc(doc)


async def list_templates(scope: AccessScope) -> list[NotificationTemplateRead]:
    authorize_hr_notify_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrNotificationTemplate.find(Eq(HrNotificationTemplate.tenant_id, tenant_id)).to_list()
    return [NotificationTemplateRead.from_doc(r) for r in rows]


async def create_announcement(scope: AccessScope, payload: AnnouncementCreate) -> AnnouncementRead:
    authorize_hr_notify_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    preview = await resolve_hr_audience(tenant_id, payload.audience)
    doc = HrAnnouncement(
        tenant_id=tenant_id,
        announcement_code=payload.announcement_code,
        title=payload.title,
        body=payload.body,
        category=payload.category,
        priority=payload.priority,
        audience=payload.audience,
        audience_preview_count=len(preview),
        channels=payload.channels,
        document_refs=payload.document_refs,
        publish_at=payload.publish_at,
        expires_at=payload.expires_at,
        pinned=payload.pinned,
        requires_acknowledgement=payload.requires_acknowledgement,
        actor_id=scope.user_id,
    )
    await doc.insert()
    return AnnouncementRead.from_doc(doc)


async def transition_announcement(scope: AccessScope, announcement_id: str, payload: AnnouncementTransition) -> AnnouncementRead:
    authorize_hr_notify_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(announcement_id, "announcement_id")
    doc = await HrAnnouncement.get(aid)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if payload.action == "submit":
        doc.status = HrAnnouncementStatus.PENDING_REVIEW
    elif payload.action == "approve":
        doc.status = HrAnnouncementStatus.APPROVED
        doc.reviewer_id = scope.user_id
    elif payload.action == "schedule":
        doc.status = HrAnnouncementStatus.SCHEDULED
    elif payload.action == "publish":
        doc.status = HrAnnouncementStatus.PUBLISHED
        doc.published_at = utcnow()
        await _fanout_announcement(scope, doc)
    elif payload.action == "withdraw":
        doc.status = HrAnnouncementStatus.WITHDRAWN
    else:
        doc.status = HrAnnouncementStatus.ARCHIVED
    doc.updated_at = utcnow()
    await doc.save()
    return AnnouncementRead.from_doc(doc)


async def _fanout_announcement(scope: AccessScope, doc: HrAnnouncement) -> int:
    users = await resolve_hr_audience(doc.tenant_id, doc.audience)
    sent = 0
    for uid in users:
        exists = await HrAnnouncementAudience.find_one(
            Eq(HrAnnouncementAudience.tenant_id, doc.tenant_id),
            Eq(HrAnnouncementAudience.announcement_id, doc.id),
            Eq(HrAnnouncementAudience.employee_user_id, uid),
        )
        if not exists:
            await HrAnnouncementAudience(tenant_id=doc.tenant_id, announcement_id=doc.id, employee_user_id=uid).insert()
        await _deliver_to_user(
            tenant_id=doc.tenant_id,
            sender_id=scope.user_id,
            recipient_user_id=uid,
            title=doc.title,
            body=doc.body,
            category=doc.category,
            priority=doc.priority,
            channels=doc.channels,
            requires_acknowledgement=doc.requires_acknowledgement,
            source_type="announcement",
            source_id=str(doc.id),
            dedupe_suffix=f"ann:{doc.id}",
        )
        sent += 1
    return sent


async def _deliver_to_user(
    *,
    tenant_id,
    sender_id,
    recipient_user_id,
    title: str,
    body: str,
    category: str,
    priority,
    channels: list[str],
    requires_acknowledgement: bool,
    source_type: str,
    source_id: str,
    dedupe_suffix: str,
) -> None:
    for channel in channels:
        dedupe = f"hr:notify:{recipient_user_id}:{dedupe_suffix}:{channel}"
        if await HrNotificationDeliveryHistory.find_one(
            Eq(HrNotificationDeliveryHistory.tenant_id, tenant_id),
            Eq(HrNotificationDeliveryHistory.dedupe_key, dedupe),
        ):
            continue
        pref = await HrNotificationPreference.find_one(
            Eq(HrNotificationPreference.tenant_id, tenant_id),
            Eq(HrNotificationPreference.user_id, recipient_user_id),
        )
        if pref and category in pref.categories_muted:
            continue
        if pref and channel in pref.channels_enabled and not pref.channels_enabled.get(channel, True):
            continue
        nid = f"hrn_{uuid4().hex[:12]}"
        status = HrNotificationDeliveryStatus.QUEUED
        if channel == "in_app":
            status = HrNotificationDeliveryStatus.DELIVERED
        row = HrNotificationDeliveryHistory(
            tenant_id=tenant_id,
            notification_id=nid,
            dedupe_key=dedupe,
            category=category,
            channel=channel,
            recipient_user_id=recipient_user_id,
            title=title,
            body=body,
            status=status,
            priority=priority,
            requires_acknowledgement=requires_acknowledgement,
            source_type=source_type,
            source_id=source_id,
            outbox_idempotency_key=dedupe,
            sender_id=sender_id,
        )
        await row.insert()
        if channel != "in_app":
            existing = await DomainOutboxEvent.find_one(
                Eq(DomainOutboxEvent.tenant_id, tenant_id),
                Eq(DomainOutboxEvent.idempotency_key, dedupe),
            )
            if existing:
                continue
            await DomainOutboxEvent(
                tenant_id=tenant_id,
                event_type=f"hr.notify.deliver.{channel}",
                aggregate_type="hr_notification",
                aggregate_id=nid,
                payload={
                    "title": title,
                    "body": body,
                    "recipient_user_id": str(recipient_user_id),
                    "channel": channel,
                    "notification_id": nid,
                },
                idempotency_key=dedupe,
                status=OutboxEventStatus.PENDING,
            ).insert()
            row.status = HrNotificationDeliveryStatus.SENT
            row.updated_at = utcnow()
            await row.save()


async def send_broadcast(scope: AccessScope, payload: HrBroadcastCreate) -> dict:
    authorize_hr_notify_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    title, body = payload.title, payload.body
    if payload.template_code:
        tpl = await HrNotificationTemplate.find_one(
            Eq(HrNotificationTemplate.tenant_id, tenant_id),
            Eq(HrNotificationTemplate.template_code, payload.template_code),
        )
        if tpl:
            title = tpl.title_pattern
            body = tpl.body_pattern
    users = await resolve_hr_audience(tenant_id, payload.audience)
    count = 0
    for uid in users:
        await _deliver_to_user(
            tenant_id=tenant_id,
            sender_id=scope.user_id,
            recipient_user_id=uid,
            title=title,
            body=body,
            category=payload.category,
            priority=payload.priority,
            channels=payload.channels,
            requires_acknowledgement=payload.requires_acknowledgement,
            source_type="broadcast",
            source_id=None,
            dedupe_suffix=f"bc:{uuid4().hex[:8]}",
        )
        count += 1
    return {"deliveries_queued": count}


async def upsert_preferences(scope: AccessScope, payload: NotificationPreferenceUpsert) -> dict:
    require_employee_tenant_scope(scope)
    tenant_id = scope.tenant_id
    doc = await HrNotificationPreference.find_one(
        Eq(HrNotificationPreference.tenant_id, tenant_id),
        Eq(HrNotificationPreference.user_id, scope.user_id),
    )
    if doc:
        doc.channels_enabled = payload.channels_enabled
        doc.categories_muted = payload.categories_muted
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = HrNotificationPreference(
            tenant_id=tenant_id,
            user_id=scope.user_id,
            channels_enabled=payload.channels_enabled,
            categories_muted=payload.categories_muted,
        )
        await doc.insert()
    return {"updated": True}


async def my_inbox(scope: AccessScope, unread_only: bool = False) -> list[InboxItemRead]:
    require_employee_tenant_scope(scope)
    tenant_id = scope.tenant_id
    filters = [
        Eq(HrNotificationDeliveryHistory.tenant_id, tenant_id),
        Eq(HrNotificationDeliveryHistory.recipient_user_id, scope.user_id),
        Eq(HrNotificationDeliveryHistory.channel, "in_app"),
    ]
    rows = await HrNotificationDeliveryHistory.find(*filters).sort(-HrNotificationDeliveryHistory.created_at).limit(100).to_list()
    if unread_only:
        rows = [r for r in rows if r.status not in {HrNotificationDeliveryStatus.READ, HrNotificationDeliveryStatus.ACKNOWLEDGED}]
    return [InboxItemRead.from_doc(r) for r in rows]


async def mark_notification_read(scope: AccessScope, notification_id: str) -> dict:
    require_employee_tenant_scope(scope)
    tenant_id = scope.tenant_id
    nid = to_object_id(notification_id, "notification_id")
    row = await HrNotificationDeliveryHistory.get(nid)
    if row is None or row.tenant_id != tenant_id or row.recipient_user_id != scope.user_id:
        raise AppError(code="FORBIDDEN", message="Notification access denied", status_code=403)
    row.status = HrNotificationDeliveryStatus.READ
    row.read_at = utcnow()
    row.updated_at = utcnow()
    await row.save()
    return {"status": row.status.value}


async def acknowledge_notification(scope: AccessScope, notification_id: str) -> dict:
    require_employee_tenant_scope(scope)
    tenant_id = scope.tenant_id
    nid = to_object_id(notification_id, "notification_id")
    row = await HrNotificationDeliveryHistory.get(nid)
    if row is None or row.tenant_id != tenant_id or row.recipient_user_id != scope.user_id:
        raise AppError(code="FORBIDDEN", message="Notification access denied", status_code=403)
    if not row.requires_acknowledgement:
        raise AppError(code="VALIDATION_ERROR", message="Acknowledgement not required", status_code=422)
    row.status = HrNotificationDeliveryStatus.ACKNOWLEDGED
    row.acknowledged_at = utcnow()
    row.updated_at = utcnow()
    await row.save()
    return {"status": row.status.value}


async def communication_history(scope: AccessScope, limit: int = 100) -> list[dict]:
    authorize_hr_notify_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrNotificationDeliveryHistory.find(Eq(HrNotificationDeliveryHistory.tenant_id, tenant_id)).sort(-HrNotificationDeliveryHistory.created_at).limit(limit).to_list()
    return [
        {
            "id": str(r.id),
            "recipient_user_id": str(r.recipient_user_id),
            "title": r.title,
            "category": r.category,
            "channel": r.channel,
            "status": r.status.value,
            "sender_id": str(r.sender_id) if r.sender_id else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]