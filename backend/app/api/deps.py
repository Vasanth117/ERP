"""Request dependencies for identity and tenant scope."""

from dataclasses import dataclass
from typing import Annotated

from beanie import PydanticObjectId
from bson.errors import InvalidId
from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.ids import to_object_id
from app.common.roles import DEPARTMENT_SCOPED_ROLES, Role
from app.common.schemas import Pagination
from app.core.security import CREDENTIALS_ERROR, decode_access_token
from app.modules.auth.models import User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AccessScope:
    role: Role
    user_id: PydanticObjectId
    tenant_id: PydanticObjectId | None
    department_id: PydanticObjectId | None

    @property
    def is_super_admin(self) -> bool:
        return self.role == Role.SUPER_ADMIN


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
    user: Annotated[User, Depends(get_current_user)],
    x_tenant_id: Annotated[
        str | None,
        Header(alias="X-Tenant-Id", description="College id. Honored only for super admins."),
    ] = None,
) -> AccessScope:
    tenant_id = user.tenant_id
    if user.role == Role.SUPER_ADMIN:
        tenant_id = to_object_id(x_tenant_id, "X-Tenant-Id") if x_tenant_id else None
    department_id = user.department_id if user.role in DEPARTMENT_SCOPED_ROLES else None
    return AccessScope(
        role=user.role,
        user_id=user.id,
        tenant_id=tenant_id,
        department_id=department_id,
    )


def require_roles(*roles: Role):
    allowed = set(roles)

    async def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this action",
            )
        return user

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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access another college",
        )
