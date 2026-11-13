"""Login, refresh, and profile."""

from beanie import PydanticObjectId

from app.common.time import utcnow
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    password_needs_upgrade,
    verify_password,
)
from app.modules.audit.service import record_audit
from app.modules.auth.models import User
from app.modules.auth.schemas import LoginRequest, RefreshRequest, TokenResponse, UserRead
from app.modules.auth.token_service import issue_refresh_token, revoke_refresh_token, rotate_refresh_token
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository

_user_repo = UserRepository()
_tenant_repo = TenantRepository()


async def _resolve_login_tenant(tenant_code: str | None) -> PydanticObjectId | None:
    if tenant_code is None:
        return None
    code = tenant_code.strip().lower()
    tenant = await _tenant_repo.find_tenant_by_code(code)
    if tenant is None:
        raise AppError(code="TENANT_NOT_FOUND", message="College not found", status_code=404)
    if not tenant.is_active:
        raise AppError(code="TENANT_INACTIVE", message="This college is inactive", status_code=409)
    return tenant.id


async def login(payload: LoginRequest) -> TokenResponse:
    email = str(payload.email).lower()
    tenant_id = await _resolve_login_tenant(payload.tenant_code)
    user = await _user_repo.find_by_email_for_login(email, tenant_id)
    password_hash = user.hashed_password if user is not None else DUMMY_PASSWORD_HASH
    password_ok = verify_password(payload.password, password_hash)

    if user is None or not password_ok:
        await record_audit(
            actor_id=user.id if user is not None else None,
            action="auth.login.failure",
            resource_type="user",
            resource_id=str(user.id) if user is not None else None,
            tenant_id=tenant_id or (user.tenant_id if user is not None else None),
            outcome="failure",
            metadata={"email": email, "tenant_code": payload.tenant_code},
        )
        raise AppError(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=401,
        )

    if not user.is_active:
        await record_audit(
            actor_id=user.id,
            action="auth.login.inactive",
            resource_type="user",
            resource_id=str(user.id),
            tenant_id=user.tenant_id,
            outcome="failure",
            metadata={"email": email},
        )
        raise AppError(
            code="INVALID_CREDENTIALS",
            message="Invalid email or password",
            status_code=401,
        )

    if password_needs_upgrade(user.hashed_password):
        user.hashed_password = hash_password(payload.password)
        user.updated_at = utcnow()
        await user.save()

    refresh_plaintext, _ = await issue_refresh_token(user)
    settings = get_settings()

    await record_audit(
        actor_id=user.id,
        action="auth.login.success",
        resource_type="user",
        resource_id=str(user.id),
        tenant_id=user.tenant_id,
        metadata={"email": email},
    )
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=refresh_plaintext,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def refresh_tokens(payload: RefreshRequest) -> TokenResponse:
    settings = get_settings()
    try:
        user, new_refresh = await rotate_refresh_token(payload.refresh_token)
    except ValueError as exc:
        raise AppError(
            code="INVALID_REFRESH_TOKEN",
            message="Refresh token is invalid or expired",
            status_code=401,
        ) from exc

    await record_audit(
        actor_id=user.id,
        action="auth.token.refresh",
        resource_type="user",
        resource_id=str(user.id),
        tenant_id=user.tenant_id,
    )
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        refresh_token=new_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def logout(user: User, refresh_token: str | None) -> None:
    if refresh_token:
        await revoke_refresh_token(refresh_token)
    await record_audit(
        actor_id=user.id,
        action="auth.logout",
        resource_type="user",
        resource_id=str(user.id),
        tenant_id=user.tenant_id,
    )


def current_user_profile(user: User) -> UserRead:
    return UserRead.from_document(user)
