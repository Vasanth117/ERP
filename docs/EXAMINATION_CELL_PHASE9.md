# Examination Cell — Phase 9 (Backend)

## Scope

Module 17 — **Integration, Security & Audit Management** for the examination cell only, reusing:

- `InstitutionAuditLog` / `append_institution_audit` (platform audit chain)
- `IntegrationConfiguration` / `IntegrationHealth` (platform integrations)
- Existing RBAC (`permissions.py`) and tenant context from auth

## Collections

| Collection | Role |
|------------|------|
| `exam_integration_configs` | Per-tenant examination integration targets (links optional platform config) |
| `exam_integration_sync_logs` | Idempotent sync attempts with redacted request/response |
| `exam_integration_failures` | Failed sync tracking and recovery |
| `exam_security_events` | Examination-scoped security events (SOD, unauthorized access) |
| `exam_audit_logs` | Append-only detailed examination audit (no update/delete APIs) |
| `exam_access_review_records` | Permission access reviews for examination roles |

## Security controls

- **Separation of duties**: primary examiner cannot approve own marks batch; publication creator cannot publish same publication.
- **Rate limiting**: sensitive integration routes use Redis `exam_cell_sensitive_rate_limit`.
- **Redaction**: `exam_cell_redaction.redact_mapping` on audit/integration payloads.
- **Tenant isolation**: all reads scoped by `require_examination_cell_tenant`.

## Permissions

- `examination:integration:read|manage`
- `examination:audit:read`
- `examination:security:read|manage`

## APIs (`/api/v1/examinations/cell`)

- `GET /integrations`, `PATCH /integrations/{target}`, `POST .../sync`, `GET /integrations/health`
- `POST /integrations/failures/{id}/retry`
- `POST /audit/search`
- `GET /security/events`
- `POST /security/access-reviews`, `POST .../complete`

## Audit enhancement

`record_exam_activity` now writes `exam_audit_logs` plus institution audit rows. Use `record_exam_audit` directly for before/after snapshots.

## Tests

```bash
cd backend
py -m pytest tests/test_examination_cell_phase9.py -q
py -m pytest tests/ -k "examination_cell_phase" -q
```