# Tenant lifecycle (Phase 2)

## Lifecycle states

`pending` → `provisioning` → `active` ↔ `suspended` → offboarding states → `archived` → `closed`

Offboarding path: `offboarding_requested` → `offboarding_approved` → `offboarding_in_progress` → `archived` / `closed`

Transitions are enforced in `app/modules/tenants/enums.py` (`LIFECYCLE_TRANSITIONS`).

The registry keeps legacy `status` / `is_active` aligned via `lifecycle_sync.py`.

## Activation guardrails

Activation requires:

- Onboarding stage in `provisioned`, `admin_invitation_pending`, `admin_setup_pending`, or `completed`
- Latest provisioning job succeeded when a job exists

## Suspension policy (summary)

See `TENANT_SUSPENSION_POLICY.md`. Suspension:

- Blocks college user login and API access (403 `TENANT_SUSPENDED`)
- Revokes refresh tokens for all users in the tenant
- Does **not** delete data
- Super Admin / Platform Admin bypass for platform operations

## APIs

- `GET/POST /api/v1/tenants/{id}/lifecycle/*`
- `GET /api/v1/platform/lifecycle/operations/pending`

## Operations collection

`tenant_lifecycle_operations` stores scheduled actions, idempotency keys, progress steps, and offboarding metadata.
