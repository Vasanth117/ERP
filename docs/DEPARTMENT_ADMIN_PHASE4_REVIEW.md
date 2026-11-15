# Department Admin Phase 4 — Review & Gap Resolution Report

Date: review after initial Phase 4 implementation. **Phase 5 not started.**

## 1. Review findings (Task 1)

| Area | Status | Notes |
|------|--------|------|
| Tenant isolation | OK | Plans, slots, discrepancies keyed by `tenant_id`; dept via `resolve_authorized_department` / `central_department_id`. |
| Department authorization | OK | All routes use `department_admin_user` + permissions. |
| RBAC | OK | `department:timetable:*`, `department:attendance:*` on `DEPARTMENT_ADMIN` only. |
| Conflict detection | Partial | Faculty/section/room/lab/duration/duplicate + published overlap + leave warning; **no room capacity/type** (no master). |
| Timetable lifecycle | OK | `draft` → `submitted` → `approved` → `published`; `superseded` on republish. |
| Publish atomicity | **Fixed** | Supersede + entries + snapshot now in one transaction (was split). |
| Attendance discrepancies | **Improved** | Cancelled/rescheduled exclusion; deduped scan. |
| Correction approval | OK | Mirrors college pattern; dept-scoped faculty; `AttendanceCorrectionApproval` + audit. |
| Institutional policy | OK | `InstitutionAttendancePolicy` / `AttendancePolicyReference`; threshold not hardcoded when policy exists. |
| Audit | Partial | Timetable create/publish + correction review; **submit/approve timetable not audited**. |
| Idempotency | Partial | Publish `idempotency_key` on plan; slot **revision** optimistic lock present. |
| Concurrent publish | Partial | Idempotency helps; **no distributed lock** across two plans same term. |

### Bugs identified and disposition

| Bug | Severity | Action |
|-----|----------|--------|
| Publish supersede outside Mongo transaction | High | **Fixed** — moved into `run_in_transaction`. |
| Missing attendance counted cancelled classes | High | **Fixed** — `attendance_eligibility.py`. |
| Discrepancy scan inserted duplicates | Medium | **Fixed** — unique index + upsert/find by summary/session. |
| Dead branch `faculty_not_in_department` in scan | Low | **Removed** (query already dept-filtered). |
| Overview `missing_submission_count` ignored cancellations | Medium | **Fixed** — recomputed via eligibility filter. |
| `excessive_records` heuristic (count > 500) | Low | **Removed** from scan (unreliable). |

### Missing tests (before this review)

- Cancelled/rescheduled exclusion (added `test_attendance_eligibility.py`).
- Publish transaction integration (requires replica-set Mongo).
- Cross-department deny (dept isolation).
- Concurrent slot revision conflict.

## 2. Cancelled-session exclusion (Task 2) — implemented

New module: `app/modules/department_admin/attendance_eligibility.py`

**Sources consulted:**

- `ClassSession.status`: `cancelled`, `rescheduled`, `completed`, `scheduled` (faculty timetable service).
- `TimetableEntryStatus`: `active`, `cancelled`, `rescheduled`.
- `PendingAttendanceSubmission` + `AttendanceSession` (submitted ⇒ not missing).

**Rules:**

1. Exclude pending/missing if attendance already **submitted** for that date/class/section.
2. Exclude if a matching `ClassSession` on that calendar date is `cancelled` or `rescheduled`.
3. Exclude if a recurring `TimetableEntry` for that weekday/course/section is `cancelled` or `rescheduled`.
4. Scan creates `missing_attendance_submission` only when still expected; `completed_session_no_attendance` when `ClassSession` is `completed` without submitted attendance.

**Dedup:** unique partial index on `(tenant_id, central_department_id, discrepancy_type, session_id)`; summary-based dedup for pending/completed types without `session_id`.

## 3. Room master integration (Task 3) — investigation

**Finding:** There is **no** college-admin classroom/laboratory master collection. Rooms appear as **string labels** on `TimetableEntry` (`room`, `room_id`, `laboratory`). Faculty `list_classrooms` aggregates strings from timetable entries only.

`InstitutionCampus` exists (`institution_campuses`) but is **not** a room catalog.

**Conclusion:** Reuse **not possible** today without a new **shared** college-level facility module (owned by College Admin, read by Department Admin).

**Proposed minimal shared design (not implemented — needs approval):**

- Collection: `institution_rooms` (tenant-scoped): `room_id`, `code`, `name`, `campus_id`, `room_type` (classroom|laboratory|seminar), `capacity`, `department_id` (optional owner), `is_active`, `metadata`.
- Department Admin: **read** + validate `room_id` on draft slots; **no** create/delete without delegation permission.
- Timetable publish: resolve `room_id` → capacity/type checks in conflict engine.
- Index: unique `(tenant_id, code)`.

## 4. Lab group configuration (Task 4) — investigation

**Existing structures:**

