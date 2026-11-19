# Department Admin — Phase 9

Phase 9: **Module 1 Document Management** and **Module 2 Security & Audit History**.

## Status

| Label | Meaning |
|-------|---------|
| **Implementation-complete** | APIs, RBAC, metadata models, unit tests delivered. |
| **Pending production verification** | Not production-ready without Mongo integration, storage path review, malware scanning policy, and audit backfill verification. |

MongoDB integration tests **deferred**.

---

## Module 9.1 — Document Management

### Design

- **Storage** — reuses `app.modules.lms.storage` (`validate_upload`, `storage_key_for`, `write_bytes`, `read_bytes`) under tenant prefix `dept_documents/`. No duplicate binary engine.
- **Metadata** — `department_documents`, `department_document_versions`, `department_document_history`.
- **Versioning** — new file revision creates a version row; prior binaries retained via version `storage_key`.
- **Malware scanning** — not wired (assumption: institutional AV at gateway or future worker). Document before enabling production uploads.

### Permissions

- `department:documents:read` — list, get, download (non-archived), versions, history, categories.
- `department:documents:manage` — upload, update, version, archive; download archived documents.

### Categories (allowlist)

`department_administration`, `academic_curriculum`, `faculty_coordination`, `meetings_minutes`, `seminars_workshops`, `project_reviews`, `department_events`, `resource_records`, `reports`, `other`.

**Assumption:** configurable categories via College Admin policy are not implemented; allowlist is code-defined until confirmed.

### Lifecycle

`active`, `archived`, `superseded`, `pending_approval`, `restricted`, `deleted` (soft-delete via status; hard file purge not automated).

### APIs (`/api/v1/department`)

| Method | Path |
|--------|------|
| GET | `/documents/categories` |
| GET | `/documents` |
| POST | `/documents` |
| GET | `/documents/{document_id}` |
| PATCH | `/documents/{document_id}` |
| GET | `/documents/{document_id}/download` |
| POST | `/documents/{document_id}/versions` |
| GET | `/documents/{document_id}/versions` |
| POST | `/documents/{document_id}/archive` |
| GET | `/documents/{document_id}/history` |

Upload body uses base64 file content (same transport pattern as phase 8 import jobs).

### Access scopes

`dept_admin_only`, `dept_faculty`, `dept_students`, `programme`, `batch`, `section`, `explicit_users` — enforced on metadata; faculty/student consumption APIs are **not** part of this phase (Department Admin repository only).

---

## Module 9.2 — Security & Audit History

### Design

- **Canonical audit** — read-only queries on `audit_logs` (`AuditLog`), filtered by `metadata.central_department_id` matching the authorized department.
- **No second audit log** — export jobs stored in `department_audit_export_jobs` (artifact metadata only).
- **Configuration history** — `department_settings_history` for delegated settings.
- **Security events** — subset of `security_events` for tenant, category allowlist, and optional `metadata.central_department_id`.

### Permissions

- `department:audit:read` — audit list, detail, summary, approvals, security events, configuration history, effective permissions.
- `department:audit:export` — `POST /audit/exports` (CSV, 72h retention on job record).

### Audit coverage gap (documented)

Historical `record_audit` calls from phases 1–8 often omit `metadata.central_department_id`. Those events **do not appear** in departmental audit views until enriched or re-logged. Phase 9 document actions include department metadata.

### Redaction

`audit_redaction.redact_audit_metadata` strips keys containing password/token/secret before API responses.

### APIs (`/api/v1/department`)

| Method | Path |
|--------|------|
| GET | `/audit` |
| GET | `/audit/summary` |
| GET | `/audit/approvals` |
| GET | `/audit/security-events` |
| GET | `/audit/configuration-history` |
| GET | `/audit/permissions` |
| POST | `/audit/exports` |
| GET | `/audit/{event_id}` |

Department Admin **cannot** modify or delete audit records.

---

## Tests

- `backend/tests/test_department_admin_phase9.py` — RBAC, categories, redaction, action categories.

---

## Known limitations

1. Title search is in-memory after Mongo filter (no text index).
2. Faculty/student download enforcement for scoped documents not exposed in this phase.
3. Security event visibility depends on emitters setting `metadata.central_department_id`.
4. Pending approval workflow for documents is a status only; no approval engine hook.

Do **not** start Phase 10 until Phase 9 is reviewed.