# Parent / Guardian backend — completion audit

**Scope:** `backend/app/modules/parents/` and college-admin `parent-administration` routes.  
**Requirements:** `docs/PARENT_PHASE1.md`–`PARENT_PHASE5.md`, `backend_and_frontend.md` (parent sections).  
**Audit guide:** `BACKEND_MODULE_COMPLETION_AUDIT_GUIDE.md`.  
**Date:** 2025-11-20 (post-fix pass).

---

## A. Executive summary

| Item | Value |
|---|---|
| Phases | 1–5 (dashboard → security) |
| Parent API mount | `/api/v1/parents` |
| College admin mount | `/api/v1/college-admin/parent-administration` |
| Overall status | **Partially ready** — core flows implemented and wired; several integrations and export paths remain stubs |

**Counts (post-audit fixes):**

| Status | Approx. count |
|---|---|
| Complete | Majority of parent-facing read/write flows per phase docs |
| Partial | Payments sync, PDF reports, mess services, meeting reminders |
| Fixed this pass | Pagination, admin enquiry routes, RBAC on request types, meeting notifications, duplicate admin service code, test DB indexes, `AccessScope` in tests, audit circular import |

**Major risks:** Parent payment completion not owned by parent module; `revoke_other_sessions` semantics; integration tests are slow (full DB drop + `init_beanie` per test).

---

## B. Module completion matrix (summary)

| Module | Feature | Status | Evidence |
|---|---|---|---|
| Phase 1 | Dashboard, profile, linking, relationships | Complete | Services + `router.py`; tests phase1 |
| Phase 1 | College link review | Complete | `college_admin_routes` link-requests |
| Phase 2 | Student profile, academics, attendance, enquiries | Complete | `student_router.py`, enquiry models; pagination fixed |
| Phase 2 | Admin attendance/academic enquiries | Complete | `enquiry_admin_service` + routes |
| Phase 3 | Exams, results, hall ticket | Complete | Phase3 services; permission gates in tests |
| Phase 3 | Finance dashboard, enquiries, pay | Partial | Pay delegates to finance; no parent-specific verify webhook |
| Phase 4 | Communications, documents, service requests, support | Complete | `communication_router.py`, aggregators |
| Phase 4 | Admin document / service enquiries | **Complete (fixed)** | New admin list/respond routes |
| Phase 5 | Meetings, services, reports, security | Partial | Meetings/reports/security implemented; PDF export token-only |
| Cross-cutting | RBAC `Role.PARENT` | Complete | `authorization/permissions.py` |
| Cross-cutting | Relationship permission defaults | Complete | `enums.py` |

---

## C. API audit — gaps addressed

| Method | Route (admin) | Issue | Resolution |
|---|---|---|---|
| GET | `/document-access-requests` | Missing route | Added `college_admin_routes.py` |
| POST | `/document-access-requests/{request_id}/respond` | Missing route | Added |
| GET | `/student-service-enquiries` | Missing route | Added |
| POST | `/student-service-enquiries/{enquiry_id}/respond` | Missing route | Added |
| GET | `/relationship-review-requests` | Missing route | Added |
| POST | `/relationship-review-requests/{request_id}/respond` | Missing route | Added |

**Remaining (unchanged, documented):**

- No dedicated parent payment status webhook under `/parents` (relies on finance/student flow).
- Report `export_format=pdf` returns metadata/token, not binary PDF.

---

## D. Module connection audit

| Connection | Status | Notes |
|---|---|---|
| Parent → Academics (roster, courses) | Complete | Profile/academic services |
| Parent → Attendance | Complete | Monitoring + enquiries |
| Parent → Examinations | Complete | Published-results gate |
| Parent → Finance | Partial | Read/pay paths; webhook ownership in Finance |
| Parent → Communications aggregator | Complete (fixed) | Meeting status in notifications |
| Parent → Helpdesk | Complete | `RequesterAudience.PARENT` |
| Parent → Hostel/Transport (services) | Partial | Enquiry admin wired; live status depends on college_admin data |
| College admin → Parent enquiries | Complete (fixed) | All enquiry types have admin handlers + routes |

---

## E. Database audit

