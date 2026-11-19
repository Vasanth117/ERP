# Department Admin — Phase 7

Phase 7: **Module 1 Requests & Approvals** and **Module 2 Department Resources**.

## Acceptance status

| Label | Meaning |
|-------|---------|
| **Implementation-complete** | Code, RBAC, routes, and unit tests delivered; review fixes applied (see below). |
| **Pending production verification** | Not production-ready until Mongo integration, tenant-isolation, workflow, and regression tests pass. |

**MongoDB integration tests remain deferred** by project decision.

---

## Final review (Phase 7 gate)

### 1. Requests & Approvals

| Check | Result |
|-------|--------|
| Aggregated requests scoped to tenant + department | **Pass** — aggregator queries use `tenant_id` and `central_department_id` (or `institution_department_id` for profile). Section transfers include **source or destination** department. Attendance corrections filtered by department faculty set. Timetable changes scoped via department timetable plans. |
| Approve/reject delegates to existing services | **Pass** — `section_transfer` → `review_section_transfer`; `student_correction` → `review_correction_request`; `attendance_correction` → attendance oversight review. Simple categories update canonical status only (no slot changes for timetable). |
| Self-approval restrictions | **Pass** for `SIMPLE_APPROVE_CATEGORIES` and **student correction approve**. Section transfers use existing `assert_reviewer_may_act`. **Gap (documented):** student correction **reject** and attendance correction do not block “requester == reviewer” because requesters are typically faculty/student, not the dept admin actor. |
| Profile changes forward-only | **Pass** — `FORWARD_ONLY_APPROVE`; approve/reject return 403. |
| Forward / escalate → outbox + coordination log | **Pass** — `_append_coordination` append-only records; `DomainOutboxEvent` with idempotent keys for `department.request.forwarded`, `.escalated`, `.information_requested`; approve also queues `department.request.approved`. |
| Cross-tenant / cross-department request IDs | **Pass (after fix)** — `_ensure_request_visible` requires request to appear in department aggregator before get/mutate. Timetable approve also validates plan `central_department_id`. |

**Review fixes applied (Phase 7 only):**

1. **GET request no longer creates coordination log rows** (read was inserting documents).
2. **Mutations require inbox visibility** via `_ensure_request_visible`.
3. **Timetable change approve/reject** validates owning timetable plan department.
4. **Section transfer inbox** includes destination department transfers.
5. **History** section-transfer steps scoped to tenant + source/destination department.

### 2. Department Resources

| Check | Result |
|-------|--------|
| Read-only directory; no duplicate facility/inventory | **Pass** — synthesized from `department_timetable_slots`, `timetable_entries`, optional `library_catalog_items` (equipment categories only). No new facility master. |
| Resource requests & issues scoped | **Pass** — `tenant_id` + `central_department_id` on create/list; idempotency keys tenant-scoped. |
| Availability advisory | **Pass** — `UTILIZATION_ADVISORY` always returned on classroom/lab availability (not a booking guarantee). Non room/lab IDs return explicit note that check does not apply. |
| Utilization accuracy / limitations | **Pass** — `ResourceUtilizationRead.advisory` describes timetable-derived counts and missing facility master. |

### 3. General quality

| Area | Result |
|------|--------|
| Routes | **19** on `phase7_router` (9 requests + 10 resources) |
| RBAC | `department:requests:read\|manage`, `department:resources:read\|manage` on `Role.DEPARTMENT_ADMIN` |
| Beanie | `DepartmentRequestCoordinationLog`, `DepartmentResourceRequest`, `DepartmentResourceIssue` in `database.py` |
| Validation | Pydantic schemas in `phase7_schemas.py`; forward target enum; reject body requires reason |
| Audit | Approve, resource request create, resource issue report |
| Service boundaries | No changes to College Admin / Faculty / Student modules; orchestration only in `department_admin` |
| Duplicate logic | Inbox aggregation is new; decisions reuse Phase 2–4 services where specified |

### Unit / regression tests run

```
tests/test_department_admin_phase7.py        — 3 passed
tests/test_department_admin_phase6_rbac.py   — 2 passed
tests/test_calendar_conflict_detection.py  — 3 passed
```

**8 passed** total (no Mongo `db_ready` tests).

---

## Confirmed product decisions (unchanged)

- Timetable change **approve = status only** — no automatic slot apply.
- Forward to college / HR / examination cell = **outbox handoff only** — no college workflow in Phase 7.
- Inbox merge cap **80 items per category**, in-memory sort/pagination — not suitable for very large histories without server-side cursor (future).
- **No** college facility master or new inventory system in Phase 7.

---

## Module 7.1 — Requests & Approvals

### Unified request ID

`{category}:{mongo_object_id}`

### Categories

| Category | Canonical collection | Hub approve/reject |
|----------|----------------------|--------------------|
| `section_transfer` | `department_section_transfer_requests` | Delegate |
| `student_correction` | `department_student_correction_requests` | Delegate (+ self-approve block on approve) |
| `attendance_correction` | `attendance_correction_requests` | Delegate |
| `timetable_change` | `department_timetable_change_requests` | Status only |
| `substitute_faculty` | `department_substitute_requests` | Status only |
| `faculty_assignment` | `department_faculty_assignment_requests` | Status only |
| `course_offering` | `department_course_offering_requests` | Status only |
| `profile_change` | `department_profile_change_requests` | **Forward / escalate only** |
| `resource_request` | `department_resource_requests` | Status only |

### Permissions

- `department:requests:read`
- `department:requests:manage`

### APIs (`/api/v1/department`)

See prior sections; paths under `/requests` and `/requests/{request_id}/*`.

### Pagination limitation

List/summary loads up to **80 records per category**, merges, then applies `limit`/`offset`. Older items beyond the cap do not appear until filtering by category or a future cursor API.

---

## Module 7.2 — Department Resources

### Permissions

- `department:resources:read`
- `department:resources:manage`

### APIs

Paths under `/resources`, `/resources/requests`, `/resources/issues`, `/resources/utilization`, `/resources/availability`.

**Equipment directory** is tenant-wide library catalog filter — not department-owned inventory (college remains authoritative).

---

## Remaining limitations (pre-production)

- No Mongo-backed tenant-isolation, workflow, concurrency, or notification delivery tests.
- Approve on faculty assignment / course offering / substitute does **not** invoke college admin publishers.
- Resource issue outbox does not create college helpdesk tickets.
- `request-information` does not change canonical request status (overlay only).
- Equipment list capped at 200 catalog rows per request.

---

## Next phase

Phase 7 is **implementation-complete, pending production verification**. Phase 8 (Reports & Analytics / Data Import & Export) may start after stakeholder sign-off on this review.