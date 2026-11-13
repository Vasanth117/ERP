"""Institution custom roles and permission catalogue."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.core.exceptions import AppError
from app.modules.audit.service import record_audit
from app.modules.college_admin.identity_models import InstitutionPermission, InstitutionRole
from app.modules.college_admin.identity_schemas import (
    InstitutionRoleCreate,
    InstitutionRoleRead,
    InstitutionRoleUpdate,
    PermissionRead,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.college_admin.rbac_policy import validate_custom_permissions
from app.modules.college_admin.rbac_service import seed_tenant_permission_catalog


async def list_permissions(scope: AccessScope) -> list[PermissionRead]:
    authorize(scope, Permission.INSTITUTION_ROLE_READ)
    tenant_id = require_college_tenant_scope(scope)
    await seed_tenant_permission_catalog(tenant_id)
    rows = await InstitutionPermission.find(Eq(InstitutionPermission.tenant_id, tenant_id)).sort("+permission_code").to_list()
    return [
        PermissionRead(
            permission_code=row.permission_code,
            description=row.description,
            assignable=row.assignable,
            category=row.category,
        )
        for row in rows
    ]


async def list_institution_roles(scope: AccessScope) -> list[InstitutionRoleRead]:
    authorize(scope, Permission.INSTITUTION_ROLE_READ)
    tenant_id = require_college_tenant_scope(scope)
    rows = await InstitutionRole.find(Eq(InstitutionRole.tenant_id, tenant_id)).sort("+role_code").to_list()
    return [InstitutionRoleRead.from_document(row) for row in rows]


async def create_institution_role(scope: AccessScope, payload: InstitutionRoleCreate) -> InstitutionRoleRead:
    authorize(scope, Permission.INSTITUTION_ROLE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.role_code.upper()
    existing = await InstitutionRole.find_one(Eq(InstitutionRole.tenant_id, tenant_id), Eq(InstitutionRole.role_code, code))
    if existing is not None:
        raise AppError(code="CONFLICT", message="Role code already exists", status_code=409)
    try:
        granted, denied = validate_custom_permissions(
            payload.granted_permissions,
            payload.denied_permissions,
            base_role=payload.base_role,
        )
    except (ValueError, TypeError) as exc:
        raise AppError(code="VALIDATION_ERROR", message=str(exc), status_code=422) from exc

    doc = InstitutionRole(
        tenant_id=tenant_id,
        role_code=code,
        name=payload.name,
        description=payload.description,
        base_role=payload.base_role,
        granted_permissions=granted,
        denied_permissions=denied,
        updated_by=scope.user_id,
    )
    await doc.insert()
    await record_audit(
        actor_id=scope.user_id,
        action="institution.role.created",
        resource_type="institution_role",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
        metadata={"role_code": code},
    )
    return InstitutionRoleRead.from_document(doc)


async def update_institution_role(
    scope: AccessScope,
    role_id: PydanticObjectId,
    payload: InstitutionRoleUpdate,
) -> InstitutionRoleRead:
    authorize(scope, Permission.INSTITUTION_ROLE_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    doc = await InstitutionRole.get(role_id)
    if doc is None or doc.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Institution role not found", status_code=404)
    if doc.is_system:
        raise AppError(code="FORBIDDEN", message="System roles cannot be modified", status_code=403)

    if payload.name is not None:
        doc.name = payload.name
    if payload.description is not None:
        doc.description = payload.description
    if payload.is_active is not None:
        doc.is_active = payload.is_active
    if payload.granted_permissions is not None or payload.denied_permissions is not None:
        granted = payload.granted_permissions if payload.granted_permissions is not None else doc.granted_permissions
        denied = payload.denied_permissions if payload.denied_permissions is not None else doc.denied_permissions
        try:
            doc.granted_permissions, doc.denied_permissions = validate_custom_permissions(
                granted,
                denied,
                base_role=doc.base_role,
            )
        except (ValueError, TypeError) as exc:
            raise AppError(code="VALIDATION_ERROR", message=str(exc), status_code=422) from exc

    doc.version += 1
    doc.updated_at = utcnow()
    doc.updated_by = scope.user_id
    await doc.save()
    await record_audit(
        actor_id=scope.user_id,
        action="institution.role.updated",
        resource_type="institution_role",
        resource_id=str(doc.id),
        tenant_id=tenant_id,
    )
    return InstitutionRoleRead.from_document(doc)
