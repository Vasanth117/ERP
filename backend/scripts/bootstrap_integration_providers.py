"""Seed approved integration provider catalog entries."""

import asyncio

from app.core.database import close_mongo, connect_to_mongo
from app.core.logging import configure_logging
from app.modules.integrations.enums import IntegrationProviderType
from app.modules.integrations.models import IntegrationProvider


DEFAULT_PROVIDERS = (
    ("sendgrid", "SendGrid", IntegrationProviderType.EMAIL, True, False),
    ("twilio_sms", "Twilio SMS", IntegrationProviderType.SMS, True, False),
    ("stripe", "Stripe", IntegrationProviderType.PAYMENT, True, False),
    ("s3", "Amazon S3", IntegrationProviderType.OBJECT_STORAGE, True, True),
    ("azure_ad", "Microsoft Entra ID", IntegrationProviderType.IDENTITY, True, False),
    ("generic_webhook", "Generic Webhook", IntegrationProviderType.WEBHOOK, False, True),
)


async def main() -> None:
    configure_logging()
    await connect_to_mongo()
    try:
        for code, name, ptype, tenant_creds, global_shared in DEFAULT_PROVIDERS:
            existing = await IntegrationProvider.find_one(IntegrationProvider.code == code)
            if existing is not None:
                continue
            await IntegrationProvider(
                code=code,
                name=name,
                provider_type=ptype,
                version="1",
                supports_tenant_credentials=tenant_creds,
                supports_global_shared=global_shared,
            ).insert()
            print(f"seeded provider {code}")
    finally:
        await close_mongo()


if __name__ == "__main__":
    asyncio.run(main())
