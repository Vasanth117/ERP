"""Hostel audit search and configuration management."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.models import InstitutionSettings
from app.modules.college_admin.security_admin_models import InstitutionAuditLog
from app.modules.department_admin.csv_safe import encode_csv_base64, rows_to_csv
from app.modules.hostel.audit_config_schemas import (
    HostelAuditDashboard,
    HostelAuditLogRead,
    HostelAuditSearch,
    HostelConfigRead,
    HostelConfigTransition,
    HostelConfigUpsert,
    HostelPolicyApprovalInput,
    HostelPolicyDefinitionUpsert,
    HostelPolicyRead,
)
from app.modules.hostel.config_models import (
    HostelConfigLifecycle,
    HostelConfiguration,
    HostelConfigurationVersion,
    HostelPolicyApproval,
    HostelPolicyDefinition,
    HostelPolicyVersion,
)
from app.modules.hostel.hostel_audit_constants import HOSTEL_AUDIT_MODULES
from app.modules.hostel.hostel_audit_helper import record_hostel_audit
from app.modules.hostel.policy import (
    authorize_hostel_audit_export,
    authorize_hostel_audit_read,
    authorize_hostel_config_manage,
    authorize_hostel_config_read,
    require_hostel_tenant_scope,
)


async def audit_dashboard(scope: AccessScope) -> HostelAuditDashboard:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_audit_read(scope)
    base = {"tenant_id": tenant_id, "module": {"$in": list(HOSTEL_AUDIT_MODULES)}}
    total = await InstitutionAuditLog.find(base).count()

    async def count_module(mod: str) -> int:
        return await InstitutionAuditLog.find({**base, "module": mod}).count()

    async def count_action_like(fragments: list[str]) -> int:
        count = 0
        rows = await InstitutionAuditLog.find(base).limit(5000).to_list()
        for r in rows:
            if any(f in r.action for f in fragments):
                count += 1
        return count

    return HostelAuditDashboard(
        total_entries=total,
        infrastructure_changes=await count_action_like(["infrastructure", "building", "room", "bed"]),
        allocation_changes=await count_action_like(["allocation", "transfer"]),
        resident_operations=await count_module("hostel_resident") + await count_action_like(["check_in", "check_out", "resident"]),
        visitor_activity=await count_module("hostel_visitor") + await count_action_like(["visitor"]),
        mess_billing=await count_module("hostel_mess") + await count_action_like(["billing", "mess"]),
        leave_outpass=await count_module("hostel_leave") + await count_action_like(["leave", "outpass", "gate", "outpass"]),
        maintenance_incidents=await count_module("hostel_maintenance") + await count_module("hostel_incident"),
        integration_config=await count_module("hostel_integration") + await count_module("hostel_configuration"),
    )


def _audit_read(row: InstitutionAuditLog) -> HostelAuditLogRead:
    return HostelAuditLogRead(
        action=row.action,
        module=row.module,
        resource_type=row.resource_type,
        resource_id=row.resource_id,
        actor_id=str(row.actor_id) if row.actor_id else None,
        outcome=row.outcome,
        metadata=dict(row.metadata or {}),
        created_at=row.created_at,
    )


async def search_audit(scope: AccessScope, pagination: Pagination, filters: HostelAuditSearch) -> Page[HostelAuditLogRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_audit_read(scope)
    q: dict = {"tenant_id": tenant_id, "module": {"$in": list(HOSTEL_AUDIT_MODULES)}}
    if filters.module:
        q["module"] = filters.module
    if filters.action:
        q["action"] = filters.action
    if filters.actor_id:
        q["actor_id"] = PydanticObjectId(filters.actor_id)
    if filters.resource_type:
        q["resource_type"] = filters.resource_type
    if filters.from_date or filters.to_date:
        created: dict = {}
        if filters.from_date:
            created["$gte"] = filters.from_date
        if filters.to_date:
            created["$lte"] = filters.to_date
        q["created_at"] = created
    rows = await InstitutionAuditLog.find(q).sort("-created_at").to_list()
    if filters.hostel_code:
        hc = filters.hostel_code.upper()
        rows = [r for r in rows if (r.metadata or {}).get("hostel_code") == hc]
    total = len(rows)
    skip = (pagination.page - 1) * pagination.page_size
    page_rows = rows[skip : skip + pagination.page_size]
    return Page(items=[_audit_read(r) for r in page_rows], total=total, page=pagination.page, page_size=pagination.page_size)


async def export_audit(scope: AccessScope, filters: HostelAuditSearch) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_audit_export(scope)
    page = await search_audit(scope, Pagination(page=1, page_size=5000), filters)
    dict_rows = [r.model_dump() for r in page.items]
    b64 = encode_csv_base64(rows_to_csv(dict_rows))
    await record_hostel_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.audit.export",
        module="hostel",
        resource_type="audit_export",
    )
    return {"row_count": len(dict_rows), "file_content_base64": b64}


async def upsert_config(scope: AccessScope, payload: HostelConfigUpsert) -> HostelConfigRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_config_manage(scope)
    hostel = payload.hostel_code.upper() if payload.hostel_code else None
    doc = await HostelConfiguration.find_one(
        {
            "tenant_id": tenant_id,
            "policy_section": payload.policy_section,
            "hostel_code": hostel,
        }
    )
    if doc:
        doc.payload = payload.payload
        doc.version += 1
        doc.effective_from = payload.effective_from
        doc.effective_to = payload.effective_to
        doc.change_reason = payload.change_reason
        doc.status = HostelConfigLifecycle.DRAFT
        doc.actor_id = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = await HostelConfiguration(
            tenant_id=tenant_id,
            policy_section=payload.policy_section,
            hostel_code=hostel,
            payload=payload.payload,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            change_reason=payload.change_reason,
            actor_id=scope.user_id,
        ).insert()
    await HostelConfigurationVersion(
        tenant_id=tenant_id,
        version_id=f"hcv_{uuid4().hex[:10]}",
        policy_section=doc.policy_section,
        hostel_code=doc.hostel_code,
        version=doc.version,
        payload_snapshot=doc.payload,
        status=doc.status,
        effective_from=doc.effective_from,
        actor_id=scope.user_id,
        change_reason=payload.change_reason,
    ).insert()
    if payload.policy_section == "visitor" and not hostel:
        settings = await InstitutionSettings.find_one(Eq(InstitutionSettings.tenant_id, tenant_id))
        if settings:
            merged = dict(settings.settings or {})
            hostel_root = dict(merged.get("hostel") or {})
            hostel_root["visitor_policy"] = {**hostel_root.get("visitor_policy", {}), **payload.payload}
            merged["hostel"] = hostel_root
            settings.settings = merged
            await settings.save()
    await record_hostel_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.configuration.upsert",
        module="hostel_configuration",
        resource_type="policy_section",
        resource_id=doc.policy_section,
        hostel_code=hostel,
    )
    return HostelConfigRead(
        policy_section=doc.policy_section,
        hostel_code=doc.hostel_code,
        version=doc.version,
        status=doc.status,
        payload=doc.payload,
        effective_from=doc.effective_from,
        updated_at=doc.updated_at,
    )


async def transition_config(scope: AccessScope, payload: HostelConfigTransition) -> HostelConfigRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_config_manage(scope)
    hostel = payload.hostel_code.upper() if payload.hostel_code else None
    doc = await HostelConfiguration.find_one(
        {"tenant_id": tenant_id, "policy_section": payload.policy_section, "hostel_code": hostel}
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Configuration not found", status_code=404)
    mapping = {
        "submit": HostelConfigLifecycle.UNDER_REVIEW,
        "approve": HostelConfigLifecycle.APPROVED,
        "publish": HostelConfigLifecycle.ACTIVE,
        "suspend": HostelConfigLifecycle.SUSPENDED,
        "archive": HostelConfigLifecycle.ARCHIVED,
    }
    if payload.action == "publish":
        today = date.today()
        if doc.effective_from and doc.effective_from > today:
            doc.status = HostelConfigLifecycle.SCHEDULED
        else:
            doc.status = HostelConfigLifecycle.ACTIVE
    else:
        doc.status = mapping[payload.action]
    doc.change_reason = payload.change_reason or doc.change_reason
    doc.updated_at = utcnow()
    await doc.save()
    return HostelConfigRead(
        policy_section=doc.policy_section,
        hostel_code=doc.hostel_code,
        version=doc.version,
        status=doc.status,
        payload=doc.payload,
        effective_from=doc.effective_from,
        updated_at=doc.updated_at,
    )


async def list_configurations(scope: AccessScope, hostel_code: str | None = None) -> list[HostelConfigRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_config_read(scope)
    q: dict = {"tenant_id": tenant_id}
    if hostel_code:
        q["hostel_code"] = hostel_code.upper()
    rows = await HostelConfiguration.find(q).sort("-updated_at").limit(200).to_list()
    return [
        HostelConfigRead(
            policy_section=r.policy_section,
            hostel_code=r.hostel_code,
            version=r.version,
            status=r.status,
            payload=r.payload,
            effective_from=r.effective_from,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


async def list_policy_definitions(scope: AccessScope) -> list[HostelPolicyRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_config_read(scope)
    rows = await HostelPolicyDefinition.find(Eq(HostelPolicyDefinition.tenant_id, tenant_id)).sort("-updated_at").limit(200).to_list()
    return [
        HostelPolicyRead(
            policy_code=r.policy_code,
            title=r.title,
            category=r.category,
            version=r.current_version,
            status=r.status,
        )
        for r in rows
    ]


async def get_config(scope: AccessScope, policy_section: str, hostel_code: str | None = None) -> HostelConfigRead | None:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_config_read(scope)
    doc = await HostelConfiguration.find_one(
        {"tenant_id": tenant_id, "policy_section": policy_section, "hostel_code": hostel_code.upper() if hostel_code else None}
    )
    if doc is None:
        return None
    return HostelConfigRead(
        policy_section=doc.policy_section,
        hostel_code=doc.hostel_code,
        version=doc.version,
        status=doc.status,
        payload=doc.payload,
        effective_from=doc.effective_from,
        updated_at=doc.updated_at,
    )


async def upsert_policy_definition(scope: AccessScope, payload: HostelPolicyDefinitionUpsert) -> HostelPolicyRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_config_manage(scope)
    code = payload.policy_code.strip().upper()
    doc = await HostelPolicyDefinition.find_one(Eq(HostelPolicyDefinition.tenant_id, tenant_id), Eq(HostelPolicyDefinition.policy_code, code))
    if doc:
        doc.title = payload.title
        doc.category = payload.category
        doc.description = payload.description
        doc.severity = payload.severity
        doc.hostel_codes = [h.upper() for h in payload.hostel_codes]
        doc.current_version += 1
        doc.status = HostelConfigLifecycle.UNDER_REVIEW
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = await HostelPolicyDefinition(
            tenant_id=tenant_id,
            policy_code=code,
            title=payload.title,
            category=payload.category,
            description=payload.description,
            severity=payload.severity,
            hostel_codes=[h.upper() for h in payload.hostel_codes],
        ).insert()
    await HostelPolicyVersion(
        tenant_id=tenant_id,
        policy_code=code,
        version=doc.current_version,
        rules=payload.rules,
        status=HostelConfigLifecycle.UNDER_REVIEW,
        actor_id=scope.user_id,
    ).insert()
    return HostelPolicyRead(policy_code=doc.policy_code, title=doc.title, category=doc.category, version=doc.current_version, status=doc.status)


async def approve_policy(scope: AccessScope, payload: HostelPolicyApprovalInput) -> HostelPolicyRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_config_manage(scope)
    doc = await HostelPolicyDefinition.find_one(
        Eq(HostelPolicyDefinition.tenant_id, tenant_id), Eq(HostelPolicyDefinition.policy_code, payload.policy_code.upper())
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Policy not found", status_code=404)
    decision = "approved" if payload.approve else "rejected"
    await HostelPolicyApproval(
        tenant_id=tenant_id,
        approval_id=f"hpa_{uuid4().hex[:10]}",
        policy_code=doc.policy_code,
        version=doc.current_version,
        decision=decision,
        actor_id=scope.user_id,
        comment=payload.comment,
    ).insert()
    doc.status = HostelConfigLifecycle.ACTIVE if payload.approve else HostelConfigLifecycle.ARCHIVED
    await doc.save()
    ver = await HostelPolicyVersion.find_one(
        {"tenant_id": tenant_id, "policy_code": doc.policy_code, "version": doc.current_version}
    )
    if ver:
        ver.status = doc.status
        await ver.save()
    return HostelPolicyRead(policy_code=doc.policy_code, title=doc.title, category=doc.category, version=doc.current_version, status=doc.status)