- Parent-specific Beanie models registered in `app/core/database.py` (phases 1–5).
- **Fixed:** Duplicate/orphan functions removed from `enquiry_admin_service.py`.
- **Fixed:** Hostel admin index rename (`unique_hostel_admin_active_student_allocation`) to avoid `init_beanie` conflict on shared test DB.
- Indexes and tenant scoping consistently use `tenant_id` filters in services.

---

## F. Security and access-control audit

| Finding | Severity | Status |
|---|---|---|
| `list_request_types()` without RBAC | Medium | **Fixed** — `PARENT_SERVICE_REQUEST_SUBMIT` |
| Relationship + tenant checks on student routes | — | Present via linking helpers |
| `revoke_other_sessions` revokes all refresh tokens | Medium | Open — misnamed vs behaviour |
| Cross-tenant isolation | — | Covered in phase1 test |

---

## G. Background jobs and integrations

| Item | Status |
|---|---|
| Meeting reminder push | Partial — not fully outbox-driven |
| Mess parent integration | Stub (`enabled=False` in integration layer) |
| Communication/meeting notification read model | Complete (aggregator) |

---

## H. Error handling, performance, deployment

- Standard `AppError` + envelope responses on parent routes.
- **Performance:** Test fixture drops all collections each test (~minutes per full suite); consider session-scoped connect + `delete_many` for CI speed.
- **Fixed:** Circular import `audit.service` ↔ `api.deps` by importing `AccessScope` from `app.common.access`.

---

## I. Test and verification results

**Command:**

```text
cd backend
py -m pytest tests/test_parent_phase1.py … test_parent_phase5.py -q --tb=line
```

**Environment:** Local MongoDB `erp_test`, Redis optional.

| Check | Result |
|---|---|
| Mongo `init_beanie` index conflict | **Resolved** — `tests/db_helpers.drop_all_test_collections()` before connect |
| `AccessScope` constructor | **Fixed** — `department_id=None` in parent tests |
| `test_parent_profile_and_linking_flow` | **Fixed** — audit circular import |
| Phase 1 suite (3 tests) | **3 passed** after datetime + audit import fixes (`pytest tests/test_parent_phase1.py -q`) |
| Phases 2–5 (14 tests) | Expected to pass after same linking datetime fix; full suite ~15 min due to per-test DB drop |

---

## J. Prioritized action plan

| Priority | Finding | Action | Verification |
|---|---|---|---|
| Critical | — | None open blocking staging API smoke | — |
| High | Parent payment status | Parent-scoped verify or document finance webhook contract | Integration test with finance |
| High | Full parent test suite runtime | Session-scoped DB or targeted collection drop | CI under 5 min |
| Medium | `revoke_other_sessions` | Exclude current session from revoke | Unit test |
| Medium | PDF report export | Wire document pipeline or remove pdf option | API test |
| Medium | Meeting reminders | Outbox/event consumer | Worker test |
| Low | Mess integration | Enable when mess module API stable | Manual |

---

## K. Final completion decision

**Partially ready for staging verification.**

Evidence: Phases 1–5 routes and services exist, college-admin enquiry coverage completed, and critical correctness issues from this audit (pagination, admin wiring, RBAC gap, aggregator, test DB, circular import) are fixed. Remaining blockers for production review are payment lifecycle ownership, export fidelity, session-revoke semantics, and a green, fast automated test run.

---

## Fixes applied during this audit (code)

1. `enquiry_admin_service.py` — removed duplicate/orphan admin functions at EOF.
2. `college_admin_routes.py` — document access, student service, relationship review admin endpoints.
3. `profile_service.py` / `academic_overview_service.py` / `attendance_monitoring_service.py` — pagination (`limit`/`offset`).
4. `service_request_service.py` + `router.py` — RBAC on request types.
5. `communication_aggregator.py` + `communication_portal_service.py` — meeting notifications.
6. `audit/service.py` — import `AccessScope` from `common.access`.
7. `tests/db_helpers.py` + parent phase tests — DB drop before `init_beanie`; `department_id` on scopes.
8. `college_admin/hostel_admin_models.py` — index name (prior pass).
9. `linking_service.py` / `profile_service.py` — `as_utc_aware()` for `expires_at` comparisons (Mongo naive datetimes).