# Department Admin — Phase 4 (Timetable + Attendance Oversight)

## Module 1 — Timetable management

Reuses canonical **`timetable_entries`** (published official schedule), **`timetable_change_logs`**, faculty assignments, courses, leave requests, and weekly slot shape from academics/faculty modules.

Department workflow collections:

| Collection | Purpose |
|------------|---------|
| `department_timetable_plans` | Draft → submitted → approved → published lifecycle |
| `department_timetable_slots` | Draft slots before publication |
| `department_timetable_change_requests` | Change coordination (logged; apply flow deferred for complex substitutions) |
| `department_timetable_publish_snapshots` | Immutable published slot payloads per version |

### Permissions

- `department:timetable:read` — plans, slots, views, validate, conflicts
- `department:timetable:manage` — create/edit/submit/approve/publish, change requests

### API (`/api/v1/department/...`)

Plans: `GET|POST /timetables`, `GET|PATCH /timetables/{id}`, slots `GET|POST /timetables/{id}/slots`, `PATCH /timetables/slots/{slot_id}`.

Workflow: `POST .../validate`, `.../submit`, `.../approve`, `.../publish` (idempotent via `idempotency_key`).

Views: `GET /timetables/section/{code}`, `/faculty/{id}`, `/rooms/{id}`, `GET /timetable-conflicts?plan_id=`.

### Conflict detection

`faculty_overlap`, `section_overlap`, `room_overlap`, `laboratory_overlap`, `duplicate_subject`, `invalid_duration`, overlap with **published** `timetable_entries`, and **`faculty_on_leave`** (approved leave present — date-level precision deferred).

### Publication

- Requires **approved** plan, validation pass, non-empty slots.
- Supersedes prior published plan for same dept/term **inside the same MongoDB transaction** as entry inserts and publish snapshot.
- Inserts rows into **`timetable_entries`** + **`timetable_change_logs`** (replica set required; `503 TRANSACTIONS_UNAVAILABLE` if unavailable — no fallback).
- Draft plans are **not** visible as official timetables.

### Gaps / assumptions

- No college-owned **room master** in repo — rooms are string labels on slots/entries; **capacity and room-type suitability checks are not implemented** until facility master exists.
- Lab capacity uses **section capacity** only when institution configures batch sections (`department_sections`); not auto-enforced on lab slots yet.
- Timetable change requests are **recorded**; auto-apply for substitution/cancel requires Phase 4 review + college rules.
- Workload hour caps use existing `academic_regulations` (`faculty_workload`) where wired in Phase 2 — not re-validated on every slot add in Phase 4.

## Module 2 — Attendance oversight

Reuses **`attendance_sessions`**, **`attendance_records`**, **`attendance_correction_requests`**, **`attendance_correction_approvals`**, **`pending_attendance_submissions`**, **`attendance_policy_references`**, **`institution_attendance_policies`**, faculty assignments, and `DepartmentDataReader.attendance_overview`.

New collection:

| Collection | Purpose |
|------------|---------|
| `department_attendance_discrepancies` | Review items from dept scan (not authoritative sanctions) |

### Permissions

- `department:attendance:read` — overview, summaries, discrepancies (read)
- `department:attendance:manage` — discrepancy scan, correction review

### APIs

`GET /attendance/overview`, `/classes`, `/subjects`, `/students`, `/faculty-submissions`, `/missing`, `/shortages`, `/discrepancies`, correction requests + `POST .../review`.

### Calculation policy

- Shortage threshold from **`institution_attendance_policies`** (student audience) or **`attendance_policy_references`** — **not hardcoded** (fallback only when no policy document exists).
- Percentages use `attendance.policy_engine.calculate_percentage` (present/late/excused weights).
- Department scope: sessions/records linked to **department faculty**; students filtered by `student_records.department_id`.

### Correction workflow

Department Admin may **approve/reject** faculty `attendance_correction_requests` in scope; writes same `attendance_correction_approvals` pattern as college admin (delegated). Does **not** replace faculty session submission APIs.

### Cancelled / rescheduled exclusion (review fix)

`attendance_eligibility.py` drives missing counts, class summaries, faculty pending counts, and discrepancy scan:

- `ClassSession` on session date with status `cancelled` or `rescheduled` → not missing.
- `TimetableEntry` for same weekday/course/section with status `cancelled` or `rescheduled` → not missing.
- Already **submitted** `AttendanceSession` → not missing.
- Discrepancy scan deduplicates via index + summary lookup; types include `missing_attendance_submission` and `completed_session_no_attendance`.

### Remaining gaps

- Correction window / college-only delegation flag not in settings.
- Late submission metric placeholder.
- Room capacity/type validation blocked until shared facility master (see [DEPARTMENT_ADMIN_PHASE4_REVIEW.md](DEPARTMENT_ADMIN_PHASE4_REVIEW.md)).

## Tests

```powershell
cd backend
pytest tests/test_timetable_conflicts.py tests/test_attendance_eligibility.py tests/test_department_admin_phase4.py -q
```

| Suite | Local run (no Mongo RS) |
|-------|-------------------------|
| `test_timetable_conflicts.py` | 2 passed |
| `test_attendance_eligibility.py` | Skipped/error — needs Beanie init |
| `test_department_admin_phase4.py` | Skipped/error — needs Beanie init |

Mongo replica set required for integration and **publish** tests.

## Review

Full findings: [DEPARTMENT_ADMIN_PHASE4_REVIEW.md](DEPARTMENT_ADMIN_PHASE4_REVIEW.md). **Not production-ready**; Phase 5 blocked until stakeholder review.