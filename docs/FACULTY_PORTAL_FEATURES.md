# Faculty / Professor — Features & Modules

Backend scope for the Faculty Portal (Phases 1–5). All routes are under **`/api/v1/faculty`**, identity from JWT (`/me/*`), tenant-isolated.

Engineering conventions: see [`backend_and_frontend.md`](../backend_and_frontend.md) (generic guide).

| # | Module | Status | Doc |
|---|--------|--------|-----|
| 1 | Dashboard & Personal Workspace | Implemented | [FACULTY_PHASE1.md](FACULTY_PHASE1.md) |
| 2 | Profile & Teaching Responsibilities | Implemented | [FACULTY_PHASE1.md](FACULTY_PHASE1.md) |
| 3 | Course/Subject & Academic Content | Implemented | [FACULTY_PHASE2.md](FACULTY_PHASE2.md) |
| 4 | Timetable, Class Sessions & Academic Calendar | Implemented | [FACULTY_PHASE2.md](FACULTY_PHASE2.md) |
| 5 | Attendance Management | Implemented | [FACULTY_PHASE3.md](FACULTY_PHASE3.md) |
| 6 | Assignments, Learning Materials & LMS | Implemented | [FACULTY_PHASE3.md](FACULTY_PHASE3.md) |
| 7 | Assessment, Marks Entry & Grading | Implemented | [FACULTY_PHASE4.md](FACULTY_PHASE4.md) |
| 8 | Student Support, Academic Progress & Mentoring | Implemented | [FACULTY_PHASE4.md](FACULTY_PHASE4.md) |
| 9 | Communication, Collaboration & Academic Notifications | Staging-ready* | [FACULTY_PHASE5.md](FACULTY_PHASE5.md) |
| 10 | Faculty Self-Service, Reports & Personal Records | Staging-ready* | [FACULTY_PHASE5.md](FACULTY_PHASE5.md) |

\*See [FACULTY_BACKEND_AUDIT.md](FACULTY_BACKEND_AUDIT.md) for status definitions and verification steps.

## Module 9 — Communication & notifications

**Capabilities:** course/section announcements, publish/withdraw, assignment-style updates via messages, academic reminders, department and examination notifications (inbox aggregation), read status, communication history, recipient visibility, email/push preferences and delivery logs (integration stub).

**Key paths:** `/me/communication/announcements`, `/me/communication/messages`, `/me/communication/notifications`, `/me/communication/notification-preferences`, `/me/communication/reminders`.

**Collections:** `faculty_announcements`, `academic_messages`, `communication_recipients`, `faculty_notification_preferences`, `faculty_notification_delivery_logs`; reuses `faculty_notifications` where applicable.

## Module 10 — Self-service & personal records

**Capabilities:** HR-permitted employment snapshot, leave submit/list/status (central `leave_requests`), payslips when payroll integration enabled, personal documents, academic/attendance/marks history, workload and personal activity reports with expiring download tokens, access logging.

**Key paths:** `/me/self-service/employment`, `/me/self-service/leave`, `/me/self-service/payslips`, `/me/self-service/documents`, `/me/self-service/activity`, `/me/self-service/history/*`, `/me/self-service/reports/*`.

**Collections:** `faculty_personal_documents`, `faculty_report_exports`, `faculty_document_access_logs`; reuses `faculty_activity_logs`, HR `leave_requests`, `payslip_references`, `employee_profile_snapshots` (not duplicated per faculty).

## Security summary

- Course/section scope via active `faculty_assignments` and enrollment rosters.
- Self-service data keyed to authenticated `user_id` only.
- Announcement rate limit (Redis); audit on document/report access.
- Payroll and employment return `unavailable` / `not_configured` when integration or snapshots are absent.

## Tests

```bash
cd backend
pytest tests/test_faculty_phase1.py tests/test_faculty_phase2.py tests/test_faculty_phase3.py tests/test_faculty_phase4.py tests/test_faculty_phase5.py -q
```

Requires MongoDB and Redis for integration tests; several cases skip when dependencies are offline.

## Code layout

- `app/modules/faculty/router.py` — mounts phase routers
- `app/modules/faculty/phase5_router.py` — modules 9–10 HTTP API
- `app/modules/faculty/communication_*`, `self_service_*`, `integrations/notification_dispatch.py`
- `app/modules/hr/models.py` — central leave and payslip references

See [ARCHITECTURE.md](ARCHITECTURE.md) for the system diagram.
