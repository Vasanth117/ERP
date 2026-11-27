"""Communication administration services."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.communication_admin_models import (
    AnnouncementAudience,
    CommunicationAudienceGroup,
    CommunicationDeliveryLog,
    CommunicationProviderSettings,
    CommunicationSchedule,
    CommunicationTemplate,
    DeliveryStatus,
    InstitutionAnnouncement,
)
from app.modules.college_admin.communication_admin_schemas import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementSchedule,
    AudienceGroupUpsert,
    ProviderSettingsUpsert,
    RetryDelivery,
    TemplateUpsert,
)
from app.modules.college_admin.policy import require_college_tenant_scope


async def create_announcement(scope: AccessScope, payload: AnnouncementCreate) -> AnnouncementRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    aid = payload.announcement_id.strip()
    if await InstitutionAnnouncement.find_one(Eq(InstitutionAnnouncement.tenant_id, tenant_id), Eq(InstitutionAnnouncement.announcement_id, aid)):
        raise AppError(code="CONFLICT", message="Announcement id exists", status_code=409)
    dept = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    doc = InstitutionAnnouncement(
        tenant_id=tenant_id,
        announcement_id=aid,
        title=payload.title,
        body=payload.body,
        audience=payload.audience,
        department_id=dept,
        audience_group_id=payload.audience_group_id,
        channels=payload.channels,
        actor_id=scope.user_id,
    )
    await doc.insert()
    return AnnouncementRead.from_document(doc)


async def publish_announcement(scope: AccessScope, announcement_id: str) -> AnnouncementRead:
    authorize(scope, Permission.COMMUNICATION_ADMIN_PUBLISH)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionAnnouncement.find_one(
        Eq(InstitutionAnnouncement.tenant_id, tenant_id),
        Eq(InstitutionAnnouncement.announcement_id, announcement_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    if doc.status == "published":
        raise AppError(code="CONFLICT", message="Already published", status_code=409)
    doc.status = "published"
    doc.published_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    log_id = f"dl_{uuid4().hex[:12]}"
    await CommunicationDeliveryLog(
        tenant_id=tenant_id,
        log_id=log_id,
        announcement_id=announcement_id,
        channel="in_app",
        status=DeliveryStatus.SENT,
    ).insert()
    return AnnouncementRead.from_document(doc)


async def schedule_announcement(scope: AccessScope, payload: AnnouncementSchedule) -> dict:
    authorize(scope, Permission.COMMUNICATION_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionAnnouncement.find_one(
        Eq(InstitutionAnnouncement.tenant_id, tenant_id),
        Eq(InstitutionAnnouncement.announcement_id, payload.announcement_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Announcement not found", status_code=404)
    doc.scheduled_for = payload.run_at
    doc.status = "scheduled"
    await doc.save()
    schedule_id = f"sch_{uuid4().hex[:10]}"
    await CommunicationSchedule(
        tenant_id=tenant_id,
        schedule_id=schedule_id,
        announcement_id=payload.announcement_id,
        run_at=payload.run_at,
    ).insert()
    return {"schedule_id": schedule_id}


async def upsert_template(scope: AccessScope, payload: TemplateUpsert) -> dict:
    authorize(scope, Permission.COMMUNICATION_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await CommunicationTemplate.find_one(
        Eq(CommunicationTemplate.tenant_id, tenant_id),
        Eq(CommunicationTemplate.template_code, payload.template_code),
        Eq(CommunicationTemplate.channel, payload.channel),
    )
    if doc:
        doc.subject = payload.subject
        doc.body = payload.body
        doc.version += 1
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await CommunicationTemplate(
            tenant_id=tenant_id,
            template_code=payload.template_code,
            channel=payload.channel,
            subject=payload.subject,
            body=payload.body,
            updated_by=scope.user_id,
        ).insert()
    return {"template_code": payload.template_code, "channel": payload.channel}


async def upsert_audience_group(scope: AccessScope, payload: AudienceGroupUpsert) -> dict:
    authorize(scope, Permission.COMMUNICATION_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    members = [to_object_id(uid, "member_user_id") for uid in payload.member_user_ids]
    doc = await CommunicationAudienceGroup.find_one(
        Eq(CommunicationAudienceGroup.tenant_id, tenant_id),
        Eq(CommunicationAudienceGroup.group_id, payload.group_id),
    )
    if doc:
        doc.name = payload.name
        doc.member_user_ids = members
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await CommunicationAudienceGroup(
            tenant_id=tenant_id,
            group_id=payload.group_id,
            name=payload.name,
            member_user_ids=members,
        ).insert()
    return {"group_id": payload.group_id}


async def upsert_provider_settings(scope: AccessScope, payload: ProviderSettingsUpsert) -> dict:
    authorize(scope, Permission.COMMUNICATION_ADMIN_CONFIG)
    tenant_id = require_college_tenant_scope(scope)
    doc = await CommunicationProviderSettings.find_one(
        Eq(CommunicationProviderSettings.tenant_id, tenant_id),
        Eq(CommunicationProviderSettings.channel, payload.channel),
    )
    if doc:
        doc.provider_name = payload.provider_name
        doc.credential_ref = payload.credential_ref
        doc.push_enabled = payload.push_enabled
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    else:
        await CommunicationProviderSettings(
            tenant_id=tenant_id,
            channel=payload.channel,
            provider_name=payload.provider_name,
            credential_ref=payload.credential_ref,
            push_enabled=payload.push_enabled,
            updated_by=scope.user_id,
        ).insert()
    return {"channel": payload.channel}


async def list_failed_deliveries(scope: AccessScope, pagination: Pagination) -> Page[dict]:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    query = CommunicationDeliveryLog.find(Eq(CommunicationDeliveryLog.tenant_id, tenant_id), Eq(CommunicationDeliveryLog.status, DeliveryStatus.FAILED))
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[{"log_id": r.log_id, "announcement_id": r.announcement_id, "channel": r.channel, "error": r.error} for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def retry_all_failed_deliveries(scope: AccessScope, *, limit: int = 50) -> dict:
    authorize(scope, Permission.COMMUNICATION_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    failed = await CommunicationDeliveryLog.find(
        Eq(CommunicationDeliveryLog.tenant_id, tenant_id),
        Eq(CommunicationDeliveryLog.status, DeliveryStatus.FAILED),
    ).limit(limit).to_list()
    retried = 0
    skipped = 0
    for log in failed:
        if log.retry_count >= 3:
            skipped += 1
            continue
        log.status = DeliveryStatus.RETRYING
        log.retry_count += 1
        log.updated_at = utcnow()
        await log.save()
        log.status = DeliveryStatus.SENT
        log.error = None
        log.updated_at = utcnow()
        await log.save()
        retried += 1
    remaining = await CommunicationDeliveryLog.find(
        Eq(CommunicationDeliveryLog.tenant_id, tenant_id),
        Eq(CommunicationDeliveryLog.status, DeliveryStatus.FAILED),
    ).count()
    return {"retried": retried, "skipped": skipped, "failed_remaining": remaining}


async def retry_delivery(scope: AccessScope, payload: RetryDelivery) -> dict:
    authorize(scope, Permission.COMMUNICATION_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    log = await CommunicationDeliveryLog.find_one(Eq(CommunicationDeliveryLog.tenant_id, tenant_id), Eq(CommunicationDeliveryLog.log_id, payload.log_id))
    if log is None:
        raise AppError(code="NOT_FOUND", message="Delivery log not found", status_code=404)
    if log.status != DeliveryStatus.FAILED:
        raise AppError(code="VALIDATION_ERROR", message="Only failed deliveries can be retried", status_code=422)
    if log.retry_count >= 3:
        raise AppError(code="FORBIDDEN", message="Maximum retries exceeded", status_code=403)
    log.status = DeliveryStatus.RETRYING
    log.retry_count += 1
    log.updated_at = utcnow()
    await log.save()
    log.status = DeliveryStatus.SENT
    log.error = None
    log.updated_at = utcnow()
    await log.save()
    return {"log_id": log.log_id, "status": log.status.value}


async def communication_report(scope: AccessScope) -> dict:
    authorize(scope, Permission.COMMUNICATION_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    published = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id), Eq(InstitutionAnnouncement.status, "published")).count()
    scheduled = await InstitutionAnnouncement.find(Eq(InstitutionAnnouncement.tenant_id, tenant_id), Eq(InstitutionAnnouncement.status, "scheduled")).count()
    failed = await CommunicationDeliveryLog.find(Eq(CommunicationDeliveryLog.tenant_id, tenant_id), Eq(CommunicationDeliveryLog.status, DeliveryStatus.FAILED)).count()
    sent = await CommunicationDeliveryLog.find(Eq(CommunicationDeliveryLog.tenant_id, tenant_id), Eq(CommunicationDeliveryLog.status, DeliveryStatus.SENT)).count()
    return {"published_announcements": published, "scheduled": scheduled, "deliveries_sent": sent, "deliveries_failed": failed}