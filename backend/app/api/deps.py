"""Request dependencies for identity and tenant scope."""

from typing import Annotated

from beanie import PydanticObjectId
from bson.errors import InvalidId
from fastapi import Depends, Header, Query, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.context import get_request_id, tenant_impersonation_var
from app.common.ids import to_object_id
from app.common.roles import DEPARTMENT_SCOPED_ROLES, Role
from app.common.schemas import Pagination
from app.core.exceptions import AppError
from app.core.security import CREDENTIALS_ERROR, decode_access_token
from app.modules.audit.service import record_audit
from app.authorization.permissions import Permission as Perm
from app.authorization.resolver import effective_permissions_for_user
from app.modules.auth.models import User
from app.modules.support_access.service import resolve_support_session_token
from app.modules.tenants.tenant_access import assert_tenant_allows_user_access

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise CREDENTIALS_ERROR
    payload = decode_access_token(credentials.credentials)
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise CREDENTIALS_ERROR
    try:
        user_id = PydanticObjectId(subject)
    except (InvalidId, TypeError, ValueError) as exc:
        raise CREDENTIALS_ERROR from exc
    user = await User.get(user_id)
    if user is None or not user.is_active:
        raise CREDENTIALS_ERROR
    return user


async def get_access_scope(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    x_tenant_id: Annotated[
        str | None,
        Header(alias="X-Tenant-Id", description="College id. Honored only for super admins."),
    ] = None,
    x_support_session: Annotated[
        str | None,
        Header(alias="X-Support-Session", description="Controlled support access token."),
    ] = None,
) -> AccessScope:
    effective_permissions = await effective_permissions_for_user(user)
    tenant_id = user.tenant_id
    impersonating = False
    support_session_id = None
    support_scopes: frozenset[str] = frozenset()
    support_tenant_id = None

    support_session = None
    if x_support_session:
        support_session = await resolve_support_session_token(x_support_session)
        if support_session is None:
            raise AppError(
                code="SUPPORT_SESSION_INVALID",
                message="Support session is invalid or expired",
                status_code=403,
            )
        if support_session.operator_id != user.id:
            raise AppError(code="FORBIDDEN", message="Support session does not belong to this operator", status_code=403)
        support_session_id = support_session.id
        support_scopes = frozenset(support_session.scopes)
        support_tenant_id = support_session.tenant_id
        tenant_id = support_session.tenant_id

    if x_tenant_id and support_session is None:
        if Perm.PLATFORM_TENANT_READ not in effective_permissions:
            raise AppError(
                code="FORBIDDEN",
                message="You cannot select a college context",
                status_code=403,
            )
        if Perm.SUPPORT_ACCESS_EXECUTE in effective_permissions and Perm.PLATFORM_TENANT_MANAGE not in effective_permissions:
            raise AppError(
                code="SUPPORT_SESSION_REQUIRED",
                message="Support operators must use an approved support session",
                status_code=403,
            )
        tenant_id = to_object_id(x_tenant_id, "X-Tenant-Id")
        impersonating = True
        tenant_impersonation_var.set(True)
        await record_audit(
            actor_id=user.id,
            action="platform.tenant_impersonation",
            resource_type="tenant",
            resource_id=str(tenant_id),
            tenant_id=tenant_id,
            metadata={"request_id": get_request_id()},
        )

    department_id = user.department_id if user.role in DEPARTMENT_SCOPED_ROLES else None
    effective_tenant_id = tenant_id if (impersonating or support_session is not None) else user.tenant_id
    await assert_tenant_allows_user_access(effective_tenant_id, role=user.role)
    return AccessScope(
        role=user.role,
        user_id=user.id,
        tenant_id=tenant_id,
        department_id=department_id,
        effective_permissions=effective_permissions,
        support_session_id=support_session_id,
        support_scopes=support_scopes,
        support_tenant_id=support_tenant_id,
    )


def require_roles(*roles: Role):
    allowed = set(roles)

    async def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise AppError(
                code="FORBIDDEN",
                message="You do not have permission for this action",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return user

    return checker


def require_permission(permission: Permission):
    async def checker(scope: Annotated[AccessScope, Depends(get_access_scope)]) -> AccessScope:
        authorize(scope, permission)
        return scope

    return checker


def pagination_params(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> Pagination:
    return Pagination(limit=limit, offset=offset)


def assert_tenant_access(scope: AccessScope, tenant_id: PydanticObjectId) -> None:
    if scope.is_super_admin and scope.tenant_id is None:
        return
    if scope.tenant_id is None or str(scope.tenant_id) != str(tenant_id):
        raise AppError(
            code="FORBIDDEN",
            message="You cannot access another college",
            status_code=403,
        )


async def enforce_tenant_entitlements(
    tenant_id: PydanticObjectId,
    *,
    module_code: str | None = None,
    limit_key: str | None = None,
    current_usage: int | None = None,
) -> None:
    """Call from tenant-scoped routers to enforce SaaS entitlements on the backend."""
    from app.modules.subscriptions.enforcement import (
        assert_module_entitled,
        check_entitlement_limit,
        enforce_active_subscription,
    )

    await enforce_active_subscription(tenant_id)
    if module_code:
        await assert_module_entitled(tenant_id, module_code)
    if limit_key is not None and current_usage is not None:
        await check_entitlement_limit(tenant_id, limit_key, current_usage)
