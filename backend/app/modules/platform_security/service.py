"""Security monitoring and platform audit queries."""

from datetime import datetime

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.platform_security.audit import record_platform_audit
from app.modules.platform_security.models import PlatformAuditLog, SecurityEvent
from app.modules.platform_security.schemas import (
    PlatformAuditExportRow,
    PlatformAuditLogRead,
    SecurityEventRead,
    SecurityEventUpdate,
    SecurityInvestigationNote,
)


async def list_security_events(
    scope: AccessScope,
    pagination: Pagination,
    *,
    category: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    tenant_id: PydanticObjectId | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> Page[SecurityEventRead]:
    authorize(scope, Permission.PLATFORM_SECURITY_READ)
    query = SecurityEvent.find_all()
    if category:
        query = SecurityEvent.find(Eq(SecurityEvent.category, category))
    if severity:
        query = query.find(Eq(SecurityEvent.severity, severity))
    if status:
        query = query.find(Eq(SecurityEvent.status, status))
    if tenant_id:
        query = query.find(Eq(SecurityEvent.tenant_id, tenant_id))
    if created_from:
        query = query.find(GTE(SecurityEvent.created_at, created_from))
    if created_to:
        query = query.find(LTE(SecurityEvent.created_at, created_to))
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[SecurityEventRead.from_document(row) for row in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_security_event(scope: AccessScope, event_id: PydanticObjectId) -> SecurityEventRead:
    authorize(scope, Permission.PLATFORM_SECURITY_READ)
    event = await SecurityEvent.get(event_id)
    if event is None:
        raise AppError(code="NOT_FOUND", message="Security event not found", status_code=404)
    return SecurityEventRead.from_document(event)


async def update_security_event(
    scope: AccessScope,
    event_id: PydanticObjectId,
    payload: SecurityEventUpdate,
) -> SecurityEventRead:
    authorize(scope, Permission.PLATFORM_SECURITY_MANAGE)
    event = await SecurityEvent.get(event_id)
    if event is None:
        raise AppError(code="NOT_FOUND", message="Security event not found", status_code=404)
    if payload.status is not None:
        event.status = payload.status
        if payload.status in {"resolved", "closed"}:
            event.resolved_at = utcnow()
    if payload.incident_reference is not None:
        event.incident_reference = payload.incident_reference
    if payload.escalated_to is not None:
        event.escalated_to = PydanticObjectId(payload.escalated_to)
    event.updated_at = utcnow()
    await event.save()
    return SecurityEventRead.from_document(event)


async def add_investigation_note(
    scope: AccessScope,
    event_id: PydanticObjectId,
    payload: SecurityInvestigationNote,
) -> SecurityEventRead:
    authorize(scope, Permission.PLATFORM_SECURITY_MANAGE)
    event = await SecurityEvent.get(event_id)
    if event is None:
        raise AppError(code="NOT_FOUND", message="Security event not found", status_code=404)
    event.investigation_notes.append(
        {"author_id": str(scope.user_id), "note": payload.note, "at": utcnow().isoformat()}
    )
    event.updated_at = utcnow()
    await event.save()
    return SecurityEventRead.from_document(event)


async def list_platform_audit_logs(
    scope: AccessScope,
    pagination: Pagination,
    *,
    actor_id: PydanticObjectId | None = None,
    module: str | None = None,
    action: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> Page[PlatformAuditLogRead]:
    authorize(scope, Permission.PLATFORM_AUDIT_READ)
    query = PlatformAuditLog.find_all()
    if actor_id:
        query = PlatformAuditLog.find(Eq(PlatformAuditLog.actor_id, actor_id))
    if module:
        query = query.find(Eq(PlatformAuditLog.module, module))
    if action:
        query = query.find(Eq(PlatformAuditLog.action, action))
    if created_from:
        query = query.find(GTE(PlatformAuditLog.created_at, created_from))
    if created_to:
        query = query.find(LTE(PlatformAuditLog.created_at, created_to))
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform_audit.queried",
        module="platform_security",
        resource_type="platform_audit_log",
        resource_id=None,
        metadata={"filters": {"module": module, "action": action}},
    )
    return Page(
        items=[PlatformAuditLogRead.from_document(row) for row in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_platform_audit_log(scope: AccessScope, audit_id: PydanticObjectId) -> PlatformAuditLogRead:
    authorize(scope, Permission.PLATFORM_AUDIT_READ)
    row = await PlatformAuditLog.get(audit_id)
    if row is None:
        raise AppError(code="NOT_FOUND", message="Audit record not found", status_code=404)
    return PlatformAuditLogRead.from_document(row)


async def export_platform_audit(
    scope: AccessScope,
    *,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    limit: int = 500,
) -> list[PlatformAuditExportRow]:
    authorize(scope, Permission.PLATFORM_AUDIT_EXPORT)
    query = PlatformAuditLog.find_all()
    if created_from:
        query = query.find(GTE(PlatformAuditLog.created_at, created_from))
    if created_to:
        query = query.find(LTE(PlatformAuditLog.created_at, created_to))
    rows = await query.sort("-created_at").limit(min(limit, 2000)).to_list()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="platform_audit.exported",
        module="platform_security",
        resource_type="platform_audit_log",
        resource_id=None,
        metadata={"row_count": len(rows)},
    )
    return [
        PlatformAuditExportRow(
            id=str(row.id),
            action=row.action,
            module=row.module,
            actor_id=str(row.actor_id) if row.actor_id else None,
            created_at=row.created_at,
            outcome=row.outcome,
        )
        for row in rows
    ]
