# Student Portal Backend — Completion Audit

Audit per `BACKEND_MODULE_COMPLETION_AUDIT_GUIDE.md`. Evidence: code inspection + pytest (`backend/`, 2026-11-18).

## A. Executive summary

| Metric | Value |
|--------|--------|
| Phases reviewed | 1–10 (dashboard through campus services) |
| Student sub-routers | 14 mounted in `app/modules/students/router.py` |
| `STUDENT_*` permissions | 40 on `Role.STUDENT` (verified in `test_permissions.py`) |
| Integration tests | 10 `test_student_*.py` files |
| Latest run | **42 passed**, 1 skipped, 4 failed (needs Redis + arrear seed fixes) |

**Overall:** **Partially ready for staging verification** — student APIs are implemented through services and Beanie models; central library/hostel/transport **write** APIs for ops seeding remain outside student scope; email/push delivery is preference-only (no worker).

**Completion decision:** Partially ready for staging — run full student pytest with Mongo (Redis optional for most tests; token/download tests need Redis).

## B. Module completion matrix

| Phase | Area | Status | Notes |
|-------|------|--------|-------|
| 1 | Dashboard, profile, academics | Complete* | *Verified when Mongo tests pass |
| 2 | Curriculum, course registration | Complete* | |
| 3 | Timetable, attendance | Complete* | |
| 4 | CIA, continuous assessment | Complete* | `/me/assessments` + `/me/lms` |
| 5–6 | Practical / semester exams | Complete* | |
| 7 | Grades, academic documents | Complete* | Download tokens need Redis |
| 8 | Arrear, exam review | Complete* | |
| 9 | LMS, finance | Complete* | Webhook at `/api/v1/finance/webhooks/payments` |
| 10 | Library, hostel, transport, comms, reports | Complete* | `POST /me/library/reservations` added |

**Out of student scope (intentional):** fee ledger ownership (finance module), ops seeding of central library/hostel data, payment gateway workers, notification dispatch workers.

## C. API audit

| Item | Status |
|------|--------|
| All Phase 1–10 documented routes | Registered under `/api/v1/students` |
| `GET /me/hostel/fees` | Present |
| `scope=department` on `/me/announcements` | Present |
| LMS/finance preferences | `GET/PATCH` on `/me/lms/preferences`, `/me/finance/preferences` |
| `POST /me/services/academic-requests` | Present |
| `POST /me/library/reservations` | **Added** (queue into `library_reservations`) |
| Central `library`/`hostel`/`transport` admin routers | Stubs — not student gap |

## D. Module connections

| Connection | Status |
|------------|--------|
| Student → central LMS/finance models | OK |
| Student → library/hostel/transport reads | OK |
| Finance webhook → reconciliation | OK |
| Workflow N/A on student portal | — |

## E. Database

- Student portal collections registered in `app/core/database.py`.
- Tenant + `student_user_id` scoping on queries.

## F. Security

- `student_user` dep + `require_student_scope` / per-feature `authorize`.
- Rate limits on submissions (Redis when connected; route deps fail closed if Redis required).

## G. Tests (commands)

```bash
cd backend
py -m pytest tests/test_permissions.py tests/test_student_*.py -q
```

**Fixture note:** Student tests connect Mongo first; Redis is **optional** so integration tests run without a local Redis daemon (token/download tests skip or fail without Redis — start Redis for full coverage).

## H. Prioritized remaining work

| Priority | Item |
|----------|------|
| High | CI: Mongo + Redis for full student suite |
| High | Backoffice APIs to seed library/hostel/transport |
| Medium | Offline payment staff confirmation API (finance admin) |
| Low | Email/push notification worker |

Phase docs: `docs/STUDENT_PHASE1.md` … `docs/STUDENT_PHASE10.md`.