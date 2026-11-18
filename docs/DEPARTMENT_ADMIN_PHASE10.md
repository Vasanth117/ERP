# Department Admin — Phase 10 (final planned phase)

Phase 10: **Module 1 Helpdesk & Issue Tracking** and **Module 2 Placement & Research Coordination**.

## Status

| Label | Meaning |
|-------|---------|
| **Implementation-complete** | APIs, RBAC, coordination collections, unit tests delivered. |
| **Pending production verification** | Not production-ready without Mongo integration, escalation consumers, and placement-cell boundary review. |

MongoDB integration tests **deferred**.

---

## Module 10.1 — Helpdesk & Issue Tracking

### Design

- **No institution-wide helpdesk** exists in the ERP; department tickets are **department-scoped coordination records** (`department_helpdesk_*`), not a parallel platform ticketing engine.
- **Related issues:** Phase 7 `department_resource_issues` and Phase 5 examination coordination issues remain separate; helpdesk tickets may reference them via `affected_record_*`.
- **Storage:** Attachments reference Phase 9 `department_documents` IDs only.
- **Escalation:** Emits idempotent `department.helpdesk.escalated` outbox events for College Admin / support integration (worker not implemented here).
- **SLA:** `first_response_due_at` / `resolution_due_at` fields exist; **no fixed SLA durations** are invented — institution config TBD.

### Permissions

- `department:helpdesk:read` — list, summary, get, history, comments (non-internal only without manage).
- `department:helpdesk:manage` — create, update, assign, comment (including internal), escalate, resolve, reopen.

### Lifecycle

Documented transitions in `helpdesk_constants.STATUS_TRANSITIONS`.

### APIs (`/api/v1/department`)

| Method | Path |
|--------|------|
| GET | `/helpdesk/categories` |
| GET | `/helpdesk/summary` |
| GET | `/helpdesk` |
| POST | `/helpdesk` |
| GET | `/helpdesk/{ticket_id}` |
| PATCH | `/helpdesk/{ticket_id}` |
| POST | `/helpdesk/{ticket_id}/assign` |
| POST | `/helpdesk/{ticket_id}/comments` |
| GET | `/helpdesk/{ticket_id}/comments` |
| POST | `/helpdesk/{ticket_id}/escalate` |
| POST | `/helpdesk/{ticket_id}/resolve` |
| POST | `/helpdesk/{ticket_id}/reopen` |
| GET | `/helpdesk/{ticket_id}/history` |

Audit actions use `metadata.central_department_id` for Phase 9 audit visibility.

---

## Module 10.2 — Placement & Research Coordination

### Design

- **Not a Placement Cell** — coordination metadata only; official eligibility and recruiter data are out of scope.
- **Students** — directory via Phase 3 `list_students`; placement readiness text is advisory only.
- **Projects** — merges `department_project_coordinations` with read-only **LMS** `course_assignments` for department course codes (`project_id` prefix `lms:`).
- **Calendar** — research events read from Phase 6 calendar (`seminar`, `workshop`, `project_review` categories).
- **Internships** — `organization_verified` defaults **false**; Department Admin cannot certify organizations.
- **Research** — publication refs are unverified strings; ethics/approval remain institution-level.

### Permissions

- `department:placement:read` / `department:placement:manage` — overview, students, activities, internships, combined report.
- `department:research:read` / `department:research:manage` — projects (incl. LMS), reviews, research projects, events, report sections.

### Collections (new)

| Collection | Purpose |
|------------|---------|
| `department_placement_activities` | Dept placement/career sessions |
| `department_internship_coordinations` | Internship tracking |
| `department_project_coordinations` | Dept-owned project records |
| `department_research_projects` | Research directory |
| `department_project_reviews` | Review schedules |

### APIs (`/api/v1/department`)

| Method | Path |
|--------|------|
| GET | `/placement/overview` |
| GET | `/placement/students` |
| GET | `/placement/activities` |
| POST | `/placement/activities` |
| GET | `/internships` |
| POST | `/internships` |
| GET | `/projects` |
| GET | `/projects/{project_id}` |
| POST | `/projects/{project_id}/reviews` |
| GET | `/research/overview` |
| GET | `/research/projects` |
| POST | `/research/projects` |
| GET | `/research/events` |
| GET | `/placement-research/reports` |

---

## Responsibility boundaries

| Actor | Owns |
|-------|------|
| Placement Cell (not built) | Official placement eligibility, recruiter relationships |
| Research Office (not built) | Ethics approval, verified publications |
| College Admin | Escalated helpdesk targets, org verification |
| Department Admin | Department coordination records in this module |
| LMS | Course assignments (read-only project view) |

---

## Tests

- `backend/tests/test_department_admin_phase10.py` — RBAC, categories, transitions, activity types.

---

## Department Admin programme completion

With Phase 10 delivered, the **10-phase Department Admin backend plan** from the product breakdown is **implementation-complete** at the API/module level. Full programme sign-off still requires production verification (Mongo, workflows, cross-role integration) across Phases 1–10.

## Known limitations

1. Helpdesk requester portal (faculty/student) not implemented — Department Admin only.
2. Automatic calendar creation for placement activities not wired (optional `calendar_event_id` only).
3. No `department_project_coordinations` create API in this pass — LMS assignments listed; explicit project records can be added in a follow-up if needed.
4. Escalation outbox consumers not implemented.

---

_End of planned Department Admin backend phases._