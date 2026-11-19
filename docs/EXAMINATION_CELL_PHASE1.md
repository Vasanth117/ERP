# Examination Cell — Phase 1 (Backend)

## Scope

Phase 1 delivers:

1. **Examination dashboard** — tenant-scoped metrics from authoritative examination collections (`exam_sessions`, registrations, eligibility, hall tickets, marks batches, results, review/supplementary data, coordination issues, activity logs).
2. **Exam session management** — create, update, lifecycle transitions, history, validation, and audit events.

Later examination-cell modules are intentionally out of scope.

## MongoDB collections

| Collection | Purpose |
|------------|---------|
| `exam_sessions` | Examination cell session registry (distinct from `examination_sessions` college-admin registry and `semester_examination_sessions` timetable rows) |
| `exam_session_academic_scopes` | Departments, programmes, batches, semesters applicable to a session |
| `exam_session_status_history` | Status transition timeline |
| `exam_activity_logs` | Recent examination-cell activity feed |

## Indexes

See `app/modules/examinations/exam_cell_models.py` — unique `(tenant_id, session_code)`, `(tenant_id, session_id)`, term/status and schedule indexes.

## Permissions

| Permission | Description |
|------------|-------------|
| `examination:dashboard:read` | Dashboard metrics |
| `examination:session:read` | Read sessions |
| `examination:session:manage` | Create/update/transitions |

Granted to `examination_cell` role and bundled into `college_admin` via existing `college:examination:*` privileges.

## REST API (`/api/v1/examinations/cell`)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/dashboard` | Filters: academic year, semester, session, department, course, status, type |
| POST | `/sessions` | Create draft session |
| GET | `/sessions` | Paginated list |
| GET | `/sessions/{session_id}` | Detail |
| PATCH | `/sessions/{session_id}` | Draft/scheduled edits only |
| POST | `/sessions/{session_id}/transitions` | Lifecycle actions |
| GET | `/sessions/{session_id}/history` | Status history |

## Session status lifecycle

`draft` → `scheduled` → `registration_open` → `registration_closed` → `ongoing` → `completed` → `results_processing` → `published` → `archived` (with `cancelled` branches). Enforced in `exam_cell_enums.assert_exam_session_transition`.

## Dashboard data sources

- **Sessions**: `exam_sessions`
- **Registrations / eligibility**: `student_exam_registrations`, `student_examination_eligibility`
- **Hall tickets**: `examination_hall_tickets`
- **Timetable**: `semester_examination_sessions` (by linked `season_id`)
- **Marks**: `assessments`, `marks_submission_batches`
- **Results**: `semester_result_publications`
- **Revaluation / supplementary**: `examination_review_windows`, `supplementary_examination_seasons`
- **Incidents**: `department_examination_coordination_issues` (malpractice filter on `issue_type`)
- **Activity**: `exam_activity_logs`

## Tests

```bash
cd backend
pytest tests/test_examination_cell_phase1.py -q
```

## Limitations (Phase 1)

- Department-scoped users are restricted via `AccessScope.department_id` when set; programme/batch filters on dashboard are session-scope metadata only.
- Auto-provisioning of `semester_examination_seasons` from a new `exam_session` is not performed — provide `season_id` to link operational data.
- Malpractice counts rely on coordination issue `issue_type` naming; a dedicated malpractice collection is a later phase.