"""Platform operator management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import AccessScope, get_access_scope, pagination_params
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.platform_identity.schemas import (
    PlatformAccessReviewComplete,
    PlatformAccessReviewCreate,
    PlatformAccessReviewRead,
    PlatformPermissionsUpdate,
    PlatformRoleAssignRequest,
    PlatformSessionRead,
    PlatformSuspendRequest,
    PlatformUserCreate,
    PlatformUserInviteCreate,
    PlatformUserRead,
    PlatformUserUpdate,
)
from app.modules.platform_identity.service import (
    assign_platform_role,
    complete_access_review,
    create_access_review,
    create_platform_user,
    get_platform_user,
    invite_platform_user,
    list_active_sessions,
    list_inactive_operators,
    list_platform_users,
    reactivate_platform_user,
    revoke_user_sessions,
    suspend_platform_user,
    update_platform_permissions,
    update_platform_user,
)

router = APIRouter(prefix="/operators", tags=["platform-operators"])


@router.post("", response_model=ApiResponse[PlatformUserRead], status_code=status.HTTP_201_CREATED)
async def create_platform_user_route(
    payload: PlatformUserCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlatformUserRead]:
    data = await create_platform_user(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/invitations", response_model=ApiResponse[dict])
async def invite_platform_user_route(
    payload: PlatformUserInviteCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    invitation, token = await invite_platform_user(scope, payload)
    return success_response({"invitation": invitation.model_dump(), "token": token}, request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[PlatformUserRead]])
async def list_platform_users_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[PlatformUserRead]]:
    data = await list_platform_users(scope, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/inactive", response_model=ApiResponse[list[PlatformUserRead]])
async def inactive_platform_users_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    inactive_days: Annotated[int, Query(ge=30, le=365)] = 90,
) -> ApiResponse[list[PlatformUserRead]]:
    data = await list_inactive_operators(scope, inactive_days)
    return success_response(data, request_id=get_request_id())


@router.get("/{user_id}", response_model=ApiResponse[PlatformUserRead])
async def get_platform_user_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlatformUserRead]:
    data = await get_platform_user(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.patch("/{user_id}", response_model=ApiResponse[PlatformUserRead])
async def update_platform_user_route(
    user_id: str,
    payload: PlatformUserUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlatformUserRead]:
    data = await update_platform_user(scope, to_object_id(user_id, "user id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/{user_id}/role", response_model=ApiResponse[PlatformUserRead])
async def assign_platform_role_route(
    user_id: str,
    payload: PlatformRoleAssignRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlatformUserRead]:
    data = await assign_platform_role(scope, to_object_id(user_id, "user id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/{user_id}/permissions", response_model=ApiResponse[PlatformUserRead])
async def update_permissions_route(
    user_id: str,
    payload: PlatformPermissionsUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlatformUserRead]:
    data = await update_platform_permissions(scope, to_object_id(user_id, "user id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/{user_id}/suspend", response_model=ApiResponse[PlatformUserRead])
async def suspend_platform_user_route(
    user_id: str,
    payload: PlatformSuspendRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlatformUserRead]:
    data = await suspend_platform_user(scope, to_object_id(user_id, "user id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/{user_id}/reactivate", response_model=ApiResponse[PlatformUserRead])
async def reactivate_platform_user_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlatformUserRead]:
    data = await reactivate_platform_user(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.get("/{user_id}/sessions", response_model=ApiResponse[list[PlatformSessionRead]])
async def list_sessions_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[PlatformSessionRead]]:
    data = await list_active_sessions(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.post("/{user_id}/sessions/revoke", response_model=ApiResponse[dict])
async def revoke_sessions_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    count = await revoke_user_sessions(scope, to_object_id(user_id, "user id"))
    return success_response({"revoked": count}, request_id=get_request_id())


@router.post("/access-reviews", response_model=ApiResponse[PlatformAccessReviewRead], status_code=status.HTTP_201_CREATED)
async def create_access_review_route(
    payload: PlatformAccessReviewCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlatformAccessReviewRead]:
    data = await create_access_review(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/access-reviews/{review_id}/complete", response_model=ApiResponse[PlatformAccessReviewRead])
async def complete_access_review_route(
    review_id: str,
    payload: PlatformAccessReviewComplete,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PlatformAccessReviewRead]:
    data = await complete_access_review(scope, to_object_id(review_id, "review id"), payload)
    return success_response(data, request_id=get_request_id())
