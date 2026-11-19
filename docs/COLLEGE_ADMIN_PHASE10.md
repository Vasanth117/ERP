# College Admin Phase 10

Data import & migration (module 19) and integration management (module 20).

## Import (`/api/v1/college-admin/data-import`)

CSV uploads (Excel extension accepted; CSV execution in this phase), column mapping, validation, preview, approval gate, execute, retry, migration history, and expiring error report tokens.

| Collection | Role |
|------------|------|
| `institution_import_templates` | Entity templates + column rules |
| `institution_import_mappings` | Column maps + duplicate keys |
| `institution_import_jobs` | Job lifecycle + idempotency |
| `institution_import_validation_errors` | Row-level validation |
| `institution_import_row_results` | Per-row outcomes |
| `institution_migration_history` | Execute audit + compensating metadata |

Files stored under `{export_storage_path}/institution_imports/` (tenant-scoped keys).

**Permissions:** `college:import:read|manage|execute|approve`

## Integrations (`/api/v1/college-admin/integration-administration`)

Tenant-scoped wrappers around `integration_configurations` with `credential_ref` only in `institution_provider_credential_references` (no plaintext secrets). SSRF checks on outbound URLs. Webhook signature + replay protection via `institution_webhook_endpoints` and delivery logs.

**Permissions:** `college:integration:read|manage|config`

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase1.py … tests/test_college_admin_phase10.py -q
```