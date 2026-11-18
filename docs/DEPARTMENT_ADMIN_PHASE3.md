# Department Admin — Phase 3 (Batch/Section/Class + Student Administration)

## Module 1 — Batch, section & class management

Reuses canonical enrollment fields on `student_records` / `student_profiles` (`batch_label`, `section_code`, `programme_code`). Reuses `section_offerings` and `faculty_assignments` for structure summaries.

New collections:

| Collection | Purpose |
|------------|---------|
| `department_batches` | Department-scoped batch definitions per programme |
| `department_sections` | Sections under a department batch (capacity, coordinator) |
| `department_section_transfer_requests` | Section transfer workflow with audit trail |

### Permissions

- `department:class:read` — batches, sections, class structure/strength, transfer reads
- `department:class:manage` — create/update batches and sections, submit transfers
- `department:student:manage` — approve section transfers (and student corrections)

### API (`/api/v1/department/...`)

- `GET|POST /batches`, `GET|PATCH /batches/{batch_id}`
- `GET|POST /batches/{batch_id}/sections`
- `GET|PATCH /sections/{section_id}`
- `GET /classes/structure`, `GET /classes/strength`
- `GET|POST /section-transfer-requests`, `GET .../{request_id}`, `POST .../{request_id}/review`

### Strength & structure

Student counts come from `student_profiles` filtered by `department_id`, programme, batch, and section. Offerings/faculty counts use current `AcademicYearContext` when present.

### Transfer rules (implemented)

| Scenario | Approval chain |
|----------|----------------|
| Same batch, section change | Source dept admin **if** `delegation_enabled` on department; otherwise college admin |
| Inter-batch, same department | Source dept admin + college admin when `inter_batch_section_transfer_requires_college_approval` (default **true**) |
| Cross-department | Source dept + destination dept + college admin |
| Cross-college | Rejected at API; use college administration |

- Students may submit via `POST /api/v1/students/me/section-transfer-requests` (`student:section_transfer:request`); they cannot approve.
- Separation of duties: the requester cannot approve their own request.
- Enrollment changes run **only after** all required approvals complete, inside a **MongoDB transaction** (replica set required).
- Optimistic checks: `student_record_updated_at` and destination `section.revision` captured at request time.
- Completion writes `department_section_transfer_history`, updates `student_records`, `student_profiles`, and matching `student_enrollments` section lines.
- Notifications: `domain_outbox_events` row `section_transfer.completed` (post-commit; no in-transaction notifications).
- College admin review: `POST /api/v1/college-admin/student-administration/section-transfer-requests/{id}/review`

### Institution setting

- `inter_batch_section_transfer_requires_college_approval` (bool, allowlisted in college institution settings; default **true** when unset).

### Assumptions / gaps

- Batch/section lifecycle defaults to `draft`; transfers require destination section `active`.
- `delegation_enabled` is a protected department setting (college admin seeds); without it, same-batch transfers need college admin approval.
- Outbox delivery worker not implemented in Phase 3 — events are persisted for a future processor.
- Academic eligibility rules beyond capacity are **not** configured yet — only capacity and section/batch validity.
- MongoDB must be a replica set; otherwise transfers return `503 TRANSACTIONS_UNAVAILABLE` (no silent non-transactional fallback).

## Module 2 — Student administration

Reuses `student_records`, `student_profiles`, `student_academic_records`, `student_enrollments`, `attendance_records`.

New collections:

| Collection | Purpose |
|------------|---------|
| `department_student_correction_requests` | Department-initiated academic field corrections |
| `department_student_follow_ups` | Department follow-up tracking |

### Permissions

- `department:student:read` — directory, academic profile, enrollment summary, follow-ups (read)
- `department:student:manage` — corrections, follow-ups, transfer/correction review

### API

- `GET /students` (filters), `GET /students/{student_id}`, `GET .../academic-profile`
- `GET /students/enrollment-summary`, `GET /students/unallocated`
- `GET|POST /student-correction-requests`, `POST .../{request_id}/review`
- `GET|POST /student-follow-ups`, `PATCH /student-follow-ups/{follow_up_id}`

### Fields Department Admin may correct (allowlist)

| Field | On approve |
|-------|------------|
| `roll_number` | Updates `student_records` + profile sync |
| `section_code` | Updates `student_records` + profile sync |
| `batch_label` | Updates `student_records` + profile sync |
| `programme_code` | Updates `student_records` + profile sync (uppercased) |

**Not** allowed: `admission_number`, `student_id`, identity/admission-owned fields (college admin / student portal flows).

### Assumptions / gaps

- Directory `semester_label` filter applies post-fetch against latest academic record (pagination total may be approximate when that filter is used).
- Enrollment status **changes** follow existing college admin workflows; this module does not invent new lifecycle rules.
- Academic profile is read-only aggregation (no financial/medical fields).
- Correction approval applies immediately; no separate college-admin second step unless policy is added later.

## Tests

```powershell
cd backend
pytest tests/test_department_admin_phase1.py tests/test_department_admin_phase2.py tests/test_department_admin_phase3.py -q
```

Requires MongoDB replica set (same as other integration tests).

## Completion status

Implementation delivered with integration tests; run pytest when Mongo is available. Phase 4 should not start until Phase 3 review is complete.