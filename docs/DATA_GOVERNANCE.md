# Data export, offboarding & retention (Phase 5)

## Export flow

1. `POST /api/v1/platform/tenants/{tenant_id}/exports` — scoped modules (`ALLOWED_EXPORT_MODULES`).
2. Review → approve/reject (`.../review`).
3. `.../start` runs job; artifact written under `EXPORT_STORAGE_PATH` (private filesystem path).
4. `POST .../artifacts/{id}/download` returns **short-lived** `token` + `signature` (not a public URL).
5. `GET .../artifacts/{id}/content?token=&signature=` — authenticated operator only.

Cross-tenant reads are rejected by matching `tenant_id` on every document.

## Offboarding stages

Tracked in `tenant_offboarding_records` (complements Phase 2 `lifecycle_status` on `tenants`).

Stages: requested → pending approval → approved → export preparation → export in progress → export available → retention → archival → archived → deletion review → deletion approved → deletion in progress → closed.

Legal holds in `tenant_legal_holds` block deletion APIs.

## Retention

Global: `GET/PATCH /api/v1/platform/retention/policies`  
Per-tenant overrides: `/api/v1/platform/tenants/{tenant_id}/retention/policy`

`allow_deletion` must be explicitly enabled before deletion requests are accepted.

## Permissions

- `platform:export:read|manage`
- `platform:retention:read|manage`
- `platform:offboarding:manage`
