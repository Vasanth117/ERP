"""HR audit dashboard, search, access management."""

from datetime import timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.security_admin_models import InstitutionAuditLog
from app.modules.department_admin.csv_safe import encode_csv_base64, rows_to_csv
from app.modules.hr.enums import HrStaffActivityType, HrTemporaryAccessStatus
from app.modules.hr.hr_access_catalog import builtin_role_profiles
from app.modules.hr.hr_audit_integration import record_hr_audit
from app.modules.hr.hr_audit_models import (
    HrAccessReviewRecord,
    HrAccessScopeAssignment,
    HrAuditExportHistory,
    HrRolePermissionMapping,
    HrTemporaryAccessGrant,
)
from app.modules.hr.hr_audit_schemas import (
    AccessReviewCreate,
    AccessReviewRead,
    AccessScopeAssignmentRead,
    AccessScopeAssignmentUpsert,
    AuditExportRead,
    AuditExportRequest,
    HrAuditDashboard,
    HrAuditEntryRead,
    HrAuditSearch,
    RoleProfileRead,
    RoleProfileUpsert,
    TemporaryAccessCreate,
    TemporaryAccessRead,
)
from app.modules.hr.hr_settings_models import HrPolicyAcknowledgement
from app.modules.hr.hr_access_enforcement import assert_hr_employee_in_scope
from app.modules.hr.hr_sod import assert_separation_of_duties
from app.modules.hr.operational_models import HrStaffActivityLog
from app.modules.hr.policy import (
    authorize_hr_access_manage,
    authorize_hr_audit_export,
    authorize_hr_audit_read,
    require_hr_tenant_scope,
)


def _redact_metadata(meta: dict) -> dict:
    blocked = {"password", "token", "bank_account", "pan", "aadhaar", "salary_breakdown"}
    out = {}
    for k, v in (meta or {}).items():
        if k.lower() in blocked:
            out[k] = "[redacted]"
        elif isinstance(v, str) and len(v) > 500:
            out[k] = v[:500] + "…"
        else:
            out[k] = v
    return out


async def audit_dashboard(scope: AccessScope) -> HrAuditDashboard:
    authorize_hr_audit_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    dash = HrAuditDashboard()
    activities = await HrStaffActivityLog.find(Eq(HrStaffActivityLog.tenant_id, tenant_id)).to_list()
    dash.total_activities = len(activities)
    for row in activities:
        key = row.activity_type.value if hasattr(row.activity_type, "value") else str(row.activity_type)
        dash.by_activity_type[key] = dash.by_activity_type.get(key, 0) + 1
    dash.institution_audit_entries = await InstitutionAuditLog.find(
        Eq(InstitutionAuditLog.tenant_id, tenant_id),
        Eq(InstitutionAuditLog.module, "hr"),
    ).count()
    dash.pending_acknowledgements = await HrPolicyAcknowledgement.find(
        {"tenant_id": tenant_id, "acknowledged_at": None}
    ).count()
    dash.active_temporary_grants = await HrTemporaryAccessGrant.find(
        Eq(HrTemporaryAccessGrant.tenant_id, tenant_id),
        Eq(HrTemporaryAccessGrant.status, HrTemporaryAccessStatus.ACTIVE),
    ).count()
    return dash


def _matches_activity(row: HrStaffActivityLog, filters: HrAuditSearch) -> bool:
    if filters.employee_user_id and str(row.employee_user_id) != filters.employee_user_id:
        return False
    if filters.actor_id and str(row.actor_id) != filters.actor_id:
        return False
    if filters.department_id and str(row.department_id) != filters.department_id:
        return False
    if filters.activity_type and row.activity_type.value != filters.activity_type:
        return False
    if filters.date_from and row.created_at < filters.date_from:
        return False
    if filters.date_to and row.created_at > filters.date_to:
        return False
    return True


def _matches_institution(row: InstitutionAuditLog, filters: HrAuditSearch) -> bool:
    if filters.module and row.module != filters.module:
        return False
    if filters.actor_id and str(row.actor_id) != filters.actor_id:
        return False
    if filters.action_prefix and not row.action.startswith(filters.action_prefix):
        return False
    if filters.date_from and row.created_at < filters.date_from:
        return False
    if filters.date_to and row.created_at > filters.date_to:
        return False
    return True