- `department_sections.capacity` (Phase 3) — section-level strength, not practical groups.
- `SessionType.LABORATORY` on timetable entries.
- Student practical views via `ClassSession` / examination metadata — **no** `practical_group` entity.

**Conclusion:** Insufficient data to implement group allocation without institutional policy.

**Proposed configuration (policy decisions required):**

| Decision | Options |
|----------|---------|
| Group definition | Per subject + batch + section vs per lab session instance |
| Group identifier | `G1..Gn` vs roll-number ranges |
| Capacity source | Section capacity split vs dedicated `practical_group_configs` |
| Student allocation | College Admin enrollment vs Department Admin only |
| Faculty/lab binding | Same as lecture assignment vs separate practical assignment |

**Minimal future model (when approved):** `practical_group_configs` referencing `tenant_id`, `course_code`, `section`, `batch_label`, `group_code`, `capacity`, `laboratory_room_id`, optional student roll ranges — timetable conflict would sum enrolled per group.

## 5. Timetable change auto-application (Task 5) — design proposal only

**Current:** `department_timetable_change_requests` — `change_type`, `reason`, `new_values`, status `pending`; **no auto-apply**.

| Request type | Suggested approver | On approve |
|--------------|-------------------|------------|
| `substitute_faculty` | Dept admin (+ college if cross-dept) | Update draft slot or published entry via controlled patch; log `TimetableChangeLog` |
| `room_change` | Dept admin | Validate room master when available; update slot/entry |
| `cancel_session` | Dept admin | Set `ClassSession`/`TimetableEntry` to `cancelled`; cancel `PendingAttendanceSubmission` |
| `reschedule` | Dept admin | New times; mark old `rescheduled`; conflict re-check |
| `slot_create` / `slot_delete` | Dept admin | Mutate `department_timetable_slots` only while plan draft/submitted |

**State:** change request `pending` → `completed` | `rejected`; published plan changes may require **new plan version** or college re-publish policy (TBD).

**Attendance impact:** On `cancel_session`, delete or dismiss related `PendingAttendanceSubmission`; do not alter submitted `AttendanceSession` history.

**Notifications:** Post-commit outbox events (`timetable.change.applied`) — same pattern as section transfer.

**Transactions:** Apply slot + log + optional `TimetableEntry` patch in one Mongo transaction; notifications after commit.

## 6. MongoDB transaction verification (Task 6)

**Implementation:** `app/common/mongo_transactions.py` → `assert_transactions_supported()` (`hello.setName`); `run_in_transaction()` wraps `start_transaction`.

**Publish path** (`publish_timetable`):

1. Supersede prior published plans (same transaction).
2. Insert each `TimetableEntry`.
3. Insert `TimetableChangeLog` per entry.
4. Update plan status/version/idempotency key.
5. Insert `department_timetable_publish_snapshot`.

**On failure:** `503 TRANSACTIONS_UNAVAILABLE` — **no** non-transactional fallback.

**Gap:** `record_audit` for publish runs **after** transaction (acceptable for audit; not atomic with publish).

**Required config:**

- Dev/test: MongoDB **replica set** (even single-node RS) — same as Phase 3 section transfers.
- Production: managed RS; do not use standalone for publish/transfer paths.

## 7. Tests and documentation

| Test file | Result (this environment) |
|-----------|---------------------------|
| `tests/test_timetable_conflicts.py` | **2 passed** |
| `tests/test_attendance_eligibility.py` | **ERROR** at setup — Mongo/Beanie not initialized (`get_motor_collection`) |
| `tests/test_department_admin_phase4.py` | **ERROR** at setup — same |

Run with Docker replica-set Mongo per project README for integration tests.

## 8. Files modified in gap resolution

- `app/modules/department_admin/attendance_eligibility.py` (new)
- `app/modules/department_admin/attendance_oversight_service.py`
- `app/modules/department_admin/timetable_management_service.py`
- `app/modules/department_admin/models.py` (discrepancy unique index)
- `tests/test_attendance_eligibility.py` (new)
- `docs/DEPARTMENT_ADMIN_PHASE4.md` (updated)
- `docs/DEPARTMENT_ADMIN_PHASE4_REVIEW.md` (this file)

## 9. Remaining blockers (not production-ready)

1. **Room/facility master** absent — capacity/type validation blocked.
2. **Lab practical groups** — no policy or schema.
3. **Timetable change auto-apply** — design only.
4. **Publish/transfer integration tests** — need replica-set Mongo in CI.
5. **College delegation** for attendance correction vs college-only — not configured in settings.
6. **Workload regulation** not enforced on timetable slot create.
7. **Approve timetable** does not re-run validation (submit does).
8. **Late submission** metric still placeholder.

## 10. Production readiness

**Not claimed.** Evidence: unit conflict tests pass; integration tests require Mongo; known blockers above; college/faculty/student modules intentionally untouched.