"""Payment gateway configuration (secret references only)."""

from uuid import uuid4

from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.core.exceptions import AppError
from app.core.secrets import assert_secret_reference
from app.modules.accounts_finance.phase3_enums import OnlinePaymentMethod, PaymentGatewayEnvironment
from app.modules.accounts_finance.phase3_models import PaymentGatewayConfiguration
from app.modules.accounts_finance.policy import authorize_finance_payment_config, require_finance_tenant_scope
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.common.time import utcnow


async def upsert_gateway_config(scope: AccessScope, payload: dict) -> dict:
    authorize_finance_payment_config(scope)
    tenant_id = require_finance_tenant_scope(scope)
    config_id = (payload.get("config_id") or f"gw_{uuid4().hex[:8]}").strip()
    api_ref = payload.get("api_key_secret_ref")
    wh_ref = payload.get("webhook_secret_ref")
    if api_ref:
        assert_secret_reference(api_ref)
    if wh_ref:
        assert_secret_reference(wh_ref)
    methods = [OnlinePaymentMethod(m) for m in payload.get("supported_methods", [])]
    doc = await PaymentGatewayConfiguration.find_one(
        Eq(PaymentGatewayConfiguration.tenant_id, tenant_id),
        Eq(PaymentGatewayConfiguration.config_id, config_id),
    )
    if doc is None:
        doc = PaymentGatewayConfiguration(
            tenant_id=tenant_id,
            config_id=config_id,
            gateway_name=payload["gateway_name"],
            provider_code=payload.get("provider_code", "stub"),
            environment=PaymentGatewayEnvironment(payload.get("environment", "sandbox")),
            merchant_reference=payload.get("merchant_reference"),
            currency=payload.get("currency", "INR"),
            supported_methods=methods,
            webhook_url=payload.get("webhook_url"),
            api_key_secret_ref=api_ref,
            webhook_secret_ref=wh_ref,
            active=payload.get("active", False),
            connection_status=payload.get("connection_status", "unknown"),
            metadata=payload.get("metadata") or {},
            updated_by=scope.user_id,
        )
        await doc.insert()
    else:
        doc.gateway_name = payload.get("gateway_name", doc.gateway_name)
        doc.provider_code = payload.get("provider_code", doc.provider_code)
        if "environment" in payload:
            doc.environment = PaymentGatewayEnvironment(payload["environment"])
        doc.merchant_reference = payload.get("merchant_reference", doc.merchant_reference)
        doc.currency = payload.get("currency", doc.currency)
        if methods:
            doc.supported_methods = methods
        doc.webhook_url = payload.get("webhook_url", doc.webhook_url)
        if api_ref:
            doc.api_key_secret_ref = api_ref
        if wh_ref:
            doc.webhook_secret_ref = wh_ref
        if "active" in payload:
            doc.active = bool(payload["active"])
        doc.connection_status = payload.get("connection_status", doc.connection_status)
        doc.metadata = payload.get("metadata", doc.metadata)
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    await append_institution_audit(
        tenant_id, actor_id=scope.user_id, action="finance.gateway_config.upsert", module="accounts_finance", resource_type="payment_gateway", resource_id=config_id
    )
    return {
        "config_id": doc.config_id,
        "gateway_name": doc.gateway_name,
        "provider_code": doc.provider_code,
        "active": doc.active,
        "api_key_secret_ref": {"secret_ref": doc.api_key_secret_ref} if doc.api_key_secret_ref else None,
        "webhook_secret_ref": {"secret_ref": doc.webhook_secret_ref} if doc.webhook_secret_ref else None,
    }


async def list_gateway_configs(scope: AccessScope) -> list[dict]:
    authorize_finance_payment_config(scope)
    tenant_id = require_finance_tenant_scope(scope)
    rows = await PaymentGatewayConfiguration.find(Eq(PaymentGatewayConfiguration.tenant_id, tenant_id)).to_list()
    return [
        {
            "config_id": r.config_id,
            "gateway_name": r.gateway_name,
            "provider_code": r.provider_code,
            "active": r.active,
            "environment": r.environment.value,
            "supported_methods": [m.value for m in r.supported_methods],
            "connection_status": r.connection_status,
        }
        for r in rows
    ]