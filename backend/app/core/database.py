"""MongoDB connection.

The ERP database is MongoDB. Beanie stores Pydantic documents through Motor.
SQLAlchemy and Alembic target relational databases, so they are not part of this
service. Tenant isolation is enforced on each request in the API and repositories.
"""

import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None


def document_models() -> list[type]:
    from app.modules.audit.models import AuditLog
    from app.modules.auth.models import RefreshToken, User
    from app.modules.tenants.models import Department, Tenant
    from app.modules.platform_identity.models import (
        PlatformAccessReview,
        PlatformInvitation,
        PlatformOperatorProfile,
        PlatformRoleAssignment,
        PlatformRoleDefinition,
        PlatformSession,
    )
    from app.modules.platform_security.models import PlatformAuditLog, SecurityEvent
    from app.modules.support_access.models import (
        SupportAccessActivity,
        SupportAccessApproval,
        SupportAccessRequest,
        SupportAccessSession,
    )
    from app.modules.platform_ops.models import (
        BackgroundJobFailure,
        BackgroundJobRegistry,
        IncidentAssignment,
        IncidentHistory,
        PlatformIncident,
        PlatformService,
        ServiceHealthSnapshot,
    )
    from app.modules.integrations.models import (
        IntegrationConfiguration,
        IntegrationConfigurationHistory,
        IntegrationHealth,
        IntegrationProvider,
        IntegrationSyncHistory,
        ProviderCredentialReference,
        WebhookDeliveryEvent,
    )
    from app.modules.data_governance.models import (
        TenantArchivalRecord,
        TenantDeletionManifest,
        TenantDeletionRequest,
        TenantExportArtifact,
        TenantExportDownload,
        TenantExportJob,
        TenantExportRequest,
        TenantLegalHold,
        TenantOffboardingRecord,
        TenantRetentionExecution,
        TenantRetentionPolicy,
    )
    from app.modules.subscriptions.models import (
        PlanEntitlement,
        SubscriptionHistory,
        SubscriptionInvoice,
        SubscriptionPayment,
        SubscriptionPlan,
        SubscriptionUsageMetric,
        SubscriptionWebhookEvent,
        TenantSubscription,
    )
    from app.modules.configuration.models import (
        ConfigurationChangeHistory,
        ConfigurationVersion,
        PlatformConfiguration,
        TenantBranding,
        TenantConfiguration,
        TenantFeatureFlags,
    )
    from app.modules.tenants.lifecycle_models import DomainVerificationRecord, TenantLifecycleOperation
    from app.modules.tenants.platform_models import (
        PlatformAlert,
        PlatformMetricsSnapshot,
        TenantAdminInvitation,
        TenantDomain,
        TenantOnboarding,
        TenantProvisioningJob,
        TenantStatusHistory,
    )

    return [
        User,
        RefreshToken,
        Tenant,
        Department,
        AuditLog,
        TenantOnboarding,
        TenantDomain,
        TenantAdminInvitation,
        TenantProvisioningJob,
        TenantStatusHistory,
        PlatformMetricsSnapshot,
        PlatformAlert,
        TenantLifecycleOperation,
        DomainVerificationRecord,
        PlatformConfiguration,
        TenantConfiguration,
        TenantBranding,
        TenantFeatureFlags,
        ConfigurationVersion,
        ConfigurationChangeHistory,
        PlatformRoleDefinition,
        PlatformOperatorProfile,
        PlatformRoleAssignment,
        PlatformInvitation,
        PlatformSession,
        PlatformAccessReview,
        SecurityEvent,
        PlatformAuditLog,
        SupportAccessRequest,
        SupportAccessApproval,
        SupportAccessSession,
        SupportAccessActivity,
        PlatformService,
        ServiceHealthSnapshot,
        PlatformIncident,
        IncidentAssignment,
        IncidentHistory,
        BackgroundJobRegistry,
        BackgroundJobFailure,
        IntegrationProvider,
        IntegrationConfiguration,
        ProviderCredentialReference,
        IntegrationHealth,
        IntegrationSyncHistory,
        WebhookDeliveryEvent,
        IntegrationConfigurationHistory,
        TenantExportRequest,
        TenantExportJob,
        TenantExportArtifact,
        TenantExportDownload,
        TenantRetentionPolicy,
        TenantRetentionExecution,
        TenantArchivalRecord,
        TenantDeletionRequest,
        TenantDeletionManifest,
        TenantLegalHold,
        TenantOffboardingRecord,
        SubscriptionPlan,
        PlanEntitlement,
        TenantSubscription,
        SubscriptionHistory,
        SubscriptionInvoice,
        SubscriptionPayment,
        SubscriptionWebhookEvent,
        SubscriptionUsageMetric,
    ]


async def connect_to_mongo() -> None:
    global _client
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
    await _client.admin.command("ping")
    await init_beanie(
        database=_client[settings.mongodb_db_name],
        document_models=document_models(),
    )
    logger.info("Connected to MongoDB database %s", settings.mongodb_db_name)


async def close_mongo() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


async def ping_mongo() -> None:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized")
    await _client.admin.command("ping")


def get_database_client() -> AsyncIOMotorClient:
    if _client is None:
        raise RuntimeError("MongoDB client is not initialized")
    return _client
