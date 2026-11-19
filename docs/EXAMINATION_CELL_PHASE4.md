# Examination Cell — Phase 4 (Backend)

## Scope

1. **Examination logistics & seating plan** — venues/rooms overlaying campus centres, auto-allocation, attendance sheets, invigilation, approval/publish.
2. **Marks entry & assessment management** — examiner access, draft/submit/moderate/approve, corrections, import, subject summaries.

Final grading and result publication remain out of scope.

## Authoritative data (read-only)

| Need | Source |
|------|--------|
| Campus / centres / rooms | `institution_campuses`, `examination_centres`, `institution_facilities` |
| Registered candidates | `exam_registrations`, `exam_registration_subjects` |
| Assessment limits | `exam_assessment_configs`, `exam_assessment_components` |
| Faculty identity | `users` (invigilator assignments) |

Cell-owned collections:

- `exam_venues`, `exam_rooms`, `exam_seating_plans`, `exam_seating_allocations`, `exam_invigilator_assignments`, `exam_duty_history`
- `exam_marks_submissions`, `exam_marks_entries`, `exam_marks_components`, `exam_marks_corrections`, `exam_marks_history`

## Permissions

- `examination:seating:read|manage|publish`
- `examination:marks:read|enter|manage|moderate` (+ `college:examination:marks` admin fallback)

## API highlights (`/api/v1/examinations/cell`)

**Seating**

- `POST /venues`, `POST /rooms`
- `POST /seating-plans`, `POST /seating-plans/allocate`
- `POST /seating-plans/{id}/submit`, `POST /seating-plans/{id}/publish`
- `GET /seating-plans/{id}/allocations`, `GET .../summary`, `GET .../rooms/{room_id}/attendance`
- `POST /invigilator-assignments`, `POST /seating-allocations/{id}/change`

**Marks**

- `POST /marks/access`
- `POST /marks/submissions/{id}/entries`, `/entries/bulk`, `/submit`, `/moderate`, `/approve`
- `POST /marks/submissions/{id}/import`, `GET .../summary`, `GET .../history`
- `POST /marks/submissions/{id}/corrections`, `POST /marks/corrections/{id}/approve|reject`

## Consistency

Seat and student uniqueness enforced via MongoDB unique indexes (`unique_student_per_seating_plan`, `unique_seat_per_room_plan`). Marks submissions lock entries on approval; edits blocked when status is `approved` or `locked`.

## Tests

```bash
cd backend
py -m pytest tests/test_examination_cell_phase4.py -q
```

Run with phases 1–3:

```bash
py -m pytest tests/test_examination_cell_phase1.py tests/test_examination_cell_phase2.py tests/test_examination_cell_phase3.py tests/test_examination_cell_phase4.py -q
```