"""Department Admin — read-only audit and security visibility."""

from __future__ import annotations

import base64
import re
from collections import Counter
from datetime import timedelta

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, GTE, LTE

from app.api.deps import AccessScope
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.audit.models import AuditLog
from app.modules.department_admin.audit_helpers import record_department_audit
from app.modules.auth.models import User
from app.modules.department_admin.audit_redaction import action_category, redact_audit_metadata
from app.modules.department_admin.csv_safe import rows_to_csv
from app.modules.department_admin.models import DepartmentAuditExportJob, DepartmentSettingHistory
from app.modules.department_admin.phase9_schemas import (
    AuditExportBody,
    AuditExportRead,
    AuditListFilters,
    AuditSummaryRead,
    ConfigurationChangeRead,
    DepartmentAuditRead,
    EffectivePermissionsRead,
    SecurityEventDeptRead,
)
from app.modules.department_admin.policy import resolve_authorized_department
from app.modules.platform_security.models import SecurityEvent

EXPORT_RETENTION_HOURS = 72
_DEPT_ACTION_PREFIX = "^department\\."
_VISIBLE_SECURITY_CATEGORIES = frozenset({"auth", "access", "authorization", "account", "session"})


def _dept_audit_filter(tenant_id: PydanticObjectId, central_id: PydanticObjectId) -> dict:
    """Scope to department audit rows (canonical and legacy metadata keys)."""
    dept = str(central_id)
    return {
        "tenant_id": tenant_id,
        "$or": [
            {"metadata.central_department_id": dept},
            {"metadata.department_id": dept},
        ],
    }


def _audit_read(entry: AuditLog, actor_role: str | None = None) -> DepartmentAuditRead:
    meta = redact_audit_metadata(entry.metadata)
    return DepartmentAuditRead(
        event_id=str(entry.id),
        actor_id=str(entry.actor_id) if entry.actor_id else None,
        actor_role=actor_role or meta.get("actor_role"),
        action=entry.action,
        action_category=action_category(entry.action),
        resource_type=entry.resource_type,
        resource_id=entry.resource_id,
        outcome=entry.outcome,
        request_id=entry.request_id,
        metadata=meta,
        created_at=entry.created_at,
    )


async def _apply_audit_filters(query, filters: AuditListFilters):
    if filters.date_from:
        query = query.find(GTE(AuditLog.created_at, filters.date_from))
    if filters.date_to:
        query = query.find(LTE(AuditLog.created_at, filters.date_to))
    if filters.actor_id:
        query = query.find(Eq(AuditLog.actor_id, to_object_id(filters.actor_id, "actor_id")))
    if filters.action:
        query = query.find(Eq(AuditLog.action, filters.action))
    elif filters.action_category:
        pattern = f"^department\\.{re.escape(filters.action_category)}\\."
        query = query.find({"action": {"$regex": pattern}})
    if filters.resource_type:
        query = query.find(Eq(AuditLog.resource_type, filters.resource_type))
    if filters.outcome:
        query = query.find(Eq(AuditLog.outcome, filters.outcome))
    if filters.resource_id:
        query = query.find(Eq(AuditLog.resource_id, filters.resource_id))
    return query


