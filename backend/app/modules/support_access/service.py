"""Controlled support access workflow."""

import secrets
from datetime import timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize, authorize_support_scope
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.core.security import hash_refresh_token
from app.modules.platform_security.audit import record_platform_audit
from app.modules.platform_security.events import emit_security_event
from app.modules.support_access.models import (
    SUPPORT_ACCESS_SCOPES,
    SupportAccessActivity,
    SupportAccessApproval,
    SupportAccessRequest,
    SupportAccessSession,
)
from app.modules.support_access.schemas import (
    SupportAccessApprovalRequest,
    SupportAccessRequestCreate,
    SupportAccessRequestRead,
    SupportAccessSessionRead,
    SupportActivityRead,
)
from app.repositories.tenant_repository import TenantRepository

_tenant_repo = TenantRepository()


def _request_to_read(doc: SupportAccessRequest) -> SupportAccessRequestRead:
    return SupportAccessRequestRead.from_document(doc)


async def request_support_access(
    scope: AccessScope,
    payload: SupportAccessRequestCreate,
) -> SupportAccessRequestRead:
    authorize(scope, Permission.SUPPORT_ACCESS_REQUEST)
    invalid = set(payload.scopes) - SUPPORT_ACCESS_SCOPES
    if invalid:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Invalid support scopes: {', '.join(sorted(invalid))}",
            status_code=422,
        )
    tenant = await _tenant_repo.get_tenant(payload.tenant_id)
    if tenant is None:
        raise AppError(code="NOT_FOUND", message="College not found", status_code=404)

    doc = SupportAccessRequest(
        requester_id=scope.user_id,
        tenant_id=payload.tenant_id,
        reason=payload.reason,
        scopes=payload.scopes,
        duration_minutes=payload.duration_minutes,
    )
    await doc.insert()
    await emit_security_event(
        code="support_access_requested",
        category="support",
        title="Support access requested",
        description=payload.reason,
        tenant_id=payload.tenant_id,
        actor_id=scope.user_id,
        metadata={"scopes": payload.scopes},
    )
    await record_platform_audit(
        actor_id=scope.user_id,
        action="support_access.requested",
        module="support_access",
        resource_type="support_access_request",
        resource_id=str(doc.id),
        tenant_id=payload.tenant_id,
    )
    return _request_to_read(doc)


async def list_support_requests(scope: AccessScope) -> list[SupportAccessRequestRead]:
    authorize(scope, Permission.SUPPORT_ACCESS_APPROVE)
    rows = await SupportAccessRequest.find_all().sort("-created_at").limit(100).to_list()
    return [_request_to_read(row) for row in rows]


async def get_support_request(scope: AccessScope, request_id: PydanticObjectId) -> SupportAccessRequestRead:
    authorize(scope, Permission.SUPPORT_ACCESS_REQUEST)
    doc = await SupportAccessRequest.get(request_id)
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Support request not found", status_code=404)
    if doc.requester_id != scope.user_id and Permission.SUPPORT_ACCESS_APPROVE not in scope.effective_permissions:
        raise AppError(code="FORBIDDEN", message="Cannot view this request", status_code=403)
    return _request_to_read(doc)


async def decide_support_request(
    scope: AccessScope,
    request_id: PydanticObjectId,
    payload: SupportAccessApprovalRequest,
) -> SupportAccessRequestRead:
    authorize(scope, Permission.SUPPORT_ACCESS_APPROVE)
    doc = await SupportAccessRequest.get(request_id)
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Support request not found", status_code=404)
    if doc.status != "pending":
        raise AppError(code="CONFLICT", message="Request is not pending approval", status_code=409)
    doc.status = payload.decision
    doc.updated_at = utcnow()
    await doc.save()
    await SupportAccessApproval(
        request_id=request_id,
        approver_id=scope.user_id,
        decision=payload.decision,
        notes=payload.notes,
    ).insert()
    await record_platform_audit(
        actor_id=scope.user_id,
        action=f"support_access.{payload.decision}",
        module="support_access",
        resource_type="support_access_request",
        resource_id=str(doc.id),
        tenant_id=doc.tenant_id,
    )
    return _request_to_read(doc)


