"""Resolve institution role overlays for tenant users."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.permissions import permissions_for_role as base_permissions_for_role
from app.modules.college_admin.identity_models import InstitutionPermission, InstitutionRole, InstitutionRoleAssignment


async def seed_tenant_permission_catalog(tenant_id: PydanticObjectId) -> None:
    from app.modules.college_admin.rbac_policy import INSTITUTION_ASSIGNABLE_PERMISSIONS

    existing = await InstitutionPermission.find(Eq(InstitutionPermission.tenant_id, tenant_id)).count()
    if existing > 0:
        return
    for perm in INSTITUTION_ASSIGNABLE_PERMISSIONS:
        await InstitutionPermission(
            tenant_id=tenant_id,
            permission_code=perm.value,
            description=perm.name.replace("_", " ").lower(),
            assignable=True,
            category=perm.value.split(":")[0] if ":" in perm.value else "general",
        ).insert()


async def institution_permission_overlay(
    tenant_id: PydanticObjectId,
    user_id: PydanticObjectId,
) -> frozenset[Permission]:
    assignments = await InstitutionRoleAssignment.find(
        Eq(InstitutionRoleAssignment.tenant_id, tenant_id),
        Eq(InstitutionRoleAssignment.user_id, user_id),
        Eq(InstitutionRoleAssignment.revoked_at, None),
    ).to_list()
    if not assignments:
        return frozenset()

    extra: set[Permission] = set()
    denied: set[Permission] = set()
    for assignment in assignments:
        role_doc = await InstitutionRole.get(assignment.institution_role_id)
        if role_doc is None or not role_doc.is_active:
            continue
        base = base_permissions_for_role(role_doc.base_role)
        extra |= base
        for code in role_doc.granted_permissions:
            if code in Permission._value2member_map_:
                extra.add(Permission(code))
        for code in role_doc.denied_permissions:
            if code in Permission._value2member_map_:
                denied.add(Permission(code))
    return frozenset(extra - denied)
