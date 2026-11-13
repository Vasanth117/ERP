"""Refresh token lifecycle."""

import uuid
from datetime import timedelta

from beanie import PydanticObjectId
from beanie.operators import Eq

from app.common.time import utcnow
from app.core.config import get_settings
from app.core.security import hash_refresh_token, new_refresh_token_plaintext
from app.modules.auth.models import RefreshToken, User


async def issue_refresh_token(user: User) -> tuple[str, RefreshToken]:
    settings = get_settings()
    plaintext = new_refresh_token_plaintext()
    document = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(plaintext),
        family_id=str(uuid.uuid4()),
        expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
    )
    await document.insert()
    return plaintext, document


async def rotate_refresh_token(plaintext: str) -> tuple[User, str]:
    settings = get_settings()
    token_hash = hash_refresh_token(plaintext)
    existing = await RefreshToken.find_one(Eq(RefreshToken.token_hash, token_hash))
    if existing is None or existing.revoked_at is not None:
        raise ValueError("invalid_refresh_token")
    if existing.expires_at <= utcnow():
        raise ValueError("expired_refresh_token")

    user = await User.get(existing.user_id)
    if user is None or not user.is_active:
        raise ValueError("invalid_refresh_token")

    existing.revoked_at = utcnow()
    await existing.save()

    new_plaintext = new_refresh_token_plaintext()
    replacement = RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(new_plaintext),
        family_id=existing.family_id,
        expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),
    )
    await replacement.insert()
    return user, new_plaintext


async def revoke_refresh_token(plaintext: str) -> None:
    token_hash = hash_refresh_token(plaintext)
    existing = await RefreshToken.find_one(Eq(RefreshToken.token_hash, token_hash))
    if existing is None:
        return
    if existing.revoked_at is None:
        existing.revoked_at = utcnow()
        await existing.save()


async def revoke_all_refresh_tokens_for_tenant(tenant_id: PydanticObjectId) -> int:
    """Revoke refresh tokens for all users in a college (access tokens expire naturally)."""
    users = await User.find(Eq(User.tenant_id, tenant_id)).to_list()
    count = 0
    for user in users:
        count += await revoke_all_for_user(user.id)
    return count


async def revoke_all_for_user(user_id: PydanticObjectId) -> int:
    now = utcnow()
    tokens = await RefreshToken.find(
        RefreshToken.user_id == user_id,
        Eq(RefreshToken.revoked_at, None),
    ).to_list()
    for token in tokens:
        token.revoked_at = now
        await token.save()
    return len(tokens)