async def start_support_session(
    scope: AccessScope,
    request_id: PydanticObjectId,
) -> SupportAccessSessionRead:
    authorize(scope, Permission.SUPPORT_ACCESS_EXECUTE)
    doc = await SupportAccessRequest.get(request_id)
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Support request not found", status_code=404)
    if doc.status != "approved":
        raise AppError(code="CONFLICT", message="Request must be approved", status_code=409)
    if doc.requester_id != scope.user_id:
        raise AppError(code="FORBIDDEN", message="Only the requester may start this session", status_code=403)

    plain = secrets.token_urlsafe(48)
    session = SupportAccessSession(
        request_id=request_id,
        operator_id=scope.user_id,
        tenant_id=doc.tenant_id,
        token_hash=hash_refresh_token(plain),
        scopes=doc.scopes,
        expires_at=utcnow() + timedelta(minutes=doc.duration_minutes),
    )
    await session.insert()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="support_access.session_started",
        module="support_access",
        resource_type="support_access_session",
        resource_id=str(session.id),
        tenant_id=doc.tenant_id,
        metadata={"scopes": doc.scopes},
    )
    return SupportAccessSessionRead.from_document(session, token=plain)


async def get_support_session(scope: AccessScope, session_id: PydanticObjectId) -> SupportAccessSessionRead:
    authorize(scope, Permission.SUPPORT_ACCESS_EXECUTE)
    session = await SupportAccessSession.get(session_id)
    if session is None:
        raise AppError(code="NOT_FOUND", message="Session not found", status_code=404)
    if session.operator_id != scope.user_id and Permission.SUPPORT_ACCESS_APPROVE not in scope.effective_permissions:
        raise AppError(code="FORBIDDEN", message="Cannot view session", status_code=403)
    return SupportAccessSessionRead.from_document(session, token=None)


async def revoke_support_session(
    scope: AccessScope,
    session_id: PydanticObjectId,
    *,
    reason: str,
) -> SupportAccessSessionRead:
    authorize(scope, Permission.SUPPORT_ACCESS_APPROVE)
    session = await _active_session(session_id)
    session.revoked_at = utcnow()
    session.revoked_by = scope.user_id
    session.ended_at = utcnow()
    await session.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="support_access.session_revoked",
        module="support_access",
        resource_type="support_access_session",
        resource_id=str(session.id),
        tenant_id=session.tenant_id,
        metadata={"reason": reason},
    )
    return SupportAccessSessionRead.from_document(session, token=None)


async def terminate_support_session(scope: AccessScope, session_id: PydanticObjectId) -> SupportAccessSessionRead:
    authorize(scope, Permission.SUPPORT_ACCESS_EXECUTE)
    session = await _active_session(session_id)
    if session.operator_id != scope.user_id:
        raise AppError(code="FORBIDDEN", message="Cannot terminate this session", status_code=403)
    session.ended_at = utcnow()
    await session.save()
    await record_platform_audit(
        actor_id=scope.user_id,
        action="support_access.session_terminated",
        module="support_access",
        resource_type="support_access_session",
        resource_id=str(session.id),
        tenant_id=session.tenant_id,
    )
    return SupportAccessSessionRead.from_document(session, token=None)


async def _active_session(session_id: PydanticObjectId) -> SupportAccessSession:
    session = await SupportAccessSession.get(session_id)
    if session is None:
        raise AppError(code="NOT_FOUND", message="Session not found", status_code=404)
    if session.ended_at is not None or session.revoked_at is not None:
        raise AppError(code="CONFLICT", message="Session is not active", status_code=409)
    if session.expires_at <= utcnow():
        session.ended_at = utcnow()
        await session.save()
        raise AppError(code="SESSION_EXPIRED", message="Support session expired", status_code=410)
    return session


async def resolve_support_session_token(token: str) -> SupportAccessSession | None:
    token_hash = hash_refresh_token(token)
    session = await SupportAccessSession.find_one(Eq(SupportAccessSession.token_hash, token_hash))
    if session is None:
        return None
    if session.ended_at or session.revoked_at or session.expires_at <= utcnow():
        return None
    return session


async def record_support_activity(
    *,
    session_id: PydanticObjectId,
    operator_id: PydanticObjectId,
    tenant_id: PydanticObjectId,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    metadata: dict | None = None,
) -> None:
    await SupportAccessActivity(
        session_id=session_id,
        operator_id=operator_id,
        tenant_id=tenant_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata=metadata or {},
    ).insert()


async def list_support_activity(
    scope: AccessScope,
    session_id: PydanticObjectId,
) -> list[SupportActivityRead]:
    authorize(scope, Permission.PLATFORM_SECURITY_READ)
    rows = (
        await SupportAccessActivity.find(Eq(SupportAccessActivity.session_id, session_id))
        .sort("-created_at")
        .to_list()
    )
    return [SupportActivityRead.from_document(row) for row in rows]


async def enforce_support_tenant_scope(scope: AccessScope, tenant_id: PydanticObjectId, required_scope: str) -> None:
    authorize_support_scope(scope, required_scope)
    if scope.support_tenant_id is None or str(scope.support_tenant_id) != str(tenant_id):
        raise AppError(
            code="SUPPORT_TENANT_MISMATCH",
            message="Support session tenant does not match the requested college",
            status_code=403,
        )
