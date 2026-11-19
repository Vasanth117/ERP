# Department Admin — Phase 2 (Faculty + Academic/Curriculum)

## Module 1 — Faculty management

Reuses `faculty_profiles`, `faculty_records`, `faculty_assignments`, `faculty_workloads`, `faculty_teaching_assignments`, `leave_requests`, `timetable_entries`.

New workflow collections:

| Collection | Purpose |
|------------|---------|
| `department_faculty_assignment_requests` | Assign/transfer requests (no HR master change) |
| `department_substitute_requests` | Substitute coordination (does not overwrite timetable) |

### Permissions

- `department:faculty:read` — directory, profiles, workload, substitutes (read)
- `department:faculty:manage` — teaching assignments, substitute/assignment requests

### API (`/api/v1/department/faculty*`)

Directory, profile, availability, workload, assignments CRUD, unassigned subjects, substitute requests, faculty assignment requests.

### Workload limits

Read from `academic_regulations` where `scope_key=faculty_workload` and `rules.max_total_hours`. **No hardcoded cap** if regulation missing.

### Assumptions

- Department admin may create `faculty_assignments` for department courses; college admin retains full `faculty-administration` authority.
- Substitute approval and timetable swap are **not** auto-applied in Phase 2.
- Cross-department faculty appear in directory if they have assignments to department courses.

## Module 2 — Academic & curriculum

Reuses `academic_programmes`, `curriculum_records`, `courses`, `subjects`, `section_offerings`, `course_coverage`, `student_profiles`, `student_academic_records`.

New collection:

| Collection | Purpose |
|------------|---------|
| `department_course_offering_requests` | Proposed offerings pending college publish |

### Permissions

- `department:academic:read` — lists and progression/coverage reads
- `department:academic:manage` — draft programme create/update, offering requests

### API

`/programmes`, `/curricula`, `/subjects`, `/course-offerings`, `/curriculum-coverage`, `/academic-progression`.

### Assumptions

- New programmes are created as `DRAFT` / `is_active=false`; college admin must publish.
- POST `/course-offerings` creates a **request**, not a live `section_offerings` row.
- Curriculum version **writes** beyond draft programmes are deferred; reads use existing college-published data.
- Coverage uses faculty-reported `course_coverage` only; no invented percentages.

## Tests

```powershell
cd backend
pytest tests/test_department_admin_phase1.py tests/test_department_admin_phase2.py -q
```

Requires MongoDB replica set and Redis optional (same as other integration tests).