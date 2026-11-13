# Tenant suspension — operational behaviour

## User impact

| Actor | Login | API access | Notes |
|-------|-------|------------|-------|
| Students / faculty / staff | Blocked | Blocked | `TENANT_SUSPENDED` on login and scoped requests |
| College Admin | Blocked | Blocked | Same as other tenant users |
| Platform Admin | Allowed | Platform APIs | No tenant-scoped impersonation requirement |
| Super Admin | Allowed | All authorized APIs | May use `X-Tenant-Id` for recovery/export |

## Sessions

- **Refresh tokens:** revoked for all users in the tenant on suspend (`revoke_all_refresh_tokens_for_tenant`).
- **Access tokens:** remain valid until expiry (short TTL). Production may add access-token denylist later.

## Data and jobs

- **MongoDB data:** retained; no deletes in Phase 2.
- **Background jobs:** should treat suspended tenants as non-runnable (worker enforcement in later phases).
- **Integrations / notifications:** should pause for suspended tenants (integration layer Phase 5+).
- **Billing / compliance:** platform operators retain read access via Super Admin tools.

## Offboarding

Initiation records retention policy, export requirement, and billing metadata. Export/archival execution is **Phase 5**.
