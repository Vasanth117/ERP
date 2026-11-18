"""Department Admin — announcements and delivery orchestration."""

from __future__ import annotations

from datetime import datetime, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.department_admin.department_scope import faculty_user_ids_in_department
from app.modules.department_admin.models import (
    DepartmentAnnouncement,
    DepartmentAnnouncementAcknowledgement,
    DepartmentAnnouncementStatus,
)
from app.modules.department_admin.phase6_schemas import (
    AnnouncementCreate,
    AnnouncementDecisionBody,
    AnnouncementDeliveryStatusRead,
    AnnouncementRead,
    AnnouncementScheduleBody,
    AnnouncementUpdate,
    AnnouncementAcknowledgementRead,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.messaging.outbox_models import DomainOutboxEvent, OutboxEventStatus
from app.modules.students.models import StudentProfile

AUDIENCE_TYPES = frozenset(
    {
        "department_faculty",
        "department_students",
        "programme",
        "batch",
        "section",
    }
)

EDITABLE_STATUSES = frozenset(
    {
        DepartmentAnnouncementStatus.DRAFT,
        DepartmentAnnouncementStatus.REJECTED,
    }
)


def _announcement_read(doc: DepartmentAnnouncement) -> AnnouncementRead:
    return AnnouncementRead(
        announcement_id=str(doc.id),
        title=doc.title,
        body=doc.body,
        category=doc.category,
        priority=doc.priority,
        audience_type=doc.audience_type,
        programme_code=doc.programme_code,
        batch_label=doc.batch_label,
        section_code=doc.section_code,
        status=doc.status,
        author_user_id=str(doc.author_user_id),
        publish_at=doc.publish_at,
        expires_at=doc.expires_at,
        scheduled_publish_at=doc.scheduled_publish_at,
        approved_by=str(doc.approved_by) if doc.approved_by else None,
        approved_at=doc.approved_at,
        delivery_summary=doc.delivery_summary,
        attachment_refs=doc.attachment_refs,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def _validate_audience(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    institution,
    *,
    audience_type: str,
    programme_code: str | None,
    batch_label: str | None,
    section_code: str | None,
) -> None:
    if audience_type not in AUDIENCE_TYPES:
        raise AppError(code="VALIDATION_ERROR", message="Unsupported audience_type", status_code=422)
    programmes = {c.upper() for c in institution.programme_codes}
    if audience_type == "programme":
        if not programme_code or programme_code.upper() not in programmes:
            raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)
    if audience_type == "batch":
        if not programme_code or not batch_label:
            raise AppError(code="VALIDATION_ERROR", message="programme_code and batch_label required", status_code=422)
        if programme_code.upper() not in programmes:
            raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)
    if audience_type == "section":
        if not programme_code or not batch_label or not section_code:
            raise AppError(code="VALIDATION_ERROR", message="programme_code, batch_label, and section_code required", status_code=422)
        if programme_code.upper() not in programmes:
            raise AppError(code="FORBIDDEN", message="Programme outside department", status_code=403)


async def _estimate_audience_size(
    tenant_id: PydanticObjectId,
    central_id: PydanticObjectId,
    doc: DepartmentAnnouncement,
) -> int:
    if doc.audience_type == "department_faculty":
        return len(await faculty_user_ids_in_department(tenant_id, central_id))
    base: dict = {"tenant_id": tenant_id, "department_id": central_id}
    if doc.audience_type == "department_students":
        return await StudentProfile.find(base).count()
    if doc.audience_type == "programme" and doc.programme_code:
        base["programme_code"] = doc.programme_code.upper()
        return await StudentProfile.find(base).count()
    if doc.audience_type == "batch" and doc.programme_code and doc.batch_label:
        base["programme_code"] = doc.programme_code.upper()
        base["batch_label"] = doc.batch_label
        return await StudentProfile.find(base).count()
    if doc.audience_type == "section" and doc.programme_code and doc.batch_label and doc.section_code:
        base["programme_code"] = doc.programme_code.upper()
        base["batch_label"] = doc.batch_label
        base["section_code"] = doc.section_code.upper()
        return await StudentProfile.find(base).count()
    return 0


async def list_announcements(
    scope: AccessScope,
    user: User,
    *,
    status: DepartmentAnnouncementStatus | None,
    pagination: Pagination,
) -> Page[AnnouncementRead]:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    q: dict = {"tenant_id": tenant_id, "central_department_id": central_id}
    if status:
        q["status"] = status.value
    db_query = DepartmentAnnouncement.find(q).sort("-created_at")
    total = await db_query.count()
    rows = await db_query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_announcement_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def get_announcement(scope: AccessScope, user: User, announcement_id: str) -> AnnouncementRead:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentAnnouncement.get(to_object_id(announcement_id, "announcement_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    return _announcement_read(doc)


async def create_announcement(scope: AccessScope, user: User, payload: AnnouncementCreate) -> AnnouncementRead:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    await _validate_audience(
        tenant_id,
        central_id,
        institution,
        audience_type=payload.audience_type,
        programme_code=payload.programme_code,
        batch_label=payload.batch_label,
        section_code=payload.section_code,
    )
    if payload.idempotency_key:
        existing = await DepartmentAnnouncement.find_one(
            Eq(DepartmentAnnouncement.tenant_id, tenant_id),
            Eq(DepartmentAnnouncement.idempotency_key, payload.idempotency_key),
        )
        if existing and existing.central_department_id == central_id:
            return _announcement_read(existing)
    doc = DepartmentAnnouncement(
        tenant_id=tenant_id,
        central_department_id=central_id,
        title=payload.title.strip(),
        body=payload.body.strip(),
        category=payload.category,
        priority=payload.priority,
        audience_type=payload.audience_type,
        programme_code=payload.programme_code.upper() if payload.programme_code else None,
        batch_label=payload.batch_label,
        section_code=payload.section_code.upper() if payload.section_code else None,
        expires_at=payload.expires_at,
        attachment_refs=payload.attachment_refs,
        status=DepartmentAnnouncementStatus.DRAFT,
        author_user_id=user.id,
        idempotency_key=payload.idempotency_key,
    )
    await doc.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.announcement.created",
        resource_type="department_announcement",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _announcement_read(doc)


async def update_announcement(
    scope: AccessScope,
    user: User,
    announcement_id: str,
    payload: AnnouncementUpdate,
) -> AnnouncementRead:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_MANAGE)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentAnnouncement.get(to_object_id(announcement_id, "announcement_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status not in EDITABLE_STATUSES:
        raise AppError(code="FORBIDDEN", message="Only draft or rejected announcements can be edited", status_code=403)
    audience_type = payload.audience_type or doc.audience_type
    programme = payload.programme_code if payload.programme_code is not None else doc.programme_code
    batch = payload.batch_label if payload.batch_label is not None else doc.batch_label
    section = payload.section_code if payload.section_code is not None else doc.section_code
    await _validate_audience(
        tenant_id,
        central_id,
        institution,
        audience_type=audience_type,
        programme_code=programme,
        batch_label=batch,
        section_code=section,
    )
    if payload.title is not None:
        doc.title = payload.title.strip()
    if payload.body is not None:
        doc.body = payload.body.strip()
    if payload.category is not None:
        doc.category = payload.category
    if payload.priority is not None:
        doc.priority = payload.priority
    if payload.audience_type is not None:
        doc.audience_type = payload.audience_type
    if payload.programme_code is not None:
        doc.programme_code = payload.programme_code.upper() if payload.programme_code else None
    if payload.batch_label is not None:
        doc.batch_label = payload.batch_label
    if payload.section_code is not None:
        doc.section_code = payload.section_code.upper() if payload.section_code else None
    if payload.expires_at is not None:
        doc.expires_at = payload.expires_at
    if payload.attachment_refs is not None:
        doc.attachment_refs = payload.attachment_refs
    doc.updated_at = utcnow()
    await doc.save()
    return _announcement_read(doc)


async def submit_announcement(scope: AccessScope, user: User, announcement_id: str) -> AnnouncementRead:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentAnnouncement.get(to_object_id(announcement_id, "announcement_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status != DepartmentAnnouncementStatus.DRAFT:
        raise AppError(code="CONFLICT", message="Only draft announcements can be submitted", status_code=409)
    est = await _estimate_audience_size(tenant_id, central_id, doc)
    if est <= 0 and doc.audience_type != "department_faculty":
        raise AppError(code="VALIDATION_ERROR", message="No recipients in selected audience", status_code=422)
    doc.status = DepartmentAnnouncementStatus.SUBMITTED
    doc.updated_at = utcnow()
    doc.publish_history.append({"action": "submitted", "at": utcnow().isoformat(), "by": str(user.id)})
    await doc.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.announcement.submitted",
        resource_type="department_announcement",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _announcement_read(doc)


async def approve_announcement(
    scope: AccessScope,
    user: User,
    announcement_id: str,
    body: AnnouncementDecisionBody,
) -> AnnouncementRead:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentAnnouncement.get(to_object_id(announcement_id, "announcement_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status != DepartmentAnnouncementStatus.SUBMITTED:
        raise AppError(code="CONFLICT", message="Announcement is not awaiting approval", status_code=409)
    doc.status = DepartmentAnnouncementStatus.APPROVED
    doc.approved_by = user.id
    doc.approved_at = utcnow()
    doc.approval_note = body.note
    doc.updated_at = utcnow()
    doc.publish_history.append({"action": "approved", "at": utcnow().isoformat(), "by": str(user.id)})
    await doc.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.announcement.approved",
        resource_type="department_announcement",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _announcement_read(doc)


async def reject_announcement(
    scope: AccessScope,
    user: User,
    announcement_id: str,
    body: AnnouncementDecisionBody,
) -> AnnouncementRead:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentAnnouncement.get(to_object_id(announcement_id, "announcement_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status != DepartmentAnnouncementStatus.SUBMITTED:
        raise AppError(code="CONFLICT", message="Announcement is not awaiting approval", status_code=409)
    doc.status = DepartmentAnnouncementStatus.REJECTED
    doc.rejection_reason = body.note
    doc.updated_at = utcnow()
    doc.publish_history.append({"action": "rejected", "at": utcnow().isoformat(), "by": str(user.id)})
    await doc.save()
    return _announcement_read(doc)


async def schedule_announcement(
    scope: AccessScope,
    user: User,
    announcement_id: str,
    body: AnnouncementScheduleBody,
) -> AnnouncementRead:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    when = body.scheduled_publish_at
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    if when <= utcnow():
        raise AppError(code="VALIDATION_ERROR", message="scheduled_publish_at must be in the future", status_code=422)
    doc = await DepartmentAnnouncement.get(to_object_id(announcement_id, "announcement_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status not in {DepartmentAnnouncementStatus.APPROVED, DepartmentAnnouncementStatus.DRAFT}:
        raise AppError(code="CONFLICT", message="Announcement cannot be scheduled in current status", status_code=409)
    if doc.status == DepartmentAnnouncementStatus.DRAFT:
        doc.status = DepartmentAnnouncementStatus.APPROVED
        doc.approved_by = user.id
        doc.approved_at = utcnow()
    doc.status = DepartmentAnnouncementStatus.SCHEDULED
    doc.scheduled_publish_at = when
    doc.updated_at = utcnow()
    doc.publish_history.append({"action": "scheduled", "at": utcnow().isoformat(), "scheduled_for": when.isoformat()})
    await doc.save()
    key = body.idempotency_key or f"dept_ann_schedule:{doc.id}:{int(when.timestamp())}"
    if not await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, key)
    ):
        await DomainOutboxEvent(
            tenant_id=tenant_id,
            event_type="department.announcement.scheduled",
            aggregate_type="department_announcement",
            aggregate_id=str(doc.id),
            payload={
                "announcement_id": str(doc.id),
                "scheduled_publish_at": when.isoformat(),
                "audience_type": doc.audience_type,
                "cancelled": False,
            },
            idempotency_key=key,
            status=OutboxEventStatus.PENDING,
        ).insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.announcement.scheduled",
        resource_type="department_announcement",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _announcement_read(doc)


async def _queue_publish_outbox(tenant_id: PydanticObjectId, doc: DepartmentAnnouncement, *, key: str) -> str | None:
    if await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, key)
    ):
        existing = await DomainOutboxEvent.find_one(
            Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, key)
        )
        return str(existing.id) if existing else None
    event = DomainOutboxEvent(
        tenant_id=tenant_id,
        event_type="department.announcement.publish",
        aggregate_type="department_announcement",
        aggregate_id=str(doc.id),
        payload={
            "announcement_id": str(doc.id),
            "title": doc.title,
            "priority": doc.priority,
            "audience_type": doc.audience_type,
            "programme_code": doc.programme_code,
            "batch_label": doc.batch_label,
            "section_code": doc.section_code,
            "central_department_id": str(doc.central_department_id),
            "channels": ["in_app", "email"],
        },
        idempotency_key=key,
        status=OutboxEventStatus.PENDING,
    )
    await event.insert()
    return str(event.id)


async def publish_announcement(scope: AccessScope, user: User, announcement_id: str) -> AnnouncementRead:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentAnnouncement.get(to_object_id(announcement_id, "announcement_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status in {
        DepartmentAnnouncementStatus.PUBLISHED,
        DepartmentAnnouncementStatus.CANCELLED,
        DepartmentAnnouncementStatus.ARCHIVED,
    }:
        raise AppError(code="CONFLICT", message="Announcement cannot be published", status_code=409)
    if doc.status not in {DepartmentAnnouncementStatus.APPROVED, DepartmentAnnouncementStatus.SCHEDULED}:
        raise AppError(code="FORBIDDEN", message="Submit and approve before publishing", status_code=403)
    est = await _estimate_audience_size(tenant_id, central_id, doc)
    if est <= 0:
        raise AppError(code="VALIDATION_ERROR", message="No recipients in selected audience", status_code=422)
    key = f"dept_ann_publish:{doc.id}"
    outbox_id = await _queue_publish_outbox(tenant_id, doc, key=key)
    now = utcnow()
    doc.status = DepartmentAnnouncementStatus.PUBLISHED
    doc.publish_at = now
    doc.scheduled_publish_at = None
    doc.delivery_summary = {
        "estimated_recipients": est,
        "queued_at": now.isoformat(),
        "status": "queued",
        "last_outbox_event_id": outbox_id,
    }
    doc.updated_at = now
    doc.publish_history.append({"action": "published", "at": now.isoformat(), "by": str(user.id)})
    await doc.save()
    await record_department_audit(
        actor_id=user.id,
        action="department.announcement.published",
        resource_type="department_announcement",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _announcement_read(doc)


async def cancel_announcement(scope: AccessScope, user: User, announcement_id: str) -> AnnouncementRead:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_MANAGE)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentAnnouncement.get(to_object_id(announcement_id, "announcement_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status == DepartmentAnnouncementStatus.PUBLISHED:
        doc.status = DepartmentAnnouncementStatus.ARCHIVED
    else:
        doc.status = DepartmentAnnouncementStatus.CANCELLED
    doc.scheduled_publish_at = None
    doc.updated_at = utcnow()
    doc.publish_history.append({"action": "cancelled", "at": utcnow().isoformat(), "by": str(user.id)})
    await doc.save()
    key = f"dept_ann_cancel:{doc.id}"
    if not await DomainOutboxEvent.find_one(
        Eq(DomainOutboxEvent.tenant_id, tenant_id), Eq(DomainOutboxEvent.idempotency_key, key)
    ):
        await DomainOutboxEvent(
            tenant_id=tenant_id,
            event_type="department.announcement.cancelled",
            aggregate_type="department_announcement",
            aggregate_id=str(doc.id),
            payload={"announcement_id": str(doc.id), "cancelled": True},
            idempotency_key=key,
            status=OutboxEventStatus.PENDING,
        ).insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.announcement.cancelled",
        resource_type="department_announcement",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
    )
    return _announcement_read(doc)


async def announcement_delivery_status(
    scope: AccessScope,
    user: User,
    announcement_id: str,
) -> AnnouncementDeliveryStatusRead:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentAnnouncement.get(to_object_id(announcement_id, "announcement_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    last_id = doc.delivery_summary.get("last_outbox_event_id")
    status = doc.delivery_summary.get("status", doc.status.value)
    if last_id:
        outbox = await DomainOutboxEvent.get(to_object_id(last_id, "outbox"))
        if outbox and outbox.tenant_id == tenant_id:
            status = outbox.status.value
    return AnnouncementDeliveryStatusRead(
        announcement_id=str(doc.id),
        status=status,
        delivery_summary=doc.delivery_summary,
        last_outbox_event_id=last_id,
    )


async def list_announcement_acknowledgements(
    scope: AccessScope,
    user: User,
    announcement_id: str,
    *,
    pagination: Pagination,
) -> Page[AnnouncementAcknowledgementRead]:
    authorize(scope, Permission.DEPARTMENT_COMMUNICATION_READ)
    central_id, _ = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    doc = await DepartmentAnnouncement.get(to_object_id(announcement_id, "announcement_id"))
    if doc is None or doc.tenant_id != tenant_id or doc.central_department_id != central_id:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    q = {
        "tenant_id": tenant_id,
        "announcement_id": doc.id,
    }
    db_query = DepartmentAnnouncementAcknowledgement.find(q).sort("-acknowledged_at")
    total = await db_query.count()
    rows = await db_query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        AnnouncementAcknowledgementRead(user_id=str(r.user_id), acknowledged_at=r.acknowledged_at) for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)