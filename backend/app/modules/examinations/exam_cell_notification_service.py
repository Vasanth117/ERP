"""Examination notifications and communication."""

from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_notification_dispatch import (
    enqueue_exam_delivery,
    process_pending_exam_deliveries,
)
from app.modules.examinations.exam_cell_notification_enums import (
    ExamAnnouncementAudience,
    ExamNotificationChannel,
    ExamNotificationEvent,
)
from app.modules.examinations.exam_cell_notification_models import (
    ExamAnnouncementRecord,
    ExamNotificationDeliveryLog,
    ExamNotificationEventRecord,
    ExamNotificationTemplate,
)
from app.modules.examinations.exam_cell_notification_schemas import (
    ExamAnnouncementCreate,
    ExamAnnouncementRead,
    ExamManualNotificationRequest,
    ExamNotificationDeliveryRead,
    ExamNotificationEventRead,
    ExamNotificationPreferenceRead,
    ExamNotificationPreferenceUpdate,
    ExamNotificationTemplateRead,
    ExamNotificationTemplateUpsert,
)
from app.modules.examinations.exam_cell_notification_templates import render_exam_notification
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_notification_manage,
    authorize_examination_cell_notification_publish,
    authorize_examination_cell_notification_read,
    require_college_tenant,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_registration_models import ExamRegistration


def _event_id() -> str:
    return f"ene_{uuid4().hex[:12]}"


def _template_id() -> str:
    return f"ent_{uuid4().hex[:12]}"


def _announcement_id() -> str:
    return f"ean_{uuid4().hex[:12]}"


_PREF_EVENT = "__user_preferences__"


async def _validate_recipient(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> User:
    user = await User.find_one(Eq(User.id, user_id))
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Recipient not in tenant", status_code=422)
    if not user.is_active:
        raise AppError(code="VALIDATION_ERROR", message="Recipient account inactive", status_code=422)
    return user


async def _user_preferences(tenant_id: PydanticObjectId, user_id: PydanticObjectId) -> ExamNotificationTemplate:
    row = await ExamNotificationTemplate.find_one(
        Eq(ExamNotificationTemplate.tenant_id, tenant_id),
        Eq(ExamNotificationTemplate.event_type, _PREF_EVENT),
        Eq(ExamNotificationTemplate.user_id, user_id),
    )
    if row is None:
        row = ExamNotificationTemplate(
            tenant_id=tenant_id,
            template_id=_template_id(),
            event_type=_PREF_EVENT,
            user_id=user_id,
            title_template="",
            body_template="",
        )
        await row.insert()
    return row


async def _resolve_template(
    tenant_id: PydanticObjectId,
    event: ExamNotificationEvent,
    template_kwargs: dict[str, str],
) -> tuple[str, str]:
    override = await ExamNotificationTemplate.find_one(
        {
            "tenant_id": tenant_id,
            "event_type": event.value,
            "user_id": None,
        }
    )
    if override and override.is_active:
        safe = {k: (v or "") for k, v in template_kwargs.items()}
        return override.title_template.format(**safe), override.body_template.format(**safe)
    return render_exam_notification(event, **template_kwargs)


def _channel_enabled(prefs: ExamNotificationTemplate, channel: ExamNotificationChannel) -> bool:
    if channel == ExamNotificationChannel.IN_APP:
        return prefs.in_app_enabled
    if channel == ExamNotificationChannel.EMAIL:
        return prefs.email_enabled
    return prefs.sms_enabled


async def _assert_restricted_recipient(user: User, *, restricted: bool) -> None:
    if not restricted:
        return
    from app.authorization.permissions import permissions_for_role

    perms = permissions_for_role(user.role)
    allowed = Permission.EXAMINATION_CELL_INCIDENT_INVESTIGATE in perms or Permission.EXAMINATION_CELL_INCIDENT_MANAGE in perms
    if not allowed:
        raise AppError(code="FORBIDDEN", message="Recipient not authorized for restricted examination communication", status_code=403)


async def emit_exam_notification(
    tenant_id: PydanticObjectId,
    *,
    event_type: ExamNotificationEvent,
    recipient_user_id: PydanticObjectId,
    dedupe_key: str,
    template_kwargs: dict[str, str],
    exam_session_id: PydanticObjectId | None = None,
    reference_type: str | None = None,
    reference_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    restricted: bool = False,
    channels: list[ExamNotificationChannel] | None = None,
) -> ExamNotificationEventRecord | None:
    if await ExamNotificationEventRecord.find_one(
        Eq(ExamNotificationEventRecord.tenant_id, tenant_id),
        Eq(ExamNotificationEventRecord.dedupe_key, dedupe_key),
    ):
        return None
    recipient = await _validate_recipient(tenant_id, recipient_user_id)
    await _assert_restricted_recipient(recipient, restricted=restricted)

    prefs = await _user_preferences(tenant_id, recipient_user_id)
    title, body = await _resolve_template(tenant_id, event_type, template_kwargs)

    record = ExamNotificationEventRecord(
        tenant_id=tenant_id,
        event_record_id=_event_id(),
        event_type=event_type.value,
        recipient_user_id=recipient_user_id,
        title=title,
        body=body,
        exam_session_id=exam_session_id,
        restricted=restricted,
        reference_type=reference_type,
        reference_id=reference_id,
        dedupe_key=dedupe_key,
        metadata=metadata or {},
    )
    await record.insert()

    use_channels = channels or [ExamNotificationChannel.IN_APP, ExamNotificationChannel.EMAIL]
    for channel in use_channels:
        if not _channel_enabled(prefs, channel):
            continue
        await enqueue_exam_delivery(
            tenant_id,
            event_record_id=record.event_record_id,
            recipient_user_id=recipient_user_id,
            channel=channel,
            title=title,
            body=body,
            dedupe_key=dedupe_key,
        )

    await record_exam_activity(
        tenant_id,
        actor_id=recipient_user_id,
        action="exam_notification.emitted",
        summary=title,
        exam_session_id=exam_session_id,
        metadata={"event_type": event_type.value, "dedupe_key": dedupe_key},
    )
    return record


async def send_manual_notification(
    scope: AccessScope,
    actor: User,
    payload: ExamManualNotificationRequest,
) -> ExamNotificationEventRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_notification_manage(scope)
    recipient = to_object_id(payload.recipient_user_id, "recipient_user_id")
    session_oid = to_object_id(payload.exam_session_id, "exam_session_id") if payload.exam_session_id else None
    dedupe = payload.dedupe_key or f"manual:{payload.event_type.value}:{recipient}:{uuid4().hex[:8]}"
    if payload.restricted:
        user = await _validate_recipient(tenant_id, recipient)
        await _assert_restricted_recipient(user, restricted=True)
    record = await emit_exam_notification(
        tenant_id,
        event_type=payload.event_type,
        recipient_user_id=recipient,
        dedupe_key=dedupe,
        template_kwargs=payload.template_kwargs,
        exam_session_id=session_oid,
        restricted=payload.restricted,
        channels=payload.channels,
    )
    if record is None:
        existing = await ExamNotificationEventRecord.find_one(
            Eq(ExamNotificationEventRecord.tenant_id, tenant_id),
            Eq(ExamNotificationEventRecord.dedupe_key, dedupe),
        )
        if existing is None:
            raise AppError(code="CONFLICT", message="Duplicate notification", status_code=409)
        return ExamNotificationEventRead.from_doc(existing)
    return ExamNotificationEventRead.from_doc(record)


async def upsert_template(
    scope: AccessScope,
    actor: User,
    payload: ExamNotificationTemplateUpsert,
) -> ExamNotificationTemplateRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_notification_manage(scope)
    _ = actor
    row = await ExamNotificationTemplate.find_one(
        {
            "tenant_id": tenant_id,
            "event_type": payload.event_type.value,
            "user_id": None,
        }
    )
    if row is None:
        row = ExamNotificationTemplate(
            tenant_id=tenant_id,
            template_id=_template_id(),
            event_type=payload.event_type.value,
            title_template=payload.title_template,
            body_template=payload.body_template,
            is_active=payload.is_active,
        )
        await row.insert()
    else:
        row.title_template = payload.title_template
        row.body_template = payload.body_template
        row.is_active = payload.is_active
        row.updated_at = utcnow()
        await row.save()
    return ExamNotificationTemplateRead.from_doc(row)


async def update_preferences(
    scope: AccessScope,
    actor: User,
    payload: ExamNotificationPreferenceUpdate,
) -> ExamNotificationPreferenceRead:
    tenant_id = require_college_tenant(scope)
    prefs = await _user_preferences(tenant_id, actor.id)
    if payload.in_app_enabled is not None:
        prefs.in_app_enabled = payload.in_app_enabled
    if payload.email_enabled is not None:
        prefs.email_enabled = payload.email_enabled
    if payload.sms_enabled is not None:
        prefs.sms_enabled = payload.sms_enabled
    prefs.updated_at = utcnow()
    await prefs.save()
    return ExamNotificationPreferenceRead.from_template(prefs)


async def get_preferences(scope: AccessScope, actor: User) -> ExamNotificationPreferenceRead:
    tenant_id = require_college_tenant(scope)
    return ExamNotificationPreferenceRead.from_template(await _user_preferences(tenant_id, actor.id))


async def list_notification_history(
    scope: AccessScope,
    pagination: Pagination,
    *,
    recipient_user_id: str | None = None,
) -> Page[ExamNotificationEventRead]:
    tenant_id = require_college_tenant(scope)
    can_manage = Permission.EXAMINATION_CELL_NOTIFICATION_MANAGE in scope.effective_permissions
    can_read = Permission.EXAMINATION_CELL_NOTIFICATION_READ in scope.effective_permissions
    is_student = Permission.STUDENT_SELF_ACCESS in scope.effective_permissions
    if not (can_read or can_manage or is_student):
        authorize_examination_cell_notification_read(scope)
    query: dict[str, Any] = {"tenant_id": tenant_id}
    if recipient_user_id:
        if not can_manage and str(scope.user_id) != recipient_user_id:
            raise AppError(code="FORBIDDEN", message="Cannot view another user's notifications", status_code=403)
        query["recipient_user_id"] = to_object_id(recipient_user_id, "recipient_user_id")
    elif not can_manage:
        query["recipient_user_id"] = scope.user_id
    rows = (
        await ExamNotificationEventRecord.find(query)
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    total = await ExamNotificationEventRecord.find(query).count()
    return Page(
        items=[ExamNotificationEventRead.from_doc(r) for r in rows],
        total=total,
        offset=pagination.offset,
        limit=pagination.limit,
    )


async def list_deliveries_for_event(scope: AccessScope, event_record_id: str) -> list[ExamNotificationDeliveryRead]:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_notification_read(scope)
    event = await ExamNotificationEventRecord.find_one(
        Eq(ExamNotificationEventRecord.tenant_id, tenant_id),
        Eq(ExamNotificationEventRecord.event_record_id, event_record_id),
    )
    if event is None:
        raise AppError(code="NOT_FOUND", message="Notification event not found", status_code=404)
    if event.restricted and Permission.EXAMINATION_CELL_INCIDENT_INVESTIGATE not in scope.effective_permissions:
        if event.recipient_user_id != scope.user_id:
            authorize_examination_cell_notification_manage(scope)
    rows = await ExamNotificationDeliveryLog.find(
        Eq(ExamNotificationDeliveryLog.tenant_id, tenant_id),
        Eq(ExamNotificationDeliveryLog.event_record_id, event_record_id),
    ).to_list()
    return [ExamNotificationDeliveryRead.from_doc(r) for r in rows]


async def create_announcement(scope: AccessScope, actor: User, payload: ExamAnnouncementCreate) -> ExamAnnouncementRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_notification_manage(scope)
    session_oid = to_object_id(payload.exam_session_id, "exam_session_id") if payload.exam_session_id else None
    recipients = [to_object_id(uid, "recipient_user_id") for uid in payload.recipient_user_ids]
    doc = ExamAnnouncementRecord(
        tenant_id=tenant_id,
        announcement_id=_announcement_id(),
        title=payload.title,
        body=payload.body,
        audience=payload.audience.value,
        exam_session_id=session_oid,
        recipient_user_ids=recipients,
        created_by=actor.id,
    )
    await doc.insert()
    return ExamAnnouncementRead.from_doc(doc)


async def publish_announcement(scope: AccessScope, actor: User, announcement_id: str) -> ExamAnnouncementRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_notification_publish(scope)
    doc = await ExamAnnouncementRecord.find_one(
        Eq(ExamAnnouncementRecord.tenant_id, tenant_id),
        Eq(ExamAnnouncementRecord.announcement_id, announcement_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.published:
        return ExamAnnouncementRead.from_doc(doc)

    targets: list[PydanticObjectId] = list(doc.recipient_user_ids)
    if doc.audience == ExamAnnouncementAudience.SESSION_STUDENTS.value and doc.exam_session_id:
        regs = await ExamRegistration.find(
            Eq(ExamRegistration.tenant_id, tenant_id),
            Eq(ExamRegistration.exam_session_id, doc.exam_session_id),
        ).to_list()
        targets.extend([r.student_user_id for r in regs])
    targets = list({str(t): t for t in targets}.values())

    for uid in targets:
        dedupe = f"announce:{doc.announcement_id}:{uid}"
        await emit_exam_notification(
            tenant_id,
            event_type=ExamNotificationEvent.CELL_ANNOUNCEMENT,
            recipient_user_id=uid,
            dedupe_key=dedupe,
            template_kwargs={"title": doc.title, "body": doc.body},
            exam_session_id=doc.exam_session_id,
            reference_type="exam_announcement",
            reference_id=doc.announcement_id,
        )

    doc.published = True
    doc.published_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_announcement.published",
        summary=doc.title,
        exam_session_id=doc.exam_session_id,
        metadata={"announcement_id": doc.announcement_id, "recipients": len(targets)},
    )
    return ExamAnnouncementRead.from_doc(doc)


async def run_notification_batch(scope: AccessScope) -> dict[str, int]:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_notification_manage(scope)
    return await process_pending_exam_deliveries(tenant_id)