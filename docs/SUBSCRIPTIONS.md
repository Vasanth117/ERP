# SaaS subscriptions (Phase 5)

## Feature flag

Set `SAAS_BILLING_ENABLED=false` to disable subscription APIs (returns `404 BILLING_DISABLED`). Tenant management and offboarding continue to work; subscription blocker checks are skipped when disabled.

## Plans & entitlements

- Plans: `/api/v1/platform/subscriptions/plans`
- Entitlements: `PATCH .../plans/{code}/entitlements` — `limits` (e.g. `max_students`) and `modules` list (use `"*"` for all).

Backend enforcement: `app/modules/subscriptions/enforcement.py`

- `enforce_active_subscription`
- `check_entitlement_limit`
- `assert_module_entitled`

## Webhooks

`POST /api/v1/platform/subscriptions/webhooks/ingest` — HMAC verification (same helper as integrations), unique `idempotency_key` in `subscription_webhook_events`.

Never store raw card data; use provider references only.

## Bootstrap

```powershell
cd backend
py -m scripts.bootstrap_subscription_plans
```
