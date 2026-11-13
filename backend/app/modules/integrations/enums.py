"""Integration provider types."""

from enum import Enum


class IntegrationProviderType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PAYMENT = "payment"
    OBJECT_STORAGE = "object_storage"
    IDENTITY = "identity"
    WEBHOOK = "webhook"
    OTHER = "other"


class IntegrationScope(str, Enum):
    GLOBAL = "global"
    TENANT = "tenant"


class IntegrationOperationalStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DEGRADED = "degraded"
    FAILED = "failed"
