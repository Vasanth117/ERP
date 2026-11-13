"""Invitation token hashing and reuse rules."""

from datetime import timedelta

import pytest
from beanie import PydanticObjectId

from app.core.database import close_mongo, connect_to_mongo
from app.core.exceptions import AppError
from app.core.security import hash_refresh_token
from app.common.time import utcnow
from app.modules.tenants.enums import InvitationStatus
from app.modules.tenants.platform_models import TenantAdminInvitation


def test_invitation_token_hash_is_stable() -> None:
    token = "sample-token"
    assert hash_refresh_token(token) == hash_refresh_token(token)


@pytest.mark.anyio
async def test_expired_invitation_rejected() -> None:
    try:
        await connect_to_mongo()
    except Exception:
        pytest.skip("MongoDB not available")

    from uuid import uuid4

    plain = f"expired-invite-{uuid4()}"
    invitation = TenantAdminInvitation(
        tenant_id=PydanticObjectId(),
        email="admin@college.test",
        full_name="Admin",
        token_hash=hash_refresh_token(plain),
        status=InvitationStatus.PENDING,
        expires_at=utcnow() - timedelta(hours=1),
        created_by=PydanticObjectId(),
    )
    await invitation.insert()
    from app.modules.tenants.invitation_service import accept_invitation_token

    try:
        with pytest.raises(AppError) as exc:
            await accept_invitation_token(plain)
        assert exc.value.code == "INVITATION_EXPIRED"
    finally:
        await invitation.delete()
        await close_mongo()
