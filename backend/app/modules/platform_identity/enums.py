"""Platform operator roles (distinct from college roles)."""

from enum import Enum


class PlatformRoleCode(str, Enum):
    PLATFORM_OWNER = "platform_owner"
    PLATFORM_SUPER_ADMIN = "platform_super_admin"
    PLATFORM_OPS_ADMIN = "platform_ops_admin"
    PLATFORM_SUPPORT_OPERATOR = "platform_support_operator"
    PLATFORM_SECURITY_AUDITOR = "platform_security_auditor"
    PLATFORM_BILLING_ADMIN = "platform_billing_admin"


class PlatformInvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"


class PlatformAccessReviewStatus(str, Enum):
    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


PRIVILEGED_PLATFORM_ROLES = frozenset(
    {
        PlatformRoleCode.PLATFORM_OWNER,
        PlatformRoleCode.PLATFORM_SUPER_ADMIN,
        PlatformRoleCode.PLATFORM_OPS_ADMIN,
    }
)
