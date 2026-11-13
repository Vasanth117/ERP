"""Login and current-user routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_access_scope, get_current_user
from app.common.envelope import ApiResponse, success_response
from app.common.context import get_request_id
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse, UserRead
from app.modules.auth.service import current_user_profile, login, logout, refresh_tokens

router = APIRouter()


@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login_route(payload: LoginRequest) -> ApiResponse[TokenResponse]:
    data = await login(payload)
    return success_response(data, request_id=get_request_id())


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh_route(payload: RefreshRequest) -> ApiResponse[TokenResponse]:
    data = await refresh_tokens(payload)
    return success_response(data, request_id=get_request_id())


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_route(
    payload: LogoutRequest,
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    await logout(user, payload.refresh_token)


@router.get("/me", response_model=ApiResponse[UserRead])
async def me_route(user: Annotated[User, Depends(get_current_user)]) -> ApiResponse[UserRead]:
    return success_response(current_user_profile(user), request_id=get_request_id())
