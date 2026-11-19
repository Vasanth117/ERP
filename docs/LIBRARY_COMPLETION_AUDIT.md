# Library (Librarian) Backend — Completion Audit

Audit performed against `BACKEND_MODULE_COMPLETION_AUDIT_GUIDE.md`. Scope: `backend/app/modules/library` (+ college-admin `library_admin_*`), mounted at `/api/v1/library`.

**Post-audit fixes in this pass:** library portal policy includes audit/inventory-approval permissions; `GET /inventory/verifications`; `inventory_audit` report type; permission tests for college admin approve.

---

## A. Executive summary

| Item | Result |
|------|--------|
| **Overall** | **Ready for staging verification** (Mongo integration tests green) |
| Modules (phases) | 1–14: dashboard → facility → catalogue → inventory → members → circulation → reservations → fines → acquisition → digital → notifications → reports → settings → audit |
| Route mounting | **Complete** — `app/api/v1/router.py` → `library_router` prefix `/library` |
| Sub-routers | 13 domain routers + dashboard routes on root library router |
| RBAC | `librarian_user` + per-module access; college admin via `LIBRARY_ADMIN_*` |
| Beanie models | Registered in `app/core/database.py` including audit/discrepancy collections |
| Integration tests | **14** `test_library_*.py` files |
| Latest run | **`pytest tests/ -k library` → 67+ passed** (re-run after fixes) |

**Residual (documented, not student/librarian gaps):** notification dispatch workers (outbox), finance procurement live webhooks, email/SMS workers.

---

## B. Module completion matrix

| # | Module | Status | Tests | Doc |
|---|--------|--------|-------|-----|
| 1 | Dashboard | Complete | `test_library_dashboard.py` | `LIBRARY_DASHBOARD.md` |
| 2 | Facility & branches | Complete | `test_library_facility.py` | `LIBRARY_FACILITY.md` |
| 3 | Catalogue | Complete | `test_library_catalogue.py` | `LIBRARY_CATALOGUE.md` |
| 4 | Inventory & verification | Complete | `test_library_inventory.py` | `LIBRARY_INVENTORY.md` |
| 5 | Members | Complete | `test_library_members.py` | `LIBRARY_MEMBERS.md` |
| 6 | Circulation | Complete | `test_library_circulation.py` | `LIBRARY_CIRCULATION.md` |
| 7 | Reservations | Complete | `test_library_reservations.py` | `LIBRARY_RESERVATIONS.md` |
| 8 | Fines | Complete | `test_library_fines.py` | `LIBRARY_FINES.md` |
| 9 | Acquisition | Complete | `test_library_acquisition.py` | `LIBRARY_ACQUISITION.md` |
| 10 | Digital | Complete | `test_library_digital.py` | `LIBRARY_DIGITAL.md` |
| 11 | Notifications | Complete* | `test_library_notifications.py` | `LIBRARY_NOTIFICATIONS.md` |
| 12 | Reports | Complete | `test_library_reports.py` | `LIBRARY_REPORTS.md` |
| 13 | Settings & policies | Complete | `test_library_settings.py` | `LIBRARY_SETTINGS.md` |
| 14 | Audit & inventory control | Complete | `test_library_audit.py` | `LIBRARY_AUDIT.md` |

\* Notifications enqueue domain events; **worker consumption unverified** in deployment wiring.

---

## C. API audit

| Check | Status |
|-------|--------|
| All phase routers included from `library/router.py` | OK |
| College admin library bridge (`library_admin_service`) | OK — delegates borrowing policy to settings |
| Student portal library reads/reservations | OK — `student_library_service` |
| `GET /inventory/verifications` | **Added** (list stock audit sessions) |
| Audit routes under `/audit/*` | OK |
| Immutable audit (no PATCH/DELETE on audit events) | OK |

---

## D. Module connections

| Connection | Status |
|------------|--------|
| Circulation ↔ policy snapshot | OK |
| Fines ↔ policy snapshot | OK |
| Reservations ↔ resolved policy | OK |
| Acquisition ↔ finance/procurement refs | OK |
| Digital ↔ LMS storage | OK |
| Notifications ↔ outbox | Partial — producer only |
| Institution audit chain | OK — `append_institution_audit` |
| Detailed `library_audit_events` | Partial — inventory/audit paths; other domains use institution + domain history collections |

---

## E. Database

- Library collections registered in `document_models()`.
- Tenant-scoped indexes on operational collections.
- Policy snapshots on `library_circulations` for immutability.

---

## F. Security

- Tenant isolation enforced in services via `tenant_id` from access scope.
- Branch scoping via staff assignments (facility module).
- Separation of duties: stock adjustment approve ≠ requester.
- Librarian lacks `library:inventory:approve`; college admin holds it.

---

## G. Tests

```bash
cd backend
py -m pytest tests/ -k "library" -q
```

Also: `tests/test_permissions.py` (librarian + college admin library permissions).

---

## H. Prioritized remaining work

| Priority | Item |
|----------|------|
| Medium | Background worker for library notification outbox |
| Medium | Broader `record_library_audit` on catalogue/circulation mutations (richer before/after) |
| Low | Redis-backed rate limits on high-volume audit export |

---

## I. Final decision

**Ready for staging verification** — APIs, models, RBAC, and Mongo integration tests cover modules 1–14. Production review still requires worker/deployment checklist for notifications and external finance hooks.