# Department Admin — Phase 6

Phase 6 covers **Module 1: Department Calendar** and **Module 2: Communication & Announcements**.

## Status

| Slice | Scope | Implementation | Production-ready |
|-------|--------|----------------|----------------|
| 6.1 | Department calendar CRUD, overview, conflicts, cancel notifications | Implemented | No — Mongo integration tests not run in CI |
| 6.2 | Announcements lifecycle, scheduling hooks, outbox publish/cancel | Implemented | No — delivery worker not verified end-to-end |

## Assumptions (confirm with institution)

1. **Announcement approval:** A user with `department:communication:manage` may submit and approve announcements for their department (no separate college approver role in this phase).
2. **Urgent priority:** Does not bypass submit/approve; it only affects sorting/display metadata.
3. **Scheduled publish:** `DomainOutboxEvent` with type `department.announcement.scheduled` is queued; a background consumer must publish at `scheduled_publish_at` (consumer not part of this module).
4. **Acknowledgements:** Collection and list API exist; student/faculty acknowledgement write paths are not implemented until product confirms requirement.
5. **College calendar:** Read-only merge via `DepartmentDataReader.upcoming_department_events`; college admin collections are not modified.

## Module 6.1 — Calendar

### Data

- Collection: `department_calendar_events`
- College events: `academic_calendar_events` (read-only, dept-scoped)

### Permissions

- `department:calendar:read`
- `department:calendar:manage`

### APIs (prefix: `/api/v1/department`)

| Method | Path |
|--------|------|
| GET | `/calendar` |
| GET | `/calendar/events` |
| POST | `/calendar/events` |
| GET | `/calendar/events/{event_id}` |
| PATCH | `/calendar/events/{event_id}` |
| POST | `/calendar/events/{event_id}/cancel` |
| GET | `/calendar/upcoming` |
| GET | `/calendar/conflicts` |

### Conflict detection

Advisory only: overlaps with peer department events, published timetable entries (`TimetableEntry`), and `ClassSession` rows.

## Module 6.2 — Communication

### Data

- `department_announcements`
- `department_announcement_acknowledgements`
- Delivery: `domain_outbox_events` (`department.announcement.publish`, `.scheduled`, `.cancelled`)

### Permissions

- `department:communication:read`
- `department:communication:manage`

### Lifecycle

`draft` → `submitted` → `approved` | `rejected` → `published` | `scheduled`  
Cancel: non-published → `cancelled`; published → `archived`.

### APIs

| Method | Path |
|--------|------|
| GET | `/announcements` |
| POST | `/announcements` |
| GET | `/announcements/{id}` |
| PATCH | `/announcements/{id}` |
| POST | `/announcements/{id}/submit` |
| POST | `/announcements/{id}/approve` |
| POST | `/announcements/{id}/reject` |
| POST | `/announcements/{id}/publish` |
| POST | `/announcements/{id}/schedule` |
| POST | `/announcements/{id}/cancel` |
| GET | `/announcements/{id}/delivery-status` |
| GET | `/announcements/{id}/acknowledgements` |

### Audience types

- `department_faculty` — `faculty_user_ids_in_department`
- `department_students` — `StudentProfile` by `department_id`
- `programme` / `batch` / `section` — scoped student profiles; programme must belong to department

## Tests

- `backend/tests/test_calendar_conflict_detection.py` — logic (no Mongo)
- `backend/tests/test_department_admin_phase6_rbac.py` — permissions
- Mongo-backed workflow tests: same gap as Phases 3–5 (Beanie + replica set fixture)

## Known limitations

- No dedicated rate limit on bulk announcement publish (college/faculty patterns may be added later).
- Outbox consumer must enforce idempotency and honour `cancelled` before firing scheduled jobs.
- Calendar event `published` status must be set explicitly on update; new events default to `draft`.

## Next phase

Do not start Phase 7 until Phase 6 is reviewed.