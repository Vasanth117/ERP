"""User administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import AccessScope, get_access_scope, pagination_params, require_roles
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.roles import Role
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.auth.schemas import UserRead
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user, get_user, list_users

router = APIRouter()

admin_roles = require_roles(Role.SUPER_ADMIN, Role.COLLEGE_ADMIN)


@router.post("", response_model=ApiResponse[UserRead], status_code=status.HTTP_201_CREATED)
async def create_user_route(
    payload: UserCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(admin_roles)],
) -> ApiResponse[UserRead]:
    data = await create_user(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[UserRead]])
async def list_users_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(admin_roles)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[UserRead]]:
    data = await list_users(scope, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/{user_id}", response_model=ApiResponse[UserRead])
async def get_user_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(admin_roles)],
) -> ApiResponse[UserRead]:
    data = await get_user(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())
