# Controlled support access (Phase 3)

## Workflow

1. Support operator `POST /api/v1/platform/support-access/requests`
2. Approver `POST .../requests/{id}/decision` (`approved` / `rejected`)
3. Requester `POST .../requests/{id}/sessions` → receives one-time `token`
4. Client sends `X-Support-Session: <token>` with API calls (server enforces expiry + scopes)
5. Terminate early or security revokes session

## Scope allowlist

- `view_tenant_config`
- `view_integration_diagnostics`
- `view_operational_errors`
- `view_system_metadata`

Student, HR, examination, and financial business data are **not** in default scopes.

## Anti-impersonation

Support operators **cannot** use `X-Tenant-Id` without an active support session. Platform owners/super admins with `platform:tenant:manage` may still impersonate with audit logging.

## Collections

`support_access_requests`, `support_access_approvals`, `support_access_sessions`, `support_access_activity`
