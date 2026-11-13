"""Operational incident management."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.platform_ops.enums import IncidentStatus, assert_incident_transition
from app.modules.platform_ops.models import IncidentAssignment, IncidentHistory, PlatformIncident
from app.modules.platform_ops.schemas import (
    IncidentAssignRequest,
    IncidentCreate,
    IncidentNote,
    IncidentRead,
    IncidentStatusUpdate,
)
from app.modules.platform_security.audit import record_platform_audit
from app.modules.platform_security.events import emit_security_event


async def create_incident(scope: AccessScope, payload: IncidentCreate) -> IncidentRead:
    authorize(scope, Permission.PLATFORM_OPS_MANAGE)
    incident = PlatformIncident(
        title=payload.title,
        description=payload.description,
        severity=payload.severity,
        priority=payload.priority,
        created_by=scope.user_id,
        related_service=payload.related_service,
        related_tenant_id=payload.related_tenant_id,
    )
    await incident.insert()
    await _history(incident.id, None, incident.status.value, scope.user_id, "created")
    await record_platform_audit(
        actor_id=scope.user_id,
        action="incident.created",
        module="platform_ops",
        resource_type="platform_incident",
        resource_id=str(incident.id),
        tenant_id=payload.related_tenant_id,
    )
    return IncidentRead.from_document(incident)


async def list_incidents(scope: AccessScope, pagination: Pagination) -> Page[IncidentRead]:
    authorize(scope, Permission.PLATFORM_OPS_READ)
    total = await PlatformIncident.find_all().count()
    rows = (
        await PlatformIncident.find_all()
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    return Page(
        items=[IncidentRead.from_document(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_incident(scope: AccessScope, incident_id: PydanticObjectId) -> IncidentRead:
    authorize(scope, Permission.PLATFORM_OPS_READ)
    incident = await PlatformIncident.get(incident_id)
    if incident is None:
        raise AppError(code="NOT_FOUND", message="Incident not found", status_code=404)
    return IncidentRead.from_document(incident)


async def assign_incident(
    scope: AccessScope,
    incident_id: PydanticObjectId,
    payload: IncidentAssignRequest,
) -> IncidentRead:
    authorize(scope, Permission.PLATFORM_OPS_MANAGE)
    incident = await PlatformIncident.get(incident_id)
    if incident is None:
        raise AppError(code="NOT_FOUND", message="Incident not found", status_code=404)
    incident.assignee_id = payload.assignee_id
    incident.updated_at = utcnow()
    await incident.save()
    await IncidentAssignment(
        incident_id=incident_id,
        assignee_id=payload.assignee_id,
        assigned_by=scope.user_id,
    ).insert()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="incident.assigned",
        module="platform_ops",
        resource_type="platform_incident",
        resource_id=str(incident.id),
        metadata={"assignee_id": str(payload.assignee_id)},
    )
    return IncidentRead.from_document(incident)


async def update_incident_status(
    scope: AccessScope,
    incident_id: PydanticObjectId,
    payload: IncidentStatusUpdate,
) -> IncidentRead:
    authorize(scope, Permission.PLATFORM_OPS_MANAGE)
    incident = await PlatformIncident.get(incident_id)
    if incident is None:
        raise AppError(code="NOT_FOUND", message="Incident not found", status_code=404)
    try:
        assert_incident_transition(incident.status, payload.status)
    except ValueError as exc:
        raise AppError(code="INVALID_TRANSITION", message=str(exc), status_code=409) from exc

    previous = incident.status.value
    incident.status = payload.status
    if payload.priority is not None:
        incident.priority = payload.priority
    if payload.status == IncidentStatus.RESOLVED:
        incident.resolved_at = utcnow()
    if payload.status == IncidentStatus.CLOSED:
        incident.closed_at = utcnow()
    incident.updated_at = utcnow()
    await incident.save()
    await _history(incident.id, previous, payload.status.value, scope.user_id, payload.note)
    if payload.status == IncidentStatus.CLOSED and incident.severity.value in {"high", "critical"}:
        await emit_security_event(
            code="incident_closed",
            category="operations",
            title="Incident closed",
            description=incident.title,
            severity=incident.severity.value,
            actor_id=scope.user_id,
        )
    return IncidentRead.from_document(incident)


async def add_incident_note(
    scope: AccessScope,
    incident_id: PydanticObjectId,
    payload: IncidentNote,
) -> IncidentRead:
    authorize(scope, Permission.PLATFORM_OPS_MANAGE)
    incident = await PlatformIncident.get(incident_id)
    if incident is None:
        raise AppError(code="NOT_FOUND", message="Incident not found", status_code=404)
    incident.investigation_notes.append(
        {"author_id": str(scope.user_id), "note": payload.note, "at": utcnow().isoformat()}
    )
    incident.updated_at = utcnow()
    await incident.save()
    return IncidentRead.from_document(incident)


async def get_incident_history(
    scope: AccessScope,
    incident_id: PydanticObjectId,
) -> list[dict]:
    authorize(scope, Permission.PLATFORM_OPS_READ)
    rows = (
        await IncidentHistory.find(Eq(IncidentHistory.incident_id, incident_id))
        .sort("-created_at")
        .to_list()
    )
    return [
        {
            "from_status": row.from_status,
            "to_status": row.to_status,
            "actor_id": str(row.actor_id) if row.actor_id else None,
            "note": row.note,
            "created_at": row.created_at.isoformat(),
        }
        for row in rows
    ]


async def _history(
    incident_id: PydanticObjectId,
    from_status: str | None,
    to_status: str,
    actor_id: PydanticObjectId,
    note: str | None,
) -> None:
    await IncidentHistory(
        incident_id=incident_id,
        from_status=from_status,
        to_status=to_status,
        actor_id=actor_id,
        note=note,
    ).insert()
