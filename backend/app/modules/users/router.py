"""User administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import AccessScope, get_access_scope, pagination_params, require_roles
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRead
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user, get_user, list_users

router = APIRouter()

admin_roles = require_roles(Role.SUPER_ADMIN, Role.COLLEGE_ADMIN)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_route(
    payload: UserCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(admin_roles)],
) -> UserRead:
    return await create_user(scope, payload)


@router.get("", response_model=Page[UserRead])
async def list_users_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(admin_roles)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> Page[UserRead]:
    return await list_users(scope, pagination)


@router.get("/{user_id}", response_model=UserRead)
async def get_user_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(admin_roles)],
) -> UserRead:
    return await get_user(scope, to_object_id(user_id, "user id"))
