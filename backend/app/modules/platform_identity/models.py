"""Platform operator identity (links to auth.users where tenant_id is null)."""

from datetime import datetime
from typing import Any

from beanie import Document, PydanticObjectId
from pydantic import Field
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.time import utcnow
from app.modules.platform_identity.enums import PlatformAccessReviewStatus, PlatformInvitationStatus, PlatformRoleCode


class PlatformRoleDefinition(Document):
    """Catalog of platform roles and default permissions."""

    code: PlatformRoleCode
    name: str
    description: str = ""
    permission_codes: list[str] = Field(default_factory=list)
    is_privileged: bool = False
    requires_mfa: bool = False
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "platform_roles"
        indexes = [
            IndexModel([("code", ASCENDING)], unique=True, name="unique_platform_role_code"),
        ]


class PlatformOperatorProfile(Document):
    """Extended profile for platform operators (`platform_users` view)."""

    user_id: PydanticObjectId
    platform_role_code: PlatformRoleCode
    granted_permissions: list[str] = Field(default_factory=list)
    denied_permissions: list[str] = Field(default_factory=list)
    mfa_enabled: bool = False
    mfa_enrolled_at: datetime | None = None
    last_mfa_at: datetime | None = None
    last_login_at: datetime | None = None
    last_login_ip: str | None = None
    suspended_at: datetime | None = None
    suspension_reason: str | None = None
    security_notes: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "platform_users"
        indexes = [
            IndexModel([("user_id", ASCENDING)], unique=True, name="unique_platform_user_profile"),
            IndexModel([("platform_role_code", ASCENDING)], name="platform_users_by_role"),
            IndexModel([("last_login_at", DESCENDING)], name="platform_users_last_login"),
        ]


class PlatformRoleAssignment(Document):
    user_id: PydanticObjectId
    role_code: PlatformRoleCode
    assigned_by: PydanticObjectId
    assigned_at: datetime = Field(default_factory=utcnow)
    active: bool = True

    class Settings:
        name = "platform_role_assignments"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("active", ASCENDING)], name="platform_role_by_user"),
        ]


class PlatformInvitation(Document):
    email: str
    full_name: str
    role_code: PlatformRoleCode
    token_hash: str
    status: PlatformInvitationStatus = PlatformInvitationStatus.PENDING
    expires_at: datetime
    accepted_at: datetime | None = None
    sent_count: int = 1
    last_sent_at: datetime = Field(default_factory=utcnow)
    created_by: PydanticObjectId
    created_at: datetime = Field(default_factory=utcnow)

    class Settings:
        name = "platform_invitations"
        indexes = [
            IndexModel([("token_hash", ASCENDING)], unique=True, name="unique_platform_invite_hash"),
            IndexModel([("email", ASCENDING)], name="platform_invite_by_email"),
        ]


class PlatformSession(Document):
    user_id: PydanticObjectId
    refresh_family_id: str
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime = Field(default_factory=utcnow)
    last_seen_at: datetime = Field(default_factory=utcnow)
    revoked_at: datetime | None = None

    class Settings:
        name = "platform_sessions"
        indexes = [
            IndexModel([("user_id", ASCENDING), ("revoked_at", ASCENDING)], name="platform_sessions_by_user"),
            IndexModel([("refresh_family_id", ASCENDING)], unique=True, name="unique_platform_session_family"),
        ]


class PlatformAccessReview(Document):
    title: str
    status: PlatformAccessReviewStatus = PlatformAccessReviewStatus.OPEN
    reviewer_id: PydanticObjectId
    decisions: list[dict[str, Any]] = Field(default_factory=list)
    inactive_threshold_days: int = 90
    created_at: datetime = Field(default_factory=utcnow)
    completed_at: datetime | None = None

    class Settings:
        name = "platform_access_reviews"
        indexes = [
            IndexModel([("status", ASCENDING), ("created_at", DESCENDING)], name="access_reviews_by_status"),
        ]
