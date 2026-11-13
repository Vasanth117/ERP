# Tenant onboarding (Phase 1)

## Workflow stages

Configurable stages (default path):

`draft` → `submitted` → `verification_pending` → `verified` → `provisioning` → `provisioned` → `admin_invitation_pending` → `admin_setup_pending` → `completed`

Terminal stages: `completed`, `cancelled`, `failed`.

`failed` may transition back to `provisioning` (retry) or `cancelled`.

## State machine

Transitions are enforced in `app/modules/tenants/enums.py` (`ONBOARDING_TRANSITIONS`).

## Provisioning saga (idempotent)

Steps recorded on `tenant_provisioning_jobs.steps_completed`:

1. `registry` — tenant registry row
2. `configuration` — academic/timezone metadata on tenant
3. `domain` — `tenant_domains` primary domain
4. `admin_invitation` — hashed token in `tenant_admin_invitations`
5. `finalize` — onboarding stage `provisioned`, tenant status `onboarding` awaiting college admin setup

Retries use a new idempotency key (`retry-{uuid}`) and reuse completed steps.

## Security

- Invitation plaintext tokens are returned once on create/resend; only SHA-256 hashes are stored.
- Invitation resend/create is rate limited via Redis (`INVITATION_RATE_LIMIT_PER_MINUTE`).
- Platform APIs require `platform:tenant:manage` or `platform:tenant:read` / `platform:dashboard:read`.

## APIs

- `POST /api/v1/tenants/register` — full registration + optional auto-submit
- `POST /api/v1/tenants/validate` — duplicate code/domain checks
- `GET /api/v1/tenants/availability/code/{code}`
- `GET /api/v1/tenants/availability/domain/{domain}`
- Onboarding, provisioning, invitation, cancel routes under `/api/v1/tenants/{tenant_id}/...`
- Dashboard under `/api/v1/platform/dashboard*`
