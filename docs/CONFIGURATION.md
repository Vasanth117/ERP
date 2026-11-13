# Platform and tenant configuration (Phase 2)

## Design

- **Allowlists** in `app/modules/configuration/registry.py` — no arbitrary JSON keys.
- **Protected platform keys** (`jwt_policy`, `session_policy`, …) cannot be set via tenant or platform PATCH APIs.
- **Versioning:** each update increments `version` and writes `configuration_versions` + `configuration_change_history`.
- **Branding file IDs** reference the centralized file service (validation deferred until file service integration).

## APIs

| Scope | Base path |
|-------|-----------|
| Global | `/api/v1/platform/configuration` |
| Tenant | `/api/v1/tenants/{tenant_id}/configuration` |
| Branding | `/api/v1/tenants/{tenant_id}/branding` |
| Feature flags | `/api/v1/tenants/{tenant_id}/feature-flags` |
| Domain verify | `/api/v1/tenants/{tenant_id}/domains/{domain_id}/verification/*` |

## Permissions

- `platform:config:read|manage` — global settings (Super Admin)
- `tenant:config:read|manage` — tenant settings (Super Admin + College Admin)
