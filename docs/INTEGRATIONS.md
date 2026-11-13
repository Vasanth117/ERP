# Integration providers (Phase 4)

## Secret handling

Credentials are stored as **references** only (`env://VAR_NAME` or future `vault://...`) in `provider_credential_references`. API responses expose `secret_ref`, never resolved values.

## Global vs tenant

- `IntegrationConfiguration.scope = global|tenant`
- Providers declare `supports_tenant_credentials` and `supports_global_shared`.

## SSRF protection

`connection_url` values are validated with `app/core/url_safety.py` (blocks private IPs, localhost, metadata hosts).

## Webhooks

`webhook_delivery_events` use unique `idempotency_key`. Verification helpers in `integrations/webhook_security.py` enforce HMAC signatures and timestamp replay windows.

## APIs

Base: `/api/v1/platform/integrations`
