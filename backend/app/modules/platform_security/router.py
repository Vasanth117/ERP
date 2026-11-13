"""Platform security and audit routes."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import AccessScope, get_access_scope, pagination_params
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.platform_security.schemas import (
    PlatformAuditExportRow,
    PlatformAuditLogRead,
    SecurityEventRead,
    SecurityEventUpdate,
    SecurityInvestigationNote,
)
from app.modules.platform_security.service import (
    add_investigation_note,
    export_platform_audit,
    get_platform_audit_log,
    get_security_event,
    list_platform_audit_logs,
    list_security_events,
    update_security_event,
)

router = APIRouter(tags=["platform-security"])


@router.get("/security/events", response_model=ApiResponse[Page[SecurityEventRead]])
async def list_security_events_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    category: Annotated[str | None, Query()] = None,
    severity: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    tenant_id: Annotated[str | None, Query()] = None,
    created_from: Annotated[datetime | None, Query()] = None,
    created_to: Annotated[datetime | None, Query()] = None,
) -> ApiResponse[Page[SecurityEventRead]]:
    data = await list_security_events(
        scope,
        pagination,
        category=category,
        severity=severity,
        status=status,
        tenant_id=None if tenant_id is None else to_object_id(tenant_id, "tenant id"),
        created_from=created_from,
        created_to=created_to,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/security/events/{event_id}", response_model=ApiResponse[SecurityEventRead])
async def get_security_event_route(
    event_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SecurityEventRead]:
    data = await get_security_event(scope, to_object_id(event_id, "event id"))
    return success_response(data, request_id=get_request_id())


@router.patch("/security/events/{event_id}", response_model=ApiResponse[SecurityEventRead])
async def patch_security_event_route(
    event_id: str,
    payload: SecurityEventUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SecurityEventRead]:
    data = await update_security_event(scope, to_object_id(event_id, "event id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/security/events/{event_id}/notes", response_model=ApiResponse[SecurityEventRead])
async def add_security_note_route(
    event_id: str,
    payload: SecurityInvestigationNote,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SecurityEventRead]:
    data = await add_investigation_note(scope, to_object_id(event_id, "event id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/audit", response_model=ApiResponse[Page[PlatformAuditLogRead]])
async def list_platform_audit_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    actor_id: Annotated[str | None, Query()] = None,
    module: Annotated[str | None, Query()] = None,
    action: Annotated[str | None, Query()] = None,
    created_from: Annotated[datetime | None, Query()] = None,
    created_to: Annotated[datetime | None, Query()] = None,
) -> ApiResponse[Page[PlatformAuditLogRead]]:
    data = await list_platform_audit_logs(
        scope,
        pagination,
        actor_id=to_object_id(actor_id, "actor id") if actor_id else None,
        module=module,
        action=action,
        created_from=created_from,
        created_to=created_to,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/audit/{audit_id}", response_model=ApiResponse[PlatformAuditLogRead])
async def get_platform_audit_route(
    audit_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlatformAuditLogRead]:
    data = await get_platform_audit_log(scope, to_object_id(audit_id, "audit id"))
    return success_response(data, request_id=get_request_id())


@router.get("/audit/export", response_model=ApiResponse[list[PlatformAuditExportRow]])
async def export_platform_audit_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    created_from: Annotated[datetime | None, Query()] = None,
    created_to: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=2000)] = 500,
) -> ApiResponse[list[PlatformAuditExportRow]]:
    data = await export_platform_audit(scope, created_from=created_from, created_to=created_to, limit=limit)
    return success_response(data, request_id=get_request_id())
