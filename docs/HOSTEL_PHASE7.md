# Hostel Admin Phase 7

Integrations management (HA 13) and audit history & configuration (HA 14). Follows `backend_and_frontend.md`.

## Reuse (no duplicate platform systems)

- **Institution integrations:** `institution_integrations`, `institution_integration_health`, platform `IntegrationConfiguration` via `institution_integration_key` and `signing_secret_ref` (never plaintext secrets).
- **Audit:** `institution_audit_logs` via `record_hostel_audit()` / `append_institution_audit`; module filter `HOSTEL_AUDIT_MODULES`.
- **Finance authority:** Mess reconciliation reads `StudentFeeDemand` only; no duplicate ledger in hostel DB.
- **Notifications / documents:** Bindings point at shared providers; delivery remains in existing notification and document modules.

## APIs (`/api/v1/hostel`)

### Integrations

| Method | Path |
|--------|------|
| GET | `/me/integrations/dashboard` |
| GET | `/me/integrations/bindings` |
| PUT | `/me/integrations/bindings` |
| POST | `/me/integrations/sync` |
| GET | `/me/integrations/health` |
| GET | `/me/integrations/reconciliation` |
| GET | `/me/integrations/sync-jobs` |
| GET | `/me/integrations/failures` |
| GET | `/me/integrations/events` |
| POST | `/me/integrations/webhooks/{category}` |
| POST | `/me/integrations/failures/{failure_id}/retry` |

Permissions: `hostel:integration:read` / `hostel:integration:manage`.

### Audit & configuration

| Method | Path |
|--------|------|
| GET | `/me/audit/dashboard` |
| POST | `/me/audit/search` |
| POST | `/me/audit/export` |
| GET | `/me/configuration` |
| PUT | `/me/configuration` |
| POST | `/me/configuration/transition` |
| GET | `/me/configuration/{policy_section}` |
| GET | `/me/policies/definitions` |
| PUT | `/me/policies/definitions` |
| POST | `/me/policies/approve` |

Permissions: `hostel:audit:read`, `hostel:audit:export`, `hostel:config:read`, `hostel:config:manage`.

## Collections

- `hostel_integrations`, `hostel_integration_mappings`, `hostel_integration_sync_jobs`, `hostel_integration_events`, `hostel_integration_failures`, `hostel_integration_reconciliation_records`, `hostel_webhook_subscriptions`
- `hostel_configuration`, `hostel_configuration_versions`, `hostel_policy_definitions`, `hostel_policy_versions`, `hostel_policy_approvals`

## Tests

```bash
cd backend
py -m pytest tests/test_hostel_phase7.py -q
```

## Limitations

- Webhook endpoint currently uses hostel admin auth (not public HMAC-only ingress); signature check stores `signing_secret_ref` presence only until shared webhook verifier is wired.
- Student/finance sync jobs are tenant-scoped reconciliation helpers, not full external API clients.
- Scheduled/event sync triggers rely on future job runner hooks; manual sync is fully supported.
- Notification/document/gate categories accept bindings and health overlay but do not invoke provider SDKs unless institution integration is configured.
- Audit dashboard aggregate counts sample up to 5000 rows for action-pattern buckets (performance guard).

Phase 7 complete — await approval before further hostel phases.