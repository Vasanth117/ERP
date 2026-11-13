# Platform MongoDB collections

| Collection | Owner | Purpose |
|------------|-------|---------|
| `tenants` | Platform | College registry (`code` unique) |
| `tenant_onboarding` | Platform | Onboarding stage + history (1:1 tenant) |
| `tenant_domains` | Platform | Normalized domain uniqueness |
| `tenant_admin_invitations` | Platform | Hashed admin invite tokens |
| `tenant_provisioning_jobs` | Platform | Idempotent provisioning saga |
| `tenant_status_history` | Platform | Operational status audit trail |
| `platform_metrics_snapshots` | Platform | Dashboard metric snapshots |
| `platform_alerts` | Platform | Critical/warning platform alerts |
| `tenant_lifecycle_operations` | Platform | Lifecycle/offboarding operations |
| `domain_verification_records` | Platform | DNS verification tokens (hashed) |
| `platform_configurations` | Platform | Global allowlisted settings |
| `tenant_configurations` | Platform/Tenant | Per-tenant allowlisted settings |
| `tenant_branding` | Tenant | Display name, colours, file refs |
| `tenant_feature_flags` | Tenant | Allowlisted boolean flags |
| `configuration_versions` | Platform/Tenant | Immutable config snapshots |
| `configuration_change_history` | Platform/Tenant | Auditable config change index |

### Phase 3 — identity, security, support

| Collection | Owner | Purpose |
|------------|-------|---------|
| `platform_users` | Platform | Operator profiles (linked to global `users`) |
| `platform_user_invitations` | Platform | Hashed operator invite tokens |
| `platform_roles` | Platform | Role → permission map |
| `platform_sessions` | Platform | Operator session metadata |
| `platform_access_reviews` | Platform | Periodic access review records |
| `security_events` | Platform | Security signal index |
| `platform_audit_logs` | Platform | Platform-scoped audit trail |
| `support_access_requests` | Platform | Controlled support access requests |
| `support_access_approvals` | Platform | Approval workflow |
| `support_access_sessions` | Platform | Active support sessions |
| `support_access_activity` | Platform | Support action activity log |

### Phase 4 — operations & integrations

| Collection | Owner | Purpose |
|------------|-------|---------|
| `platform_services` | Platform | Registered service catalog for health |
| `service_health_snapshots` | Platform | Point-in-time health (no secrets) |
| `platform_incidents` | Platform | Operational incidents |
| `incident_assignments` | Platform | Incident ownership |
| `incident_history` | Platform | Status/field change history |
| `background_job_registry` | Platform | Job summary + retry policy (no payloads) |
| `background_job_failures` | Platform | Failure records linked to registry |
| `integration_providers` | Platform | Approved provider catalog |
| `integration_configurations` | Platform/Tenant | Connection settings (URLs validated) |
| `integration_health` | Platform/Tenant | Last check + operational status |
| `integration_sync_history` | Platform/Tenant | Sync attempt history |
| `webhook_delivery_events` | Platform/Tenant | Delivery tracking + idempotency |
| `provider_credential_references` | Platform/Tenant | `env://` / `vault://` refs only |

### Phase 5 — export, retention, subscriptions

| Collection | Owner | Purpose |
|------------|-------|---------|
| `tenant_export_requests` | Platform/Tenant | Scoped export approvals |
| `tenant_export_jobs` | Platform/Tenant | Job progress (no raw payloads) |
| `tenant_export_artifacts` | Platform/Tenant | Private storage keys + checksum |
| `tenant_export_downloads` | Platform/Tenant | Hashed tokens, expiry, access counts |
| `tenant_retention_policies` | Platform/Tenant | Retention and deletion rules |
| `tenant_retention_executions` | Platform/Tenant | Scheduled retention runs |
| `tenant_archival_records` | Platform/Tenant | Archival outcomes |
| `tenant_deletion_requests` | Platform | Deletion approval workflow |
| `tenant_deletion_manifests` | Platform | Immutable deletion audit |
| `tenant_legal_holds` | Platform | Blocks deletion |
| `tenant_offboarding_records` | Platform | Extended offboarding stages |
| `subscription_plans` | Platform | SaaS plan catalog |
| `plan_entitlements` | Platform | Limits + enabled modules |
| `tenant_subscriptions` | Platform/Tenant | 1:1 tenant subscription |
| `subscription_history` | Platform/Tenant | Plan change audit |
| `subscription_invoices` | Platform/Tenant | Invoice index (no card data) |
| `subscription_payments` | Platform/Tenant | Idempotent payment records |
| `subscription_webhook_events` | Platform | Provider webhook dedupe |
| `subscription_usage_metrics` | Tenant | Usage metering |

## Key constraints

- `tenants.code` — unique (normalized lowercase)
- `tenant_domains.normalized_domain` — unique globally
- `tenant_onboarding.tenant_id` — unique
- `tenant_provisioning_jobs (tenant_id, idempotency_key)` — unique
- `tenant_admin_invitations.token_hash` — unique

## Retention

- `platform_metrics_snapshots` — operational; prune snapshots older than 90 days (ops task, not automated in Phase 1).
- `tenant_status_history` — retain for compliance (no TTL in Phase 1).
- `platform_alerts` — optional `expires_at`; acknowledge instead of delete.

## Indexes

Applied via Beanie models. After deploy:

```powershell
cd backend
python -m scripts.migrate_indexes
```