async def search_audit(scope: AccessScope, pagination: Pagination, filters: HrAuditSearch) -> Page[HrAuditEntryRead]:
    authorize_hr_audit_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    if filters.employee_user_id:
        await assert_hr_employee_in_scope(scope, tenant_id, to_object_id(filters.employee_user_id, "employee_user_id"))
    items: list[HrAuditEntryRead] = []
    activities = await HrStaffActivityLog.find(Eq(HrStaffActivityLog.tenant_id, tenant_id)).sort("-created_at").to_list()
    for row in activities:
        if not _matches_activity(row, filters):
            continue
        items.append(
            HrAuditEntryRead(
                source="hr_activity",
                action=row.activity_type.value,
                summary=row.summary,
                actor_id=str(row.actor_id) if row.actor_id else None,
                employee_user_id=str(row.employee_user_id) if row.employee_user_id else None,
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                module="hr",
                outcome=None,
                metadata=_redact_metadata(row.metadata),
                created_at=row.created_at,
            )
        )
    inst_query = InstitutionAuditLog.find(Eq(InstitutionAuditLog.tenant_id, tenant_id))
    if filters.module:
        inst_rows = await inst_query.find(Eq(InstitutionAuditLog.module, filters.module)).sort("-created_at").to_list()
    else:
        inst_rows = await inst_query.sort("-created_at").to_list()
    for row in inst_rows:
        if row.module != "hr" and not (filters.module and filters.module == row.module):
            if filters.module is None and not row.action.startswith("hr."):
                continue
        if not _matches_institution(row, filters):
            continue
        items.append(
            HrAuditEntryRead(
                source="institution_audit",
                action=row.action,
                summary=row.action,
                actor_id=str(row.actor_id) if row.actor_id else None,
                employee_user_id=(row.metadata or {}).get("employee_user_id"),
                resource_type=row.resource_type,
                resource_id=row.resource_id,
                module=row.module,
                outcome=row.outcome,
                metadata=_redact_metadata(row.metadata),
                created_at=row.created_at,
            )
        )
    items.sort(key=lambda x: x.created_at, reverse=True)
    total = len(items)
    page = items[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=page, total=total, limit=pagination.limit, offset=pagination.offset)


async def employee_audit_timeline(scope: AccessScope, employee_user_id: str, pagination: Pagination) -> Page[HrAuditEntryRead]:
    authorize_hr_audit_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    eid = to_object_id(employee_user_id, "employee_user_id")
    await assert_hr_employee_in_scope(scope, tenant_id, eid)
    filters = HrAuditSearch(employee_user_id=employee_user_id)
    return await search_audit(scope, pagination, filters)


async def get_access_scope_assignment(scope: AccessScope, user_id: str) -> AccessScopeAssignmentRead | None:
    authorize_hr_access_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    uid = to_object_id(user_id, "user_id")
    doc = await HrAccessScopeAssignment.find_one(
        Eq(HrAccessScopeAssignment.tenant_id, tenant_id),
        Eq(HrAccessScopeAssignment.user_id, uid),
    )
    return AccessScopeAssignmentRead.from_doc(doc) if doc else None


async def export_audit(scope: AccessScope, payload: AuditExportRequest) -> AuditExportRead:
    authorize_hr_audit_export(scope)
    tenant_id = require_hr_tenant_scope(scope)
    pagination = Pagination(limit=200, offset=0)
    page = await search_audit(scope, pagination, payload.filters)
    fieldnames = ["source", "action", "summary", "actor_id", "employee_user_id", "created_at"]
    rows = [
        {
            "source": i.source,
            "action": i.action,
            "summary": i.summary,
            "actor_id": i.actor_id or "",
            "employee_user_id": i.employee_user_id or "",
            "created_at": i.created_at.isoformat(),
        }
        for i in page.items
    ]
    csv_text = rows_to_csv(rows, fieldnames)
    b64 = encode_csv_base64(csv_text)
    export_code = f"AUD-{uuid4().hex[:10]}"
    retention = utcnow() + timedelta(days=max(1, payload.retention_days))
    doc = HrAuditExportHistory(
        tenant_id=tenant_id,
        export_code=export_code,
        filters=payload.filters.model_dump(mode="json"),
        row_count=len(rows),
        file_content_base64=b64,
        retention_until=retention,
        actor_id=scope.user_id,
    )
    await doc.insert()
    await record_hr_audit(
        tenant_id,
        HrStaffActivityType.ACCESS_CHANGE,
        f"Audit export {export_code}",
        actor_id=scope.user_id,
        resource_type="hr_audit_export",
        resource_id=export_code,
    )
    return AuditExportRead.from_doc(doc, b64)


async def list_role_profiles(scope: AccessScope) -> list[RoleProfileRead]:
    authorize_hr_audit_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    custom = await HrRolePermissionMapping.find(Eq(HrRolePermissionMapping.tenant_id, tenant_id), Eq(HrRolePermissionMapping.is_active, True)).to_list()
    out = builtin_role_profiles()
    for row in custom:
        out.append(
            RoleProfileRead(
                role_profile_code=row.role_profile_code,
                title=row.title,
                permission_codes=row.permission_codes,
                platform_note="Institution overlay",
            )
        )
    return out


async def upsert_role_profile(scope: AccessScope, payload: RoleProfileUpsert) -> RoleProfileRead:
    authorize_hr_access_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    code = payload.role_profile_code.strip().lower()
    doc = await HrRolePermissionMapping.find_one(
        Eq(HrRolePermissionMapping.tenant_id, tenant_id),
        Eq(HrRolePermissionMapping.role_profile_code, code),
    )
    if doc is None:
        doc = HrRolePermissionMapping(tenant_id=tenant_id, role_profile_code=code, title=payload.title)
    doc.title = payload.title
    doc.permission_codes = payload.permission_codes
    doc.separation_rules = payload.separation_rules
    doc.actor_id = scope.user_id
    doc.updated_at = utcnow()
    if doc.id:
        await doc.save()
    else:
        await doc.insert()
    await record_hr_audit(
        tenant_id,
        HrStaffActivityType.ACCESS_CHANGE,
        f"Role profile {code} updated",
        actor_id=scope.user_id,
        resource_type="hr_role_profile",
        resource_id=code,
    )
    return RoleProfileRead(role_profile_code=doc.role_profile_code, title=doc.title, permission_codes=doc.permission_codes)


async def upsert_access_scope(scope: AccessScope, payload: AccessScopeAssignmentUpsert) -> AccessScopeAssignmentRead:
    authorize_hr_access_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    user_id = to_object_id(payload.user_id, "user_id")
    user = await User.find_one(Eq(User.id, user_id))
    if user is None or user.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="User not in tenant", status_code=422)
    doc = await HrAccessScopeAssignment.find_one(Eq(HrAccessScopeAssignment.tenant_id, tenant_id), Eq(HrAccessScopeAssignment.user_id, user_id))
    if doc is None:
        doc = HrAccessScopeAssignment(tenant_id=tenant_id, user_id=user_id)
    doc.scope_kind = payload.scope_kind
    doc.department_id = to_object_id(payload.department_id, "department_id") if payload.department_id else None
    doc.campus_id = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    doc.employee_user_ids = [to_object_id(x, "employee_user_id") for x in payload.employee_user_ids]
    doc.role_profile_code = payload.role_profile_code
    doc.actor_id = scope.user_id
    doc.updated_at = utcnow()
    if doc.id:
        await doc.save()
    else:
        await doc.insert()
    await record_hr_audit(
        tenant_id,
        HrStaffActivityType.ACCESS_CHANGE,
        f"Access scope updated for user {user_id}",
        actor_id=scope.user_id,
        resource_type="hr_access_assignment",
        resource_id=str(user_id),
    )
    return AccessScopeAssignmentRead.from_doc(doc)


async def create_temporary_access(scope: AccessScope, payload: TemporaryAccessCreate) -> TemporaryAccessRead:
    authorize_hr_access_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    subject = to_object_id(payload.subject_user_id, "subject_user_id")
    if payload.expires_at <= payload.starts_at:
        raise AppError(code="VALIDATION_ERROR", message="expires_at must be after starts_at", status_code=422)
    code = payload.grant_code.strip()
    existing = await HrTemporaryAccessGrant.find_one(Eq(HrTemporaryAccessGrant.tenant_id, tenant_id), Eq(HrTemporaryAccessGrant.grant_code, code))
    if existing:
        raise AppError(code="CONFLICT", message="Grant code exists", status_code=409)
    doc = HrTemporaryAccessGrant(
        tenant_id=tenant_id,
        grant_code=code,
        subject_user_id=subject,
        granted_permissions=payload.granted_permissions,
        scope=payload.scope,
        reason=payload.reason,
        starts_at=payload.starts_at,
        expires_at=payload.expires_at,
        actor_id=scope.user_id,
    )
    await doc.insert()
    return TemporaryAccessRead.from_doc(doc)


async def approve_temporary_access(scope: AccessScope, grant_id: str) -> TemporaryAccessRead:
    authorize_hr_access_manage(scope)
    assert_separation_of_duties(scope, acting_permission=Permission.HR_ACCESS_MANAGE)
    tenant_id = require_hr_tenant_scope(scope)
    gid = to_object_id(grant_id, "grant_id")
    doc = await HrTemporaryAccessGrant.find_one(Eq(HrTemporaryAccessGrant.tenant_id, tenant_id), Eq(HrTemporaryAccessGrant.id, gid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Grant not found", status_code=404)
    if doc.actor_id == scope.user_id:
        raise AppError(code="FORBIDDEN", message="Cannot approve own grant request", status_code=403)
    now = utcnow()
    starts = as_utc_aware(doc.starts_at)
    expires = as_utc_aware(doc.expires_at)
    doc.status = HrTemporaryAccessStatus.ACTIVE if starts <= now < expires else HrTemporaryAccessStatus.APPROVED
    doc.approver_id = scope.user_id
    doc.approved_at = now
    await doc.save()
    await record_hr_audit(
        tenant_id,
        HrStaffActivityType.ACCESS_CHANGE,
        f"Temporary access approved {doc.grant_code}",
        actor_id=scope.user_id,
        resource_type="hr_temp_access",
        resource_id=doc.grant_code,
    )
    return TemporaryAccessRead.from_doc(doc)


async def expire_temporary_grants(scope: AccessScope) -> int:
    authorize_hr_access_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    now = utcnow()
    grants = await HrTemporaryAccessGrant.find(
        Eq(HrTemporaryAccessGrant.tenant_id, tenant_id),
    ).to_list()
    count = 0
    for g in grants:
        if g.status in {HrTemporaryAccessStatus.ACTIVE, HrTemporaryAccessStatus.APPROVED} and as_utc_aware(g.expires_at) <= now:
            g.status = HrTemporaryAccessStatus.EXPIRED
            await g.save()
            count += 1
    return count


async def create_access_review(scope: AccessScope, payload: AccessReviewCreate) -> AccessReviewRead:
    authorize_hr_access_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    subject = to_object_id(payload.subject_user_id, "subject_user_id")
    doc = HrAccessReviewRecord(
        tenant_id=tenant_id,
        review_code=payload.review_code.strip(),
        subject_user_id=subject,
        reviewer_id=scope.user_id,
        findings=payload.findings,
        decision=payload.decision,
        notes=payload.notes,
        completed_at=utcnow(),
    )
    await doc.insert()
    await record_hr_audit(
        tenant_id,
        HrStaffActivityType.ACCESS_CHANGE,
        f"Access review {doc.review_code}",
        actor_id=scope.user_id,
        resource_type="hr_access_review",
        resource_id=doc.review_code,
    )
    return AccessReviewRead.from_doc(doc)


async def list_access_reviews(scope: AccessScope) -> list[AccessReviewRead]:
    authorize_hr_audit_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rows = await HrAccessReviewRecord.find(Eq(HrAccessReviewRecord.tenant_id, tenant_id)).sort("-created_at").to_list()
    return [AccessReviewRead.from_doc(r) for r in rows]