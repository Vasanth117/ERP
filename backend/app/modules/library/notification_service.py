"""Library notifications and communication."""

from datetime import date, timedelta
from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.library_admin_models import LibraryMembershipReference
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryReservationStatus
from app.modules.library.library_models import LibraryCirculation, LibraryFine, LibraryReservation
from app.modules.library.member_enums import LibraryMemberStatus
from app.modules.library.notification_access import (
    authorize_notification_manage,
    authorize_notification_publish,
    authorize_notification_read,
    authorize_notification_run,
)
from app.modules.library.notification_dispatch import (
    enqueue_channel_delivery,
    mark_delivery_failed,
    mark_delivery_sent,
    process_pending_deliveries,
)
from app.modules.library.notification_enums import (
    LibraryDeliveryStatus,
    LibraryNotificationChannel,
    LibraryNotificationEvent,
)
from app.modules.library.notification_models import (
    LibraryAnnouncement,
    LibraryNotification,
    LibraryNotificationDelivery,
    LibraryNotificationPreference,
)
from app.modules.library.notification_schemas import (
    LibraryAnnouncementCreate,
    LibraryAnnouncementRead,
    LibraryNotificationPreferenceRead,
    LibraryNotificationPreferenceUpdate,
    LibraryNotificationRead,
    ManualNotificationRequest,
    NotificationDeliveryRead,
)
from app.modules.library.notification_templates import render_library_notification
from app.modules.library.policy import require_library_tenant_scope
from app.modules.library.reservation_models import LibraryReservationNotification

_EVENT_PREF: dict[LibraryNotificationEvent, str] = {
    LibraryNotificationEvent.ISSUE: "issue_enabled",
    LibraryNotificationEvent.RETURN_REMINDER: "due_reminder_enabled",
    LibraryNotificationEvent.DUE_UPCOMING: "due_reminder_enabled",
    LibraryNotificationEvent.OVERDUE: "overdue_enabled",
    LibraryNotificationEvent.RESERVATION_READY: "reservation_enabled",
    LibraryNotificationEvent.RESERVATION_EXPIRY: "reservation_enabled",
    LibraryNotificationEvent.FINE: "fine_enabled",
    LibraryNotificationEvent.MEMBERSHIP_EXPIRY: "membership_enabled",
    LibraryNotificationEvent.ANNOUNCEMENT: "announcement_enabled",
}


def _notification_id() -> str:
    return f"lnt_{uuid4().hex[:12]}"


async def _validate_recipient(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> User:
    user = await User.find_one(Eq(User.id, user_id))
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Recipient not in tenant", status_code=422)
    if not user.is_active:
        raise AppError(code="VALIDATION_ERROR", message="Recipient account inactive", status_code=422)
    return user


async def _prefs(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> LibraryNotificationPreference:
    row = await LibraryNotificationPreference.find_one(
        Eq(LibraryNotificationPreference.tenant_id, tenant_id),
        Eq(LibraryNotificationPreference.user_id, user_id),
    )
    if row is None:
        row = LibraryNotificationPreference(tenant_id=tenant_id, user_id=user_id)
        await row.insert()
    return row


def _event_allowed(prefs: LibraryNotificationPreference, event: LibraryNotificationEvent) -> bool:
    field = _EVENT_PREF.get(event)
    if not field:
        return True
    return bool(getattr(prefs, field, True))


async def emit_library_notification(
    tenant_id: PydanticObjectId,
    *,
    event_type: LibraryNotificationEvent,
    recipient_user_id: PydanticObjectId,
    dedupe_key: str,
    template_kwargs: dict[str, str],
    branch_code: str | None = None,
    reference_type: str | None = None,
    reference_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    reservation_compat: tuple[str, str, str] | None = None,
) -> LibraryNotification | None:
    """Idempotent library notification emit with delivery queue."""
    if await LibraryNotification.find_one(
        Eq(LibraryNotification.tenant_id, tenant_id),
        Eq(LibraryNotification.dedupe_key, dedupe_key),
    ):
        return None
    await _validate_recipient(tenant_id, recipient_user_id)
    prefs = await _prefs(tenant_id, recipient_user_id)
    if not _event_allowed(prefs, event_type):
        return None
    title, body = render_library_notification(event_type, **template_kwargs)
    nid = _notification_id()
    doc = LibraryNotification(
        tenant_id=tenant_id,
        notification_id=nid,
        event_type=event_type.value,
        recipient_user_id=recipient_user_id,
        branch_code=branch_code.strip().upper() if branch_code else None,
        title=title[:200],
        body=body[:4000],
        reference_type=reference_type,
        reference_id=reference_id,
        dedupe_key=dedupe_key,
        metadata=metadata or {},
    )
    await doc.insert()
    channels: list[LibraryNotificationChannel] = [LibraryNotificationChannel.IN_APP]
    if prefs.email_enabled and event_type != LibraryNotificationEvent.ANNOUNCEMENT:
        channels.append(LibraryNotificationChannel.EMAIL)
    if event_type == LibraryNotificationEvent.ANNOUNCEMENT and prefs.email_enabled:
        channels.append(LibraryNotificationChannel.EMAIL)
    for channel in channels:
        if channel == LibraryNotificationChannel.IN_APP and not prefs.in_app_enabled:
            await LibraryNotificationDelivery(
                tenant_id=tenant_id,
                delivery_id=f"ldl_{uuid4().hex[:10]}",
                notification_id=nid,
                channel=channel.value,
                status=LibraryDeliveryStatus.SKIPPED.value,
            ).insert()
            continue
        if channel == LibraryNotificationChannel.EMAIL and not prefs.email_enabled:
            continue
        await enqueue_channel_delivery(
            tenant_id,
            notification_id=nid,
            recipient_user_id=recipient_user_id,
            channel=channel,
            title=title,
            body=body,
            dedupe_key=dedupe_key,
        )
    if reservation_compat:
        rsv_id, res_id, member_id = reservation_compat
        await LibraryReservationNotification(
            tenant_id=tenant_id,
            notification_id=rsv_id,
            reservation_id=res_id,
            member_user_id=recipient_user_id,
            title=title[:200],
            body=body[:2000],
        ).insert()
    await process_pending_deliveries(tenant_id, limit=10)
    return doc


async def get_preferences(scope: AccessScope, user_id: str) -> LibraryNotificationPreferenceRead:
    authorize_notification_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    uid = PydanticObjectId(user_id)
    await _validate_recipient(tenant_id, uid)
    prefs = await _prefs(tenant_id, uid)
    return LibraryNotificationPreferenceRead.model_validate(prefs, from_attributes=True)


async def update_preferences(
    scope: AccessScope,
    user_id: str,
    payload: LibraryNotificationPreferenceUpdate,
) -> LibraryNotificationPreferenceRead:
    authorize_notification_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    uid = PydanticObjectId(user_id)
    await _validate_recipient(tenant_id, uid)
    prefs = await _prefs(tenant_id, uid)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(prefs, key, value)
    prefs.updated_at = utcnow()
    await prefs.save()
    return LibraryNotificationPreferenceRead.model_validate(prefs, from_attributes=True)


async def search_notifications(
    scope: AccessScope,
    pagination: Pagination,
    *,
    recipient_user_id: str | None = None,
    branch_code: str | None = None,
    event_type: str | None = None,
) -> Page[LibraryNotificationRead]:
    authorize_notification_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if recipient_user_id:
        filters["recipient_user_id"] = PydanticObjectId(recipient_user_id)
    if branch_code:
        filters["branch_code"] = branch_code.strip().upper()
    if event_type:
        filters["event_type"] = event_type
    query = LibraryNotification.find(filters).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[LibraryNotificationRead.model_validate(r, from_attributes=True) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def notification_deliveries(scope: AccessScope, notification_id: str) -> list[NotificationDeliveryRead]:
    authorize_notification_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    rows = await LibraryNotificationDelivery.find(
        Eq(LibraryNotificationDelivery.tenant_id, tenant_id),
        Eq(LibraryNotificationDelivery.notification_id, notification_id),
    ).to_list()
    return [NotificationDeliveryRead.model_validate(r, from_attributes=True) for r in rows]


async def retry_notification_delivery(scope: AccessScope, delivery_id: str) -> NotificationDeliveryRead:
    authorize_notification_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    row = await LibraryNotificationDelivery.find_one(
        Eq(LibraryNotificationDelivery.tenant_id, tenant_id),
        Eq(LibraryNotificationDelivery.delivery_id, delivery_id),
    )
    if row is None:
        raise AppError(code="NOT_FOUND", message="Delivery not found", status_code=404)
    if row.status != LibraryDeliveryStatus.FAILED.value:
        raise AppError(code="CONFLICT", message="Only failed deliveries can be retried", status_code=409)
    row.status = LibraryDeliveryStatus.RETRYING.value
    row.updated_at = utcnow()
    await row.save()
    await mark_delivery_sent(row)
    return NotificationDeliveryRead.model_validate(row, from_attributes=True)


async def send_manual_notification(scope: AccessScope, payload: ManualNotificationRequest) -> LibraryNotificationRead:
    authorize_notification_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    dedupe = payload.dedupe_key or f"manual:{payload.recipient_user_id}:{uuid4().hex[:8]}"
    doc = await emit_library_notification(
        tenant_id,
        event_type=LibraryNotificationEvent.ANNOUNCEMENT,
        recipient_user_id=PydanticObjectId(payload.recipient_user_id),
        dedupe_key=dedupe,
        template_kwargs={"title": payload.title, "body": payload.body},
        branch_code=payload.branch_code,
        reference_type="manual",
        reference_id=dedupe,
    )
    if doc is None:
        raise AppError(code="CONFLICT", message="Duplicate notification", status_code=409)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_notification.manual",
        module="library_notification",
        resource_type="notification",
        resource_id=doc.notification_id,
    )
    return LibraryNotificationRead.model_validate(doc, from_attributes=True)


async def create_library_announcement(scope: AccessScope, payload: LibraryAnnouncementCreate) -> LibraryAnnouncementRead:
    authorize_notification_manage(scope)
    tenant_id = require_library_tenant_scope(scope)
    aid = payload.announcement_id or f"la_{uuid4().hex[:10]}"
    if await LibraryAnnouncement.find_one(
        Eq(LibraryAnnouncement.tenant_id, tenant_id),
        Eq(LibraryAnnouncement.announcement_id, aid),
    ):
        raise AppError(code="CONFLICT", message="Announcement id exists", status_code=409)
    doc = LibraryAnnouncement(
        tenant_id=tenant_id,
        announcement_id=aid,
        branch_code=payload.branch_code.strip().upper() if payload.branch_code else None,
        title=payload.title.strip(),
        body=payload.body.strip(),
        created_by=scope.user_id,
    )
    await doc.insert()
    return LibraryAnnouncementRead.model_validate(doc, from_attributes=True)


async def publish_library_announcement(scope: AccessScope, announcement_id: str) -> dict:
    authorize_notification_publish(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryAnnouncement.find_one(
        Eq(LibraryAnnouncement.tenant_id, tenant_id),
        Eq(LibraryAnnouncement.announcement_id, announcement_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status == "published":
        raise AppError(code="CONFLICT", message="Already published", status_code=409)
    doc.status = "published"
    doc.published_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    filters: dict[str, Any] = {"tenant_id": tenant_id, "status": LibraryMemberStatus.ACTIVE.value, "eligible": True}
    if doc.branch_code:
        filters["branch_code"] = doc.branch_code
    members = await LibraryMembershipReference.find(filters).to_list()
    sent = 0
    for m in members:
        key = f"announce:{announcement_id}:{m.member_user_id}"
        created = await emit_library_notification(
            tenant_id,
            event_type=LibraryNotificationEvent.ANNOUNCEMENT,
            recipient_user_id=m.member_user_id,
            dedupe_key=key,
            template_kwargs={"title": doc.title, "body": doc.body},
            branch_code=doc.branch_code,
            reference_type="announcement",
            reference_id=announcement_id,
        )
        if created:
            sent += 1
    return {"announcement_id": announcement_id, "notifications_sent": sent}


async def run_notification_batch(scope: AccessScope, *, branch_code: str | None = None) -> dict[str, int]:
    authorize_notification_run(scope)
    tenant_id = require_library_tenant_scope(scope)
    counts = {
        "due_upcoming": await _batch_due_upcoming(tenant_id, branch_code=branch_code),
        "overdue": await _batch_overdue(tenant_id, branch_code=branch_code),
        "return_reminder": await _batch_return_reminders(tenant_id, branch_code=branch_code),
        "reservation_expiry": await _batch_reservation_expiry(tenant_id, branch_code=branch_code),
        "membership_expiry": await _batch_membership_expiry(tenant_id, branch_code=branch_code),
    }
    dispatch = await process_pending_deliveries(tenant_id, limit=200)
    counts.update(dispatch)
    return counts


async def _batch_due_upcoming(tenant_id: PydanticObjectId, *, branch_code: str | None) -> int:
    window_end = date.today() + timedelta(days=2)
    filters: dict[str, Any] = {
        "tenant_id": tenant_id,
        "status": LibraryCirculationStatus.ACTIVE.value,
        "due_at": {"$lte": window_end, "$gte": date.today()},
    }
    if branch_code:
        filters["branch_code"] = branch_code.strip().upper()
    rows = await LibraryCirculation.find(filters).to_list()
    sent = 0
    for c in rows:
        key = f"due_upcoming:{c.circulation_id}:{date.today().isoformat()}"
        doc = await emit_library_notification(
            tenant_id,
            event_type=LibraryNotificationEvent.DUE_UPCOMING,
            recipient_user_id=c.student_user_id,
            dedupe_key=key,
            template_kwargs={"title": c.title, "due_date": c.due_at.isoformat()},
            branch_code=c.branch_code,
            reference_type="circulation",
            reference_id=c.circulation_id,
        )
        if doc:
            sent += 1
    return sent


async def _batch_return_reminders(tenant_id: PydanticObjectId, *, branch_code: str | None) -> int:
    target = date.today() + timedelta(days=1)
    filters: dict[str, Any] = {
        "tenant_id": tenant_id,
        "status": LibraryCirculationStatus.ACTIVE.value,
        "due_at": target,
    }
    if branch_code:
        filters["branch_code"] = branch_code.strip().upper()
    rows = await LibraryCirculation.find(filters).to_list()
    sent = 0
    for c in rows:
        key = f"return_reminder:{c.circulation_id}:{target.isoformat()}"
        doc = await emit_library_notification(
            tenant_id,
            event_type=LibraryNotificationEvent.RETURN_REMINDER,
            recipient_user_id=c.student_user_id,
            dedupe_key=key,
            template_kwargs={"title": c.title, "due_date": c.due_at.isoformat()},
            branch_code=c.branch_code,
            reference_type="circulation",
            reference_id=c.circulation_id,
        )
        if doc:
            sent += 1
    return sent


async def _batch_overdue(tenant_id: PydanticObjectId, *, branch_code: str | None) -> int:
    filters: dict[str, Any] = {
        "tenant_id": tenant_id,
        "status": {"$in": [LibraryCirculationStatus.ACTIVE.value, LibraryCirculationStatus.OVERDUE.value]},
        "due_at": {"$lt": date.today()},
    }
    if branch_code:
        filters["branch_code"] = branch_code.strip().upper()
    rows = await LibraryCirculation.find(filters).to_list()
    sent = 0
    for c in rows:
        key = f"overdue:{c.circulation_id}:{date.today().isoformat()}"
        doc = await emit_library_notification(
            tenant_id,
            event_type=LibraryNotificationEvent.OVERDUE,
            recipient_user_id=c.student_user_id,
            dedupe_key=key,
            template_kwargs={"title": c.title, "due_date": c.due_at.isoformat()},
            branch_code=c.branch_code,
            reference_type="circulation",
            reference_id=c.circulation_id,
        )
        if doc:
            sent += 1
    return sent


async def _batch_reservation_expiry(tenant_id: PydanticObjectId, *, branch_code: str | None) -> int:
    horizon = utcnow() + timedelta(hours=24)
    filters: dict[str, Any] = {
        "tenant_id": tenant_id,
        "status": LibraryReservationStatus.READY.value,
        "pickup_expires_at": {"$lte": horizon},
    }
    if branch_code:
        filters["branch_code"] = branch_code.strip().upper()
    rows = await LibraryReservation.find(filters).to_list()
    sent = 0
    for r in rows:
        exp = r.pickup_expires_at.isoformat() if r.pickup_expires_at else ""
        key = f"reservation_expiry:{r.reservation_id}:{exp[:10]}"
        doc = await emit_library_notification(
            tenant_id,
            event_type=LibraryNotificationEvent.RESERVATION_EXPIRY,
            recipient_user_id=r.student_user_id,
            dedupe_key=key,
            template_kwargs={"title": r.title, "expires_at": exp},
            branch_code=r.branch_code,
            reference_type="reservation",
            reference_id=r.reservation_id,
        )
        if doc:
            sent += 1
    return sent


async def _batch_membership_expiry(tenant_id: PydanticObjectId, *, branch_code: str | None) -> int:
    horizon = date.today() + timedelta(days=7)
    filters: dict[str, Any] = {
        "tenant_id": tenant_id,
        "status": LibraryMemberStatus.ACTIVE.value,
        "expires_on": {"$lte": horizon, "$gte": date.today()},
    }
    if branch_code:
        filters["branch_code"] = branch_code.strip().upper()
    rows = await LibraryMembershipReference.find(filters).to_list()
    sent = 0
    for m in rows:
        if not m.expires_on:
            continue
        key = f"membership_expiry:{m.member_user_id}:{m.expires_on.isoformat()}"
        doc = await emit_library_notification(
            tenant_id,
            event_type=LibraryNotificationEvent.MEMBERSHIP_EXPIRY,
            recipient_user_id=m.member_user_id,
            dedupe_key=key,
            template_kwargs={"expires_on": m.expires_on.isoformat()},
            branch_code=m.branch_code,
            reference_type="membership",
            reference_id=m.membership_number or str(m.member_user_id),
        )
        if doc:
            sent += 1
    return sent


async def patron_notifications(tenant_id: PydanticObjectId, user_id: PydanticObjectId, limit: int = 30) -> list[dict]:
    rows = await LibraryNotification.find(
        {"tenant_id": tenant_id, "recipient_user_id": user_id}
    ).sort("-created_at").limit(limit).to_list()
    return [
        {
            "notification_key": f"library:{r.notification_id}",
            "source": "library",
            "title": r.title,
            "body": r.body,
            "created_at": r.created_at,
            "event_type": r.event_type,
        }
        for r in rows
    ]