"""Hostel communication, announcements and notification delivery."""

from __future__ import annotations

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.hostel.communication_models import (
    HostelAnnouncement,
    HostelAnnouncementAcknowledgement,
    HostelAnnouncementAudience,
    HostelAnnouncementStatus,
    HostelNotificationDeliveryHistory,
    HostelNotificationDeliveryStatus,
    HostelNotificationPriority,
    HostelNotificationTemplate,
)
from app.modules.hostel.communication_schemas import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementTransition,
    AudiencePreview,
    InboxAcknowledge,
    InboxItemRead,
    NotificationDashboard,
    NotificationTemplateRead,
    NotificationTemplateUpsert,
)
from app.modules.hostel.hostel_audience_resolver import resolve_hostel_audience
from app.modules.hostel.policy import authorize_hostel_notify_manage, authorize_hostel_notify_read, require_hostel_tenant_scope
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus


async def notification_dashboard(scope: AccessScope) -> NotificationDashboard:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_notify_read(scope)
    inbox = await HostelNotificationDeliveryHistory.find(Eq(HostelNotificationDeliveryHistory.tenant_id, tenant_id)).to_list()
    dash = NotificationDashboard()
    dash.total_notifications = len(inbox)
    dash.unread_notifications = sum(
        1
        for n in inbox
        if n.status in {HostelNotificationDeliveryStatus.QUEUED, HostelNotificationDeliveryStatus.SENT, HostelNotificationDeliveryStatus.DELIVERED}
    )
    dash.sent_notifications = sum(
        1
        for n in inbox
        if n.status
        in {
            HostelNotificationDeliveryStatus.SENT,
            HostelNotificationDeliveryStatus.DELIVERED,
            HostelNotificationDeliveryStatus.READ,
            HostelNotificationDeliveryStatus.ACKNOWLEDGED,
        }
    )
    dash.failed_notifications = sum(1 for n in inbox if n.status == HostelNotificationDeliveryStatus.FAILED)
    dash.pending_acknowledgements = sum(
        1 for n in inbox if n.requires_acknowledgement and n.status != HostelNotificationDeliveryStatus.ACKNOWLEDGED
    )
    dash.requires_action = sum(1 for n in inbox if n.requires_action and n.status != HostelNotificationDeliveryStatus.ACKNOWLEDGED)
    announcements = await HostelAnnouncement.find(Eq(HostelAnnouncement.tenant_id, tenant_id)).to_list()
    dash.published_announcements = sum(1 for a in announcements if a.status == HostelAnnouncementStatus.PUBLISHED)
    dash.draft_announcements = sum(
        1 for a in announcements if a.status in {HostelAnnouncementStatus.DRAFT, HostelAnnouncementStatus.PENDING_APPROVAL}
    )
    dash.scheduled_notifications = sum(1 for a in announcements if a.status == HostelAnnouncementStatus.SCHEDULED)
    return dash


async def preview_audience(scope: AccessScope, audience: dict) -> AudiencePreview:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_notify_manage(scope)
    users = await resolve_hostel_audience(tenant_id, audience)
    return AudiencePreview(recipient_count=len(users), sample_user_ids=[str(u) for u in users[:20]])


async def upsert_template(scope: AccessScope, payload: NotificationTemplateUpsert) -> NotificationTemplateRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_notify_manage(scope)
    code = payload.template_code.strip().upper()
    doc = await HostelNotificationTemplate.find_one(
        Eq(HostelNotificationTemplate.tenant_id, tenant_id), Eq(HostelNotificationTemplate.template_code, code)
    )
    if doc:
        doc.category = payload.category
        doc.title_pattern = payload.title_pattern
        doc.body_pattern = payload.body_pattern
        doc.default_channels = payload.default_channels
        doc.variables = payload.variables
        doc.requires_acknowledgement = payload.requires_acknowledgement
        doc.is_active = payload.is_active
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = await HostelNotificationTemplate(
            tenant_id=tenant_id,
            template_code=code,
            category=payload.category,
            title_pattern=payload.title_pattern,
            body_pattern=payload.body_pattern,
            default_channels=payload.default_channels,
            variables=payload.variables,
            requires_acknowledgement=payload.requires_acknowledgement,
            is_active=payload.is_active,
            actor_id=scope.user_id,
        ).insert()
    return NotificationTemplateRead(
        template_code=doc.template_code,
        category=doc.category,
        title_pattern=doc.title_pattern,
        body_pattern=doc.body_pattern,
        default_channels=doc.default_channels,
        is_active=doc.is_active,
    )


async def list_templates(scope: AccessScope) -> list[NotificationTemplateRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_notify_read(scope)
    rows = await HostelNotificationTemplate.find(Eq(HostelNotificationTemplate.tenant_id, tenant_id)).to_list()
    return [
        NotificationTemplateRead(
            template_code=r.template_code,
            category=r.category,
            title_pattern=r.title_pattern,
            body_pattern=r.body_pattern,
            default_channels=r.default_channels,
            is_active=r.is_active,
        )
        for r in rows
    ]


async def create_announcement(scope: AccessScope, payload: AnnouncementCreate) -> AnnouncementRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_notify_manage(scope)
    code = payload.announcement_code.strip().upper()
    if await HostelAnnouncement.find_one(Eq(HostelAnnouncement.tenant_id, tenant_id), Eq(HostelAnnouncement.announcement_code, code)):
        raise AppError(code="CONFLICT", message="Announcement code exists", status_code=409)
    preview_count = len(await resolve_hostel_audience(tenant_id, payload.audience))
    doc = await HostelAnnouncement(
        tenant_id=tenant_id,
        announcement_code=code,
        title=payload.title,
        body=payload.body,
        category=payload.category,
        priority=payload.priority,
        audience=payload.audience,
        audience_preview_count=preview_count,
        channels=payload.channels,
        document_refs=payload.document_refs,
        hostel_code=payload.hostel_code.upper() if payload.hostel_code else None,
        publish_at=payload.publish_at,
        expires_at=payload.expires_at,
        requires_acknowledgement=payload.requires_acknowledgement,
        requires_action=payload.requires_action,
        actor_id=scope.user_id,
    ).insert()
    return _ann_read(doc)


def _ann_read(doc: HostelAnnouncement) -> AnnouncementRead:
    return AnnouncementRead(
        announcement_code=doc.announcement_code,
        title=doc.title,
        status=doc.status,
        category=doc.category,
        priority=doc.priority,
        audience_preview_count=doc.audience_preview_count,
        published_at=doc.published_at,
        requires_acknowledgement=doc.requires_acknowledgement,
    )


async def transition_announcement(scope: AccessScope, announcement_code: str, payload: AnnouncementTransition) -> AnnouncementRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_notify_manage(scope)
    doc = await HostelAnnouncement.find_one(
        Eq(HostelAnnouncement.tenant_id, tenant_id), Eq(HostelAnnouncement.announcement_code, announcement_code.upper())
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if payload.action == "submit":
        doc.status = HostelAnnouncementStatus.PENDING_APPROVAL
    elif payload.action == "approve":
        doc.status = HostelAnnouncementStatus.APPROVED
        doc.reviewer_id = scope.user_id
    elif payload.action == "schedule":
        doc.status = HostelAnnouncementStatus.SCHEDULED
    elif payload.action == "publish":
        doc.status = HostelAnnouncementStatus.PUBLISHED
        doc.published_at = utcnow()
        await _fanout_announcement(scope, doc)
    elif payload.action == "withdraw":
        doc.status = HostelAnnouncementStatus.WITHDRAWN
    elif payload.action == "expire":
        doc.status = HostelAnnouncementStatus.EXPIRED
    else:
        doc.status = HostelAnnouncementStatus.ARCHIVED
    doc.updated_at = utcnow()
    await doc.save()
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action=f"hostel.announcement.{payload.action}",
        module="hostel_communication",
        resource_type="announcement",
        resource_id=doc.announcement_code,
    )
    return _ann_read(doc)


async def _fanout_announcement(scope: AccessScope, doc: HostelAnnouncement) -> int:
    users = await resolve_hostel_audience(doc.tenant_id, doc.audience)
    sent = 0
    for uid in users:
        if not await HostelAnnouncementAudience.find_one(
            {
                "tenant_id": doc.tenant_id,
                "announcement_code": doc.announcement_code,
                "student_user_id": uid,
            }
        ):
            await HostelAnnouncementAudience(
                tenant_id=doc.tenant_id,
                announcement_code=doc.announcement_code,
                student_user_id=uid,
            ).insert()
        await deliver_hostel_notification(
            tenant_id=doc.tenant_id,
            sender_id=scope.user_id,
            recipient_user_id=uid,
            title=doc.title,
            body=doc.body,
            category=doc.category,
            priority=doc.priority,
            channels=doc.channels,
            requires_acknowledgement=doc.requires_acknowledgement,
            requires_action=doc.requires_action,
            source_type="announcement",
            source_id=doc.announcement_code,
            dedupe_suffix=f"ann:{doc.announcement_code}",
        )
        sent += 1
    return sent


async def deliver_hostel_notification(
    *,
    tenant_id: PydanticObjectId,
    sender_id: PydanticObjectId | None,
    recipient_user_id: PydanticObjectId,
    title: str,
    body: str,
    category: str,
    priority: HostelNotificationPriority,
    channels: list[str],
    requires_acknowledgement: bool,
    requires_action: bool = False,
    source_type: str,
    source_id: str,
    dedupe_suffix: str,
    related_record_type: str | None = None,
    related_record_id: str | None = None,
) -> None:
    for channel in channels:
        dedupe = f"hostel:notify:{recipient_user_id}:{dedupe_suffix}:{channel}"
        if await HostelNotificationDeliveryHistory.find_one(
            Eq(HostelNotificationDeliveryHistory.tenant_id, tenant_id), Eq(HostelNotificationDeliveryHistory.dedupe_key, dedupe)
        ):
            continue
        nid = f"hnt_{uuid4().hex[:12]}"
        status = HostelNotificationDeliveryStatus.DELIVERED if channel == "in_app" else HostelNotificationDeliveryStatus.QUEUED
        await HostelNotificationDeliveryHistory(
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
            requires_action=requires_action,
            source_type=source_type,
            source_id=source_id,
            related_record_type=related_record_type,
            related_record_id=related_record_id,
            outbox_idempotency_key=dedupe,
            sender_id=sender_id,
        ).insert()
        if channel != "in_app":
            if await DomainOutboxEvent.find_one(Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, dedupe)):
                continue
            await DomainOutboxEvent(
                tenant_id=tenant_id,
                event_type=f"hostel.notify.{channel}",
                aggregate_type="hostel_notification",
                aggregate_id=nid,
                payload={
                    "recipient_user_id": str(recipient_user_id),
                    "title": title,
                    "body": body,
                    "category": category,
                },
                idempotency_key=dedupe,
                status=OutboxEventStatus.PENDING,
            ).insert()