async def list_department_audit(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
    filters: AuditListFilters,
) -> Page[DepartmentAuditRead]:
    authorize(scope, Permission.DEPARTMENT_AUDIT_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    base = AuditLog.find(_dept_audit_filter(tenant_id, central_id))
    base = await _apply_audit_filters(base, filters)
    total = await base.count()
    rows = await base.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[_audit_read(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def get_department_audit_event(scope: AccessScope, user: User, event_id: str) -> DepartmentAuditRead:
    authorize(scope, Permission.DEPARTMENT_AUDIT_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    row = await AuditLog.get(to_object_id(event_id, "event_id"))
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Audit event not found", status_code=404)
    dept = str(central_id)
    if row.metadata.get("central_department_id") != dept and row.metadata.get("department_id") != dept:
        raise AppError(code="NOT_FOUND", message="Audit event not found", status_code=404)
    return _audit_read(row)


async def audit_summary(scope: AccessScope, user: User, filters: AuditListFilters) -> AuditSummaryRead:
    authorize(scope, Permission.DEPARTMENT_AUDIT_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = AuditLog.find(_dept_audit_filter(tenant_id, central_id))
    query = await _apply_audit_filters(query, filters)
    rows = await query.sort("-created_at").limit(5000).to_list()
    outcomes = Counter(r.outcome for r in rows)
    categories = Counter(action_category(r.action) for r in rows)
    return AuditSummaryRead(
        total_events=len(rows),
        by_outcome=dict(outcomes),
        by_action_category=dict(categories),
        window_start=filters.date_from,
        window_end=filters.date_to,
        advisory=(
            "Audit visibility requires metadata.central_department_id on canonical audit_logs. "
            "Older department actions without this field are not listed until enriched."
        ),
    )


async def approval_audit_history(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
    filters: AuditListFilters,
) -> Page[DepartmentAuditRead]:
    authorize(scope, Permission.DEPARTMENT_AUDIT_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = AuditLog.find(_dept_audit_filter(tenant_id, central_id))
    query = query.find({"action": {"$regex": r"^department\.request\."}})
    query = await _apply_audit_filters(query, filters)
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[_audit_read(r) for r in rows],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def list_department_security_events(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[SecurityEventDeptRead]:
    authorize(scope, Permission.DEPARTMENT_AUDIT_READ)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = SecurityEvent.find(Eq(SecurityEvent.tenant_id, tenant_id))
    rows_all = await query.sort("-created_at").limit(2000).to_list()
    scoped: list[SecurityEvent] = []
    for row in rows_all:
        if row.category not in _VISIBLE_SECURITY_CATEGORIES:
            continue
        meta_dept = row.metadata.get("central_department_id")
        if meta_dept is not None and meta_dept != str(central_id):
            continue
        if meta_dept is None and row.category not in {"access", "authorization"}:
            continue
        scoped.append(row)
    total = len(scoped)
    page = scoped[pagination.offset : pagination.offset + pagination.limit]
    return Page(
        items=[
            SecurityEventDeptRead(
                event_id=str(r.id),
                code=r.code,
                category=r.category,
                severity=r.severity,
                title=r.title,
                description=r.description[:500],
                status=r.status,
                created_at=r.created_at,
            )
            for r in page
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def configuration_change_history(
    scope: AccessScope,
    user: User,
    pagination: Pagination,
) -> Page[ConfigurationChangeRead]:
    authorize(scope, Permission.DEPARTMENT_AUDIT_READ)
    central_id, institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = DepartmentSettingHistory.find(
        Eq(DepartmentSettingHistory.tenant_id, tenant_id),
        Eq(DepartmentSettingHistory.institution_department_id, institution.id),
    )
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[
            ConfigurationChangeRead(
                setting_key=r.setting_key,
                previous_value=r.previous_value,
                new_value=r.new_value,
                changed_by=str(r.changed_by) if r.changed_by else None,
                changed_at=r.created_at,
            )
            for r in rows
        ],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


def effective_department_permissions(scope: AccessScope) -> EffectivePermissionsRead:
    authorize(scope, Permission.DEPARTMENT_AUDIT_READ)
    perms = sorted(p.value for p in scope.effective_permissions if p.value.startswith("department:"))
    return EffectivePermissionsRead(
        permissions=perms,
        advisory="Read-only view of effective department-scoped permissions; self-grant is not permitted.",
    )


async def export_department_audit(scope: AccessScope, user: User, body: AuditExportBody) -> AuditExportRead:
    authorize(scope, Permission.DEPARTMENT_AUDIT_EXPORT)
    central_id, _institution = await resolve_authorized_department(scope, user)
    tenant_id = scope.tenant_id
    assert tenant_id is not None

    query = AuditLog.find(_dept_audit_filter(tenant_id, central_id))
    query = await _apply_audit_filters(query, body.filters)
    rows = await query.sort("-created_at").limit(body.max_rows).to_list()
    export_rows = [
        {
            "event_id": str(r.id),
            "created_at": r.created_at.isoformat(),
            "actor_id": str(r.actor_id) if r.actor_id else "",
            "action": r.action,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id or "",
            "outcome": r.outcome,
            "request_id": r.request_id or "",
        }
        for r in rows
    ]
    csv_text = rows_to_csv(export_rows, list(export_rows[0].keys()) if export_rows else ["event_id"])
    b64 = base64.b64encode(csv_text.encode("utf-8")).decode("ascii")
    expires = utcnow() + timedelta(hours=EXPORT_RETENTION_HOURS)
    job = DepartmentAuditExportJob(
        tenant_id=tenant_id,
        central_department_id=central_id,
        requested_by=user.id,
        filters=body.filters.model_dump(mode="json"),
        row_count=len(rows),
        file_content_base64=b64,
        expires_at=expires,
    )
    await job.insert()
    await record_department_audit(
        actor_id=user.id,
        action="department.audit.exported",
        resource_type="department_audit_export",
        resource_id=str(job.id),
        tenant_id=tenant_id,
        central_department_id=central_id,
        metadata={"row_count": len(rows)},
    )
    return AuditExportRead(
        export_id=str(job.id),
        row_count=len(rows),
        content_type="text/csv",
        file_name=f"department_audit_{central_id}.csv",
        content_base64=b64,
        expires_at=expires,
    )