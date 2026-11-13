"""MFA and step-up authentication for platform operators."""

from datetime import timedelta

from app.common.time import utcnow
from app.core.exceptions import AppError
from app.core.security import verify_password
from app.modules.auth.models import User
from app.modules.platform_identity.enums import PRIVILEGED_PLATFORM_ROLES
from app.modules.platform_identity.models import PlatformOperatorProfile


async def assert_reauth(user: User, password: str | None) -> None:
    if not password:
        raise AppError(
            code="REAUTH_REQUIRED",
            message="Reauthentication password is required",
            status_code=401,
        )
    if not verify_password(password, user.hashed_password):
        raise AppError(code="REAUTH_FAILED", message="Reauthentication failed", status_code=401)


async def assert_mfa_if_required(profile: PlatformOperatorProfile) -> None:
    if profile.platform_role_code in PRIVILEGED_PLATFORM_ROLES or profile.mfa_enabled:
        if not profile.mfa_enabled:
            raise AppError(
                code="MFA_REQUIRED",
                message="Multi-factor authentication must be enabled for this operator",
                status_code=403,
            )
        if profile.last_mfa_at is None or profile.last_mfa_at < utcnow() - timedelta(minutes=30):
            raise AppError(
                code="MFA_STEP_UP_REQUIRED",
                message="Recent MFA verification is required",
                status_code=403,
            )
