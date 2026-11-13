"""Platform operator API schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.platform_identity.enums import PlatformInvitationStatus, PlatformRoleCode
from app.modules.platform_identity.models import PlatformAccessReview, PlatformInvitation, PlatformOperatorProfile, PlatformSession
from app.modules.auth.models import User


class ReauthCredentials(BaseModel):
    reauth_password: str | None = Field(default=None, min_length=8, max_length=128)


class PlatformUserCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=12, max_length=128)
    platform_role_code: PlatformRoleCode
    mfa_enabled: bool = False


class PlatformUserUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    mfa_enabled: bool | None = None


class PlatformUserInviteCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr
    full_name: str = Field(min_length=1, max_length=200)
    platform_role_code: PlatformRoleCode


class PlatformUserRead(BaseModel):
    id: str
    email: str
    full_name: str
    platform_role_code: PlatformRoleCode
    granted_permissions: list[str]
    denied_permissions: list[str]
    mfa_enabled: bool
    is_active: bool
    suspended_at: datetime | None
    last_login_at: datetime | None
    last_login_ip: str | None
    created_at: datetime

    @classmethod
    def from_parts(cls, user: User, profile: PlatformOperatorProfile) -> "PlatformUserRead":
        return cls(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            platform_role_code=profile.platform_role_code,
            granted_permissions=profile.granted_permissions,
            denied_permissions=profile.denied_permissions,
            mfa_enabled=profile.mfa_enabled,
            is_active=user.is_active and profile.suspended_at is None,
            suspended_at=profile.suspended_at,
            last_login_at=profile.last_login_at,
            last_login_ip=profile.last_login_ip,
            created_at=profile.created_at,
        )


class PlatformRoleAssignRequest(BaseModel):
    platform_role_code: PlatformRoleCode
    reauth_password: str | None = Field(default=None, min_length=8)


class PlatformPermissionsUpdate(BaseModel):
    grant: list[str] = Field(default_factory=list)
    revoke: list[str] = Field(default_factory=list)
    reauth_password: str | None = Field(default=None, min_length=8)


class PlatformSuspendRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    reauth_password: str = Field(min_length=8)


class PlatformInvitationRead(BaseModel):
    id: str
    email: str
    full_name: str
    role_code: PlatformRoleCode
    status: PlatformInvitationStatus
    expires_at: datetime
    sent_count: int
    last_sent_at: datetime

    @classmethod
    def from_document(cls, invitation: PlatformInvitation) -> "PlatformInvitationRead":
        return cls(
            id=str(invitation.id),
            email=invitation.email,
            full_name=invitation.full_name,
            role_code=invitation.role_code,
            status=invitation.status,
            expires_at=invitation.expires_at,
            sent_count=invitation.sent_count,
            last_sent_at=invitation.last_sent_at,
        )


class PlatformSessionRead(BaseModel):
    id: str
    user_id: str
    ip_address: str | None
    user_agent: str | None
    created_at: datetime
    last_seen_at: datetime
    revoked_at: datetime | None

    @classmethod
    def from_document(cls, session: PlatformSession) -> "PlatformSessionRead":
        return cls(
            id=str(session.id),
            user_id=str(session.user_id),
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            created_at=session.created_at,
            last_seen_at=session.last_seen_at,
            revoked_at=session.revoked_at,
        )


class PlatformAccessReviewCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    inactive_threshold_days: int = Field(default=90, ge=30, le=365)


class PlatformAccessReviewDecision(BaseModel):
    user_id: str
    decision: str = Field(pattern=r"^(retain|revoke|suspend)$")
    notes: str | None = Field(default=None, max_length=500)


class PlatformAccessReviewComplete(BaseModel):
    decisions: list[PlatformAccessReviewDecision]


class PlatformAccessReviewRead(BaseModel):
    id: str
    title: str
    status: str
    reviewer_id: str
    inactive_threshold_days: int
    decisions: list[dict[str, Any]]
    created_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_document(cls, review: PlatformAccessReview) -> "PlatformAccessReviewRead":
        return cls(
            id=str(review.id),
            title=review.title,
            status=review.status.value,
            reviewer_id=str(review.reviewer_id),
            inactive_threshold_days=review.inactive_threshold_days,
            decisions=review.decisions,
            created_at=review.created_at,
            completed_at=review.completed_at,
        )
