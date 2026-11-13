# Super Admin / tenant platform — completion audit

Audit date: against `BACKEND_MODULE_COMPLETION_AUDIT_GUIDE.md` and Phases 1–5 platform scope.

## Executive summary

| Status | Count (high level) |
|--------|-------------------|
| Complete / verified | Core tenant CRUD, onboarding, lifecycle, config, identity, ops health, integrations, export, subscriptions |
| Fixed in this pass | Lifecycle offboarding approve/start, provisioning ops retry, lifecycle↔Phase5 offboarding sync, `background_job_failures` writes, offboarding report API, subscription suspend |

**Tests:** `py -m pytest tests/ -q` — 44+ passed (re-run after fixes).

**Staging blockers (remaining):** No API integration tests for most platform routes; export still runs synchronously in-request (Celery worker not required for MVP); `platform_services` catalog needs bootstrap script run.

---

## Module completion matrix (tenant / platform)

| Module | Feature | Status | Notes |
|--------|---------|--------|-------|
| P1 Dashboard | Stats, alerts, activity, health | Complete | Celery unknown without workers — expected |
| P1 Tenants | Register, onboard, provision | Complete | |
| P2 Lifecycle | Activate, suspend, offboarding initiate | Complete | |
| P2 Lifecycle | Offboarding approve/start | **Fixed** | Was Missing — added routes |
| P2 Config | Platform/tenant config, branding, flags | Complete | |
| P3 Identity | Operators, roles, sessions | Complete | |
| P3 Security / support access | Audit, support sessions | Complete | |
| P4 Ops | Health, incidents, job retry | Partial→Improved | Provisioning retry was disconnected — **fixed** |
| P4 Integrations | Providers, webhooks | Complete | |
| P5 Export | Scoped export, downloads | Complete | Sync job; cross-tenant guard in service |
| P5 Offboarding | Extended workflow | Partial→Improved | Synced with lifecycle |
| P5 Subscriptions | Plans, assign, webhooks | Partial | Suspend **added**; suspend policy automation unverified |
| P5 Retention / deletion | Policies, legal hold, manifest | Complete | |

---

## Critical fixes applied

1. **`POST .../lifecycle/offboarding/approve`** and **`.../start`** — implement `OFFBOARDING_APPROVE` / `OFFBOARDING_START` transitions.
2. **`offboarding_sync.py`** — links `TenantLifecycleOperation` to `tenant_offboarding_records`.
3. **`retry_background_job`** — calls `retry_failed_provisioning` instead of `pass`.
4. **`background_job_failures`** — populated on export failure via `record_job_failure`.
5. **`GET /platform/tenants/{id}/offboarding/report`** — offboarding report.
6. **`POST /platform/subscriptions/tenants/{id}/suspend`** — subscription suspend.
7. **`bootstrap_platform_services.py`** — seed `platform_services`.
8. **PLATFORM_OPS role** — `PLATFORM_EXPORT_READ`, `PLATFORM_RETENTION_READ`.

---

## Remaining recommendations (medium)

- Add integration tests for lifecycle offboarding approve/start and export approve flow.
- Move large exports to Celery task; keep registry status updates.
- Wire `tenant.data_export` into ops retry allowlist only if async queue is added.
- Document dual entry: `/tenants/{id}/lifecycle/offboarding/*` (Phase 2) vs `/platform/tenants/{id}/offboarding/*` (Phase 5) — now synced via `offboarding_sync`.

---

## Verification

```powershell
cd backend
py -m pytest tests/ -q
py -m scripts.migrate_indexes
py -m scripts.bootstrap_platform_services
```
