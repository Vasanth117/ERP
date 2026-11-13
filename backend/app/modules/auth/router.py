"""Login and current-user routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, TokenResponse, UserRead
from app.modules.auth.service import current_user_profile, login

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login_route(payload: LoginRequest) -> TokenResponse:
    return await login(payload)


@router.get("/me", response_model=UserRead)
async def me_route(user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return current_user_profile(user)