async def student_inbox(scope: AccessScope, user: User, pagination: Pagination) -> Page[InboxItemRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    q = {"tenant_id": tenant_id, "recipient_user_id": user.id}
    total = await HostelNotificationDeliveryHistory.find(q).count()
    skip = (pagination.page - 1) * pagination.page_size
    rows = await HostelNotificationDeliveryHistory.find(q).sort("-created_at").skip(skip).limit(pagination.page_size).to_list()
    items = [
        InboxItemRead(
            notification_id=r.notification_id,
            title=r.title,
            body=r.body,
            category=r.category,
            status=r.status,
            requires_acknowledgement=r.requires_acknowledgement,
            read_at=r.read_at,
            acknowledged_at=r.acknowledged_at,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, page=pagination.page, page_size=pagination.page_size)


async def mark_inbox_read(scope: AccessScope, user: User, notification_id: str) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    row = await HostelNotificationDeliveryHistory.find_one(
        Eq(HostelNotificationDeliveryHistory.tenant_id, tenant_id),
        Eq(HostelNotificationDeliveryHistory.notification_id, notification_id),
        Eq(HostelNotificationDeliveryHistory.recipient_user_id, user.id),
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Notification not found", status_code=404)
    row.read_at = utcnow()
    if row.status == HostelNotificationDeliveryStatus.DELIVERED:
        row.status = HostelNotificationDeliveryStatus.READ
    row.updated_at = utcnow()
    await row.save()
    return {"notification_id": notification_id}


async def acknowledge_inbox(scope: AccessScope, user: User, payload: InboxAcknowledge) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    row = await HostelNotificationDeliveryHistory.find_one(
        Eq(HostelNotificationDeliveryHistory.tenant_id, tenant_id),
        Eq(HostelNotificationDeliveryHistory.notification_id, payload.notification_id),
        Eq(HostelNotificationDeliveryHistory.recipient_user_id, user.id),
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Notification not found", status_code=404)
    if not row.requires_acknowledgement:
        raise AppError(code="VALIDATION_ERROR", message="Acknowledgement not required", status_code=422)
    row.acknowledged_at = utcnow()
    row.status = HostelNotificationDeliveryStatus.ACKNOWLEDGED
    row.updated_at = utcnow()
    await row.save()
    if row.source_type == "announcement" and row.source_id:
        exists = await HostelAnnouncementAcknowledgement.find_one(
            {
                "tenant_id": tenant_id,
                "announcement_code": row.source_id,
                "student_user_id": user.id,
            }
        )
        if not exists:
            await HostelAnnouncementAcknowledgement(
                tenant_id=tenant_id,
                announcement_code=row.source_id,
                student_user_id=user.id,
            ).insert()
    return {"notification_id": payload.notification_id}


async def run_reminder_scan(scope: AccessScope) -> dict:
    """Enqueue deduped reminders for overdue operational items."""
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_notify_manage(scope)
    from app.modules.hostel.leave_outpass_models import HostelLeaveOutpassStatus, HostelOutpassRequest
    from app.modules.hostel.rules_incident_models import HostelRule, HostelRuleAcknowledgement

    sent = 0
    now = utcnow()
    overdue = await HostelOutpassRequest.find(
        {"tenant_id": tenant_id, "status": HostelLeaveOutpassStatus.OVERDUE.value}
    ).to_list()
    for row in overdue:
        await deliver_hostel_notification(
            tenant_id=tenant_id,
            sender_id=scope.user_id,
            recipient_user_id=row.student_user_id,
            title="Overdue return reminder",
            body=f"Your outpass {row.request_id} is overdue. Please return immediately.",
            category="leave_outpass",
            priority=HostelNotificationPriority.HIGH,
            channels=["in_app"],
            requires_acknowledgement=False,
            source_type="reminder",
            source_id=row.request_id,
            dedupe_suffix=f"reminder:outpass_overdue:{row.request_id}",
        )
        sent += 1

    rules = await HostelRule.find({"tenant_id": tenant_id, "published": True, "requires_acknowledgement": True}).to_list()
    from app.modules.hostel.resident_models import HostelResident, HostelResidentStatus

    residents = await HostelResident.find(
        {"tenant_id": tenant_id, "status": {"$in": [HostelResidentStatus.CHECKED_IN.value]}}
    ).to_list()
    for rule in rules:
        for res in residents:
            ack = await HostelRuleAcknowledgement.find_one(
                {"tenant_id": tenant_id, "rule_code": rule.rule_code, "student_user_id": res.student_user_id, "rule_version": rule.version}
            )
            if ack:
                continue
            await deliver_hostel_notification(
                tenant_id=tenant_id,
                sender_id=scope.user_id,
                recipient_user_id=res.student_user_id,
                title="Rule acknowledgement reminder",
                body=f"Please acknowledge hostel rule: {rule.title}",
                category="rules",
                priority=HostelNotificationPriority.NORMAL,
                channels=["in_app"],
                requires_acknowledgement=True,
                source_type="reminder",
                source_id=rule.rule_code,
                dedupe_suffix=f"reminder:rule_ack:{rule.rule_code}:v{rule.version}",
            )
            sent += 1
    return {"reminders_enqueued": sent, "scanned_at": now.isoformat()}