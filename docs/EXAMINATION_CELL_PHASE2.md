# Examination Cell — Phase 2 (Backend)

## Scope

1. **Assessment configuration** — component types, weightage, eligibility, rounding, versioning.
2. **Exam scheduling & timetable management** — drafts, validation, approval, publish, revisions.

Registration, hall tickets, seating, and marks entry are out of scope.

## Collections

| Collection | Purpose |
|------------|---------|
| `exam_assessment_configs` | Programme/term/subject assessment policy header |
| `exam_assessment_components` | Typed components with max marks and weightage |
| `exam_assessment_policy_versions` | Immutable configuration snapshots |
| `exam_timetables` | Timetable per `exam_sessions` record |
| `exam_timetable_entries` | Scheduled papers with venue links |
| `exam_timetable_revisions` | Audit trail for timetable lifecycle |
| `exam_schedule_approvals` | Review decisions |

## Integration (read-only references)

- **Courses**: `course_catalog_references`
- **Subjects**: `subject_catalog_references` (optional scope validation)
- **Exam sessions**: `exam_sessions` (Phase 1)
- **Venues**: `examination_centres` + `institution_facilities` (no duplicate campus inventory)
- **Campus**: `institution_campuses`

Exam timetable entries do **not** duplicate `timetable_entries` or `semester_examination_sessions`; they remain the examination-cell authoritative schedule for an exam session.

## Permissions

| Permission | Capability |
|------------|------------|
| `examination:assessment:read` | View configurations |
| `examination:assessment:manage` | Create/update/activate |
| `examination:timetable:read` | View timetables |
| `examination:timetable:manage` | Draft entries, submit, revise |
| `examination:timetable:approve` | Approve/reject |
| `examination:timetable:publish` | Publish approved timetables |

## API (`/api/v1/examinations/cell`)

### Assessment

- `POST /assessment-configurations`
- `GET /assessment-configurations`
- `GET/PATCH /assessment-configurations/{id}`
- `POST /assessment-configurations/{id}/activate`
- `GET /assessment-configurations/{id}/versions`

### Timetables

- `POST /timetables`
- `GET /timetables`
- `GET /timetables/{id}`
- `POST /timetables/{id}/entries`
- `GET /timetables/{id}/validate`
- `POST /timetables/{id}/submit|approve|reject|publish|revise`
- `POST /timetables/{id}/entries/{code}/cancel|reschedule`
- `GET /timetables/{id}/revisions|approvals|entries`

## Conflict detection

Active entries are checked for:

- Student group time overlap
- Subject group overlap (programme/batch/section/course)
- Room double-booking (`centre_code` + `room_label`)
- Facility double-booking (`facility_id`)

## Tests

```bash
cd backend
py -m pytest tests/test_examination_cell_phase2.py -q
```

## Limitations

- Student clash detection uses deterministic `student_group_label` (programme:batch:section:course), not per-student enrollment expansion.
- Publishing does not auto-sync `semester_examination_sessions` (avoids duplicate authoritative schedules).