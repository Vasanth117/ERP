# Student Portal — Phase 2 (Curriculum + Course Registration)

## Scope

| Module | Routes prefix | Purpose |
|--------|---------------|---------|
| 3 — Course, subject & curriculum | `/students/me/curriculum/*` | Read-only access to approved academic content |
| 4 — Registration & electives | `/students/me/registration/*` | Self-service registration within policy windows |

Built on Phase 1 (`student_profiles`, programme context) and **central** academics collections (`courses`, `syllabus_records`, `curriculum_records`, `enrollment_rosters`, `timetable_entries`).

## Portal collections (configuration + student state)

| Collection | Role |
|------------|------|
| `course_catalog_references` | Programme-term registration catalogue (pointers to `course_id`) |
| `subject_catalog_references` | Semester subject ordering/credits overlay |
| `curriculum_references` | Programme regulations + pointer to central curriculum |
| `syllabus_references` | Syllabus **revision history** (units read from `syllabus_records`) |
| `course_prerequisites` | Prerequisite/corequisite/CGPA rules |
| `elective_groups` / `elective_options` | Elective pools and choices |
| `registration_policy_references` | Credits, deadlines, approval flags |
| `student_course_registrations` | Per-student course lines (unique per term+course) |
| `student_elective_selections` | Elective picks linked to groups |
| `course_registration_requests` | Submission bundle + validation snapshot |
| `student_registration_history` | Immutable lifecycle log |

## Permissions

- `student:curriculum:read` — all curriculum GET routes
- `student:registration:read` — catalogue, eligibility, validate, status, history
- `student:registration:manage` — submit, update, cancel

## Validation rules (registration)

1. Registration window (`registration_open_at` … `registration_close_at`)
2. `allow_self_registration` on policy
3. Course open in `course_catalog_references`
4. Prerequisites vs **approved** `student_course_registrations`
5. Min/max credits on policy
6. Optional timetable overlap check via `timetable_entries`
7. **Unique** compound index on `student_course_registrations` — duplicate inserts raise `409 CONFLICT`

## API summary

See OpenAPI `/docs` tag `students`. Key routes:

- `GET /me/curriculum/courses`, `.../subjects`, `.../syllabus`, `.../outcomes`, `.../prerequisites`, `.../info`
- `GET /me/registration/available-courses`, `elective-groups`, `eligibility`
- `POST /me/registration/validate`, `/submit`
- `PUT /me/registration/requests/{id}`, `POST .../courses/{course_id}/cancel`

## Tests

```bash
cd backend
py -m pytest tests/test_student_phase2.py tests/test_permissions.py -q
```

## Admin data

Institutional admins (future college admin APIs) populate catalogue, policies, prerequisites, and elective groups. Until then, seed via tests or scripts mirroring `test_student_phase2.py`.
