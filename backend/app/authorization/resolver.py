"""Effective permission resolution for platform and tenant users."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.authorization.platform_roles import PLATFORM_ROLE_PERMISSIONS
from app.common.roles import PLATFORM_ROLES, Role
from app.modules.auth.models import User
from app.modules.platform_identity.enums import PlatformRoleCode
from app.modules.platform_identity.models import PlatformOperatorProfile


async def get_platform_profile(user_id: PydanticObjectId) -> PlatformOperatorProfile | None:
    return await PlatformOperatorProfile.find_one(Eq(PlatformOperatorProfile.user_id, user_id))


async def effective_permissions_for_user(user: User) -> frozenset[Permission]:
    if user.tenant_id is not None:
        base = permissions_for_role(user.role)
        from app.modules.college_admin.rbac_service import institution_permission_overlay

        overlay = await institution_permission_overlay(user.tenant_id, user.id)
        return frozenset(base | overlay)

    if user.role == Role.SUPER_ADMIN:
        return PLATFORM_ROLE_PERMISSIONS[PlatformRoleCode.PLATFORM_OWNER]

    profile = await get_platform_profile(user.id)
    if profile is None:
        if user.role == Role.PLATFORM_ADMIN:
            return PLATFORM_ROLE_PERMISSIONS[PlatformRoleCode.PLATFORM_OPS_ADMIN]
        return frozenset()

    if profile.suspended_at is not None:
        return frozenset()

    base = PLATFORM_ROLE_PERMISSIONS.get(profile.platform_role_code, frozenset())
    granted = {Permission(code) for code in profile.granted_permissions if code in Permission._value2member_map_}
    denied = {Permission(code) for code in profile.denied_permissions if code in Permission._value2member_map_}
    return frozenset((base | granted) - denied)


def is_platform_operator(user: User) -> bool:
    return user.tenant_id is None and user.role in PLATFORM_ROLES
