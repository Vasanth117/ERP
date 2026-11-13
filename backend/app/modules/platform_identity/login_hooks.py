"""Platform login tracking."""

from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.platform_identity.models import PlatformOperatorProfile, PlatformSession
from beanie.odm.operators.find.comparison import Eq


async def assert_platform_operator_active(user: User) -> None:
    profile = await PlatformOperatorProfile.find_one(Eq(PlatformOperatorProfile.user_id, user.id))
    if profile is not None and profile.suspended_at is not None:
        raise AppError(
            code="ACCOUNT_SUSPENDED",
            message="This platform operator account is suspended",
            status_code=403,
        )


async def track_platform_login(user: User, refresh_family_id: str, *, ip_address: str | None = None) -> None:
    profile = await PlatformOperatorProfile.find_one(Eq(PlatformOperatorProfile.user_id, user.id))
    if profile is not None:
        profile.last_login_at = utcnow()
        profile.last_login_ip = ip_address
        profile.last_mfa_at = utcnow() if profile.mfa_enabled else profile.last_mfa_at
        profile.updated_at = utcnow()
        await profile.save()
    await PlatformSession(
        user_id=user.id,
        refresh_family_id=refresh_family_id,
        ip_address=ip_address,
    ).insert()
