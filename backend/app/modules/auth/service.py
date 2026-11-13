"""Login checks."""

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    verify_password,
)
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, TokenResponse, UserRead


async def login(payload: LoginRequest) -> TokenResponse:
    email = str(payload.email).lower()
    user = await User.find_one(User.email == email)
    password_hash = user.hashed_password if user is not None else DUMMY_PASSWORD_HASH
    password_ok = verify_password(payload.password, password_hash)

    if user is None or not password_ok:
        await record_audit(
            actor_id=user.id if user is not None else None,
            action="auth.login.failure",
            resource_type="user",
            resource_id=str(user.id) if user is not None else None,
            tenant_id=user.tenant_id if user is not None else None,
            metadata={"email": email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        await record_audit(
            actor_id=user.id,
            action="auth.login.inactive",
            resource_type="user",
            resource_id=str(user.id),
            tenant_id=user.tenant_id,
            metadata={"email": email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    await record_audit(
        actor_id=user.id,
        action="auth.login.success",
        resource_type="user",
        resource_id=str(user.id),
        tenant_id=user.tenant_id,
        metadata={"email": email},
    )
    settings = get_settings()
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        expires_in=settings.access_token_expire_minutes * 60,
    )


def current_user_profile(user: User) -> UserRead:
    return UserRead.from_document(user)
