"""Tenant-scoped audit and security administration."""

import hashlib
import json
from datetime import timedelta
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
from app.modules.audit.models import AuditLog
from app.modules.auth.models import User
from app.modules.auth.token_service import revoke_all_for_user
from app.modules.college_admin.audit_export_tokens import issue_audit_export_token, resolve_audit_export_token
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.security_admin_models import (
    InstitutionAccessReview,
    InstitutionAuditDataAccessLog,
    InstitutionAuditExport,
    InstitutionAuditLog,
    InstitutionLoginActivity,
    InstitutionSecurityEvent,
    InstitutionSecurityPolicy,
    SecurityIncidentStatus,
)
from app.modules.college_admin.security_admin_schemas import (
    AccessReviewCreate,
    AuditExportRead,
    AuditLogSearch,
    IntegrityCheckRead,
    InstitutionAuditLogRead,
    LoginActivityRead,
    SecurityEventRead,
    SecurityPolicyRead,
    SecurityPolicyUpdate,
    SecurityReportRead,
)
from app.modules.platform_security.models import SecurityEvent


def _hash_entry(payload: dict, previous_hash: str | None) -> str:
    raw = json.dumps({"previous": previous_hash, "payload": payload}, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _last_institution_audit_hash(tenant_id: PydanticObjectId) -> str | None:
    last = (
        await InstitutionAuditLog.find(Eq(InstitutionAuditLog.tenant_id, tenant_id))
        .sort("-created_at")
        .first_or_none()
    )
    return last.entry_hash if last else None


async def append_institution_audit(
    tenant_id: PydanticObjectId,
    *,
    actor_id: PydanticObjectId | None,
    action: str,
    module: str,
    resource_type: str,
    resource_id: str | None = None,
    outcome: str = "success",
    metadata: dict | None = None,
    source_audit_id: str | None = None,
) -> None:
    previous = await _last_institution_audit_hash(tenant_id)
    payload = {
        "tenant_id": str(tenant_id),
        "actor_id": str(actor_id) if actor_id else None,
        "action": action,
        "module": module,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "outcome": outcome,
        "metadata": metadata or {},
    }
    entry_hash = _hash_entry(payload, previous)
    await InstitutionAuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        module=module,
        resource_type=resource_type,
        resource_id=resource_id,
        outcome=outcome,
        metadata=metadata or {},
        source_audit_id=source_audit_id,
        entry_hash=entry_hash,
        previous_entry_hash=previous,
    ).insert()


async def _log_audit_data_access(
    tenant_id: PydanticObjectId,
    actor_id: PydanticObjectId,
    action: str,
    metadata: dict | None = None,
) -> None:
    await InstitutionAuditDataAccessLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        metadata=metadata or {},
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=actor_id,
        action=f"audit.data.{action}",
        module="security",
        resource_type="audit_log",
        metadata=metadata,
    )


async def get_security_policy(scope: AccessScope) -> InstitutionSecurityPolicy:
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionSecurityPolicy.find_one(
        Eq(InstitutionSecurityPolicy.tenant_id, tenant_id),
        Eq(InstitutionSecurityPolicy.policy_id, "default"),
    )
    if doc is None:
        doc = InstitutionSecurityPolicy(tenant_id=tenant_id)
        await doc.insert()
    return doc


async def read_security_policy(scope: AccessScope) -> SecurityPolicyRead:
    authorize(scope, Permission.SECURITY_ADMIN_READ)
    doc = await get_security_policy(scope)
    return SecurityPolicyRead(
        policy_id=doc.policy_id,
        max_failed_logins=doc.max_failed_logins,
        session_max_idle_minutes=doc.session_max_idle_minutes,
        require_mfa_privileged=doc.require_mfa_privileged,
        audit_retention_days=doc.audit_retention_days,
        block_self_approval=doc.block_self_approval,
        alert_on_privileged_access=doc.alert_on_privileged_access,
        updated_at=doc.updated_at,
    )


async def update_security_policy(scope: AccessScope, user: User, payload: SecurityPolicyUpdate) -> SecurityPolicyRead:
    authorize(scope, Permission.SECURITY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await get_security_policy(scope)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(doc, key, value)
    doc.updated_by = user.id
    doc.updated_at = utcnow()
    await doc.save()
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="security.policy.update",
        module="security",
        resource_type="security_policy",
        resource_id=doc.policy_id,
    )
    return await read_security_policy(scope)


def _audit_read(doc: InstitutionAuditLog) -> InstitutionAuditLogRead:
    return InstitutionAuditLogRead(
        id=str(doc.id),
        actor_id=str(doc.actor_id) if doc.actor_id else None,
        action=doc.action,
        module=doc.module,
        resource_type=doc.resource_type,
        resource_id=doc.resource_id,
        outcome=doc.outcome,
        entry_hash=doc.entry_hash,
        previous_entry_hash=doc.previous_entry_hash,
        created_at=doc.created_at,
    )


async def search_institution_audit_logs(
    scope: AccessScope,
    filters: AuditLogSearch,
    pagination: Pagination,
) -> Page[InstitutionAuditLogRead]:
    authorize(scope, Permission.SECURITY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    await _log_audit_data_access(tenant_id, scope.user_id, "search", metadata=filters.model_dump(mode="json"))
    mongo_filter: dict = {"tenant_id": tenant_id}
    if filters.actor_id:
        mongo_filter["actor_id"] = to_object_id(filters.actor_id, "actor_id")
    if filters.module:
        mongo_filter["module"] = filters.module
    if filters.resource_type:
        mongo_filter["resource_type"] = filters.resource_type
    if filters.action_prefix:
        mongo_filter["action"] = {"$regex": f"^{filters.action_prefix}"}
    if filters.date_from or filters.date_to:
        created: dict = {}
        if filters.date_from:
            created["$gte"] = filters.date_from
        if filters.date_to:
            created["$lte"] = filters.date_to
        mongo_filter["created_at"] = created
    total_inst = await InstitutionAuditLog.find(mongo_filter).count()
    inst_docs = (
        await InstitutionAuditLog.find(mongo_filter)
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [_audit_read(d) for d in inst_docs]
    if len(items) < pagination.limit:
        audit_filter: dict = {"tenant_id": tenant_id}
        if filters.actor_id:
            audit_filter["actor_id"] = to_object_id(filters.actor_id, "actor_id")
        if filters.resource_type:
            audit_filter["resource_type"] = filters.resource_type
        if filters.action_prefix:
            audit_filter["action"] = {"$regex": f"^{filters.action_prefix}"}
        if filters.date_from or filters.date_to:
            created = {}
            if filters.date_from:
                created["$gte"] = filters.date_from
            if filters.date_to:
                created["$lte"] = filters.date_to
            audit_filter["created_at"] = created
        platform_docs = (
            await AuditLog.find(audit_filter)
            .sort("-created_at")
            .skip(max(0, pagination.offset - total_inst))
            .limit(pagination.limit - len(items))
            .to_list()
        )
        for doc in platform_docs:
            module = filters.module or doc.resource_type.split("_")[0] if doc.resource_type else "general"
            if filters.module and filters.module != module:
                continue
            items.append(
                InstitutionAuditLogRead(
                    id=str(doc.id),
                    actor_id=str(doc.actor_id) if doc.actor_id else None,
                    action=doc.action,
                    module=module,
                    resource_type=doc.resource_type,
                    resource_id=doc.resource_id,
                    outcome=doc.outcome,
                    entry_hash="",
                    previous_entry_hash=None,
                    created_at=doc.created_at,
                )
            )
    total = total_inst + await AuditLog.find({"tenant_id": tenant_id}).count()
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def list_security_events(scope: AccessScope, pagination: Pagination) -> Page[SecurityEventRead]:
    authorize(scope, Permission.SECURITY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    await _log_audit_data_access(tenant_id, scope.user_id, "security_events")
    inst_total = await InstitutionSecurityEvent.find(Eq(InstitutionSecurityEvent.tenant_id, tenant_id)).count()
    inst_docs = (
        await InstitutionSecurityEvent.find(Eq(InstitutionSecurityEvent.tenant_id, tenant_id))
        .sort("-created_at")
        .skip(pagination.offset)
        .limit(pagination.limit)
        .to_list()
    )
    items = [
        SecurityEventRead(
            event_id=d.event_id,
            code=d.code,
            category=d.category,
            severity=d.severity,
            title=d.title,
            description=d.description,
            status=d.status,
            created_at=d.created_at,
        )
        for d in inst_docs
    ]
    if len(items) < pagination.limit:
        platform = (
            await SecurityEvent.find(Eq(SecurityEvent.tenant_id, tenant_id))
            .sort("-created_at")
            .skip(max(0, pagination.offset - inst_total))
            .limit(pagination.limit - len(items))
            .to_list()
        )
        for p in platform:
            items.append(
                SecurityEventRead(
                    event_id=p.incident_reference or str(p.id),
                    code=p.code,
                    category=p.category,
                    severity=p.severity,
                    title=p.title,
                    description=p.description,
                    status=SecurityIncidentStatus.OPEN if p.status == "open" else SecurityIncidentStatus.RESOLVED,
                    created_at=p.created_at,
                )
            )
    total = inst_total + await SecurityEvent.find(Eq(SecurityEvent.tenant_id, tenant_id)).count()
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def record_login_activity(
    tenant_id: PydanticObjectId,
    *,
    user_id: PydanticObjectId | None,
    email: str | None,
    success: bool,
    ip_address: str | None = None,
    failure_reason: str | None = None,
) -> None:
    await InstitutionLoginActivity(
        tenant_id=tenant_id,
        user_id=user_id,
        email=email,
        success=success,
        ip_address=ip_address,
        failure_reason=failure_reason,
    ).insert()


async def list_login_activity(scope: AccessScope, *, success_only: bool | None, pagination: Pagination) -> Page[LoginActivityRead]:
    authorize(scope, Permission.SECURITY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    await _log_audit_data_access(tenant_id, scope.user_id, "login_activity")
    query = InstitutionLoginActivity.find(Eq(InstitutionLoginActivity.tenant_id, tenant_id))
    if success_only is True:
        query = query.find(Eq(InstitutionLoginActivity.success, True))
    elif success_only is False:
        query = query.find(Eq(InstitutionLoginActivity.success, False))
    total = await query.count()
    docs = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            LoginActivityRead(
                user_id=str(d.user_id) if d.user_id else None,
                email=d.email,
                success=d.success,
                ip_address=d.ip_address,
                failure_reason=d.failure_reason,
                created_at=d.created_at,
            )
            for d in docs
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def revoke_authorized_sessions(scope: AccessScope, user_id: str) -> dict:
    authorize(scope, Permission.SECURITY_ADMIN_SESSION)
    tenant_id = require_college_tenant_scope(scope)
    uid = to_object_id(user_id, "user_id")
    user = await User.get(uid)
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="User not found", status_code=404)
    count = await revoke_all_for_user(uid)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="security.session.revoke",
        module="security",
        resource_type="user",
        resource_id=str(uid),
        metadata={"revoked_sessions": count},
    )
    return {"revoked_sessions": count}


async def verify_audit_integrity(scope: AccessScope) -> IntegrityCheckRead:
    authorize(scope, Permission.SECURITY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    docs = await InstitutionAuditLog.find(Eq(InstitutionAuditLog.tenant_id, tenant_id)).sort("+created_at").to_list()
    previous: str | None = None
    for doc in docs:
        payload = {
            "tenant_id": str(tenant_id),
            "actor_id": str(doc.actor_id) if doc.actor_id else None,
            "action": doc.action,
            "module": doc.module,
            "resource_type": doc.resource_type,
            "resource_id": doc.resource_id,
            "outcome": doc.outcome,
            "metadata": doc.metadata,
        }
        expected = _hash_entry(payload, doc.previous_entry_hash)
        if expected != doc.entry_hash or doc.previous_entry_hash != previous:
            return IntegrityCheckRead(
                tenant_id=str(tenant_id),
                entries_checked=len(docs),
                valid=False,
                broken_at=str(doc.id),
            )
        previous = doc.entry_hash
    return IntegrityCheckRead(
        tenant_id=str(tenant_id),
        entries_checked=len(docs),
        valid=True,
        broken_at=None,
    )


async def security_report(scope: AccessScope) -> SecurityReportRead:
    authorize(scope, Permission.SECURITY_ADMIN_READ)
    tenant_id = require_college_tenant_scope(scope)
    since = utcnow() - timedelta(hours=24)
    failed = await InstitutionLoginActivity.find(
        {
            "tenant_id": tenant_id,
            "success": False,
            "created_at": {"$gte": since},
        }
    ).count()
    open_events = await InstitutionSecurityEvent.find(
        Eq(InstitutionSecurityEvent.tenant_id, tenant_id),
        Eq(InstitutionSecurityEvent.status, SecurityIncidentStatus.OPEN),
    ).count()
    week = utcnow() - timedelta(days=7)
    privileged = await InstitutionAuditLog.find(
        {
            "tenant_id": tenant_id,
            "action": {"$regex": "privileged|finance|payroll|session"},
            "created_at": {"$gte": week},
        }
    ).count()
    integrity = await verify_audit_integrity(scope)
    return SecurityReportRead(
        failed_logins_24h=failed,
        open_security_events=open_events,
        privileged_operations_7d=privileged,
        audit_chain_valid=integrity.valid,
    )


async def export_audit_records(scope: AccessScope, user: User, filters: AuditLogSearch) -> AuditExportRead:
    authorize(scope, Permission.SECURITY_ADMIN_EXPORT)
    tenant_id = require_college_tenant_scope(scope)
    page = await search_institution_audit_logs(scope, filters, Pagination(limit=200, offset=0))
    export_id = f"aud_{uuid4().hex[:12]}"
    expires_at = utcnow() + timedelta(minutes=15)
    token = None
    token_hash = None
    try:
        token, token_hash = await issue_audit_export_token(
            tenant_id=str(tenant_id),
            user_id=str(user.id),
            export_id=export_id,
        )
    except Exception:
        pass
    await InstitutionAuditExport(
        tenant_id=tenant_id,
        export_id=export_id,
        actor_id=user.id,
        filter_summary=filters.model_dump(mode="json"),
        record_count=len(page.items),
        download_token_hash=token_hash,
        expires_at=expires_at,
    ).insert()
    await _log_audit_data_access(tenant_id, user.id, "export", metadata={"export_id": export_id})
    return AuditExportRead(export_id=export_id, record_count=len(page.items), download_token=token, expires_at=expires_at)


async def download_audit_export(scope: AccessScope, user: User, token: str) -> dict:
    authorize(scope, Permission.SECURITY_ADMIN_EXPORT)
    tenant_id = require_college_tenant_scope(scope)
    export_id = await resolve_audit_export_token(tenant_id=str(tenant_id), token=token, user_id=str(user.id))
    doc = await InstitutionAuditExport.find_one(
        Eq(InstitutionAuditExport.tenant_id, tenant_id),
        Eq(InstitutionAuditExport.export_id, export_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Export not found", status_code=404)
    page = await search_institution_audit_logs(scope, AuditLogSearch(**doc.filter_summary), Pagination(limit=200, offset=0))
    return {
        "export_id": export_id,
        "records": [item.model_dump(mode="json") for item in page.items],
    }


async def create_access_review(scope: AccessScope, user: User, payload: AccessReviewCreate) -> dict:
    authorize(scope, Permission.SECURITY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    rid = payload.review_id.strip()
    if await InstitutionAccessReview.find_one(
        Eq(InstitutionAccessReview.tenant_id, tenant_id),
        Eq(InstitutionAccessReview.review_id, rid),
    ):
        raise AppError(code="CONFLICT", message="Review id exists", status_code=409)
    subject = to_object_id(payload.subject_user_id, "subject_user_id")
    await InstitutionAccessReview(
        tenant_id=tenant_id,
        review_id=rid,
        subject_user_id=subject,
        reviewer_id=user.id,
        decision=payload.decision,
        notes=payload.notes,
    ).insert()
    await append_institution_audit(
        tenant_id,
        actor_id=user.id,
        action="security.access_review",
        module="security",
        resource_type="user",
        resource_id=str(subject),
        metadata={"decision": payload.decision},
    )
    return {"review_id": rid, "status": "recorded"}


async def ingest_tenant_security_event(
    tenant_id: PydanticObjectId,
    *,
    code: str,
    category: str,
    title: str,
    description: str,
    severity: str = "medium",
    actor_id: PydanticObjectId | None = None,
) -> None:
    await InstitutionSecurityEvent(
        tenant_id=tenant_id,
        event_id=f"evt_{uuid4().hex[:12]}",
        code=code,
        category=category,
        severity=severity,
        title=title,
        description=description,
        actor_id=actor_id,
    ).insert()