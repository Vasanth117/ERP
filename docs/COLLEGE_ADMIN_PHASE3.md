# College Admin Phase 3

Academic configuration (module 5) and student administration (module 6) for college administrators.

Base path: `/api/v1/college-admin`

## Academic configuration

Prefix: `/academic-config`

| Endpoint | Description |
|---|---|
| `GET/POST /years`, `PATCH /years/{id}`, `POST /years/{id}/publish` | Academic years; publish syncs `academic_year_context` |
| `GET/POST /terms` | Semesters / terms scoped to a year |
| `POST /calendars`, `POST /calendars/{id}/publish` | Calendar events; publish mirrors `academic_calendar_events` |
| `POST/GET /programmes` | Programme catalogue (`academic_programmes` + department link) |
| `PUT /regulations`, `POST /regulations/{id}/publish` | Grading, attendance, progression, examination, registration rules |
| `POST /courses`, `POST /sections` | Writes authoritative `course_records` and `section_offerings` |
| `GET /configuration-history` | `academic_configuration_versions` audit trail |

Publication locks immutable resources where enforced (e.g. published academic years).

## Student administration

Prefix: `/student-administration`

| Endpoint | Description |
|---|---|
| `POST/GET /admissions`, `POST /admissions/{id}/confirm` | Admission pipeline |
| `POST/GET /students`, `GET/PATCH /students/{id}` | Creates `users` + `student_records`, syncs `student_profiles` |
| `POST /students/{id}/status` | Lifecycle transitions + `student_status_history` |
| `POST /students/{id}/enrollments` | Authoritative `student_enrollments` |
| `POST /students/{id}/transfer`, `/promotion` | Transfer and promotion records |
| `POST /students/{id}/guardians` | `student_guardian_relationships` |
| `GET /students/{id}/academic-history` | Enrollments, status, transfers, promotions |
| `POST /students/bulk` | Bulk import (max 100) |
| `POST /profile-corrections/decide` | Approves `student_profile_correction_requests` |

Document references reuse portal collection `student_document_references` (read via student portal modules).

## Collections

**Academic:** `academic_years`, `academic_terms`, `academic_calendars`, `academic_programmes`, `academic_regulations`, `academic_configuration_versions`.

**Student admin:** `student_admissions`, `student_records`, `student_status_history`, `student_transfers`, `student_promotion_records`, `student_guardian_relationships`.

**Reused authoritative stores:** `academic_year_context`, `academic_calendar_events`, `course_records`, `section_offerings`, `grading_policies`, `attendance_policy_references`, `student_profiles`, `student_enrollments`, `users`, `departments`.

## Security

- Permissions: `college:academic:read`, `college:academic:manage`, `college:student_admin:read`, `college:student_admin:manage` (included on `COLLEGE_ADMIN`)
- `authorize()` on every service entry; `require_college_tenant_scope()` for tenant isolation
- Duplicate guards: academic year code, roll number, student id, enrollment uniqueness per term/course
- Student user creation uses institutional password policy; guardians stored with relationship metadata (portal PII rules still apply on student self-service)

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase1.py tests/test_college_admin_phase2.py tests/test_college_admin_phase3.py -q --disable-warnings
```

Phase 3 coverage: year publish → context, duplicate identifiers, admission → record + profile sync, enrollment conflict, transfer, RBAC denial, cross-tenant isolation.

## Known gaps (vs full ERP prompt)

- Dedicated syllabus/curriculum approval APIs (reuse `curriculum_records` / faculty workflows for now)
- First-class course registration period admin (partial via `registration` regulation scope)
- Explicit college-admin CRUD for `student_document_references`

These can be extended in a follow-up without changing the Phase 3 collection layout.
