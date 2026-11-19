# Examination Cell — Phase 3 (Backend)

## Scope

1. **Student eligibility & exam registration** — rule evaluation, subject-level outcomes, staff/student registration, bulk, correction/cancel, summaries.
2. **Hall ticket management** — generation, PDF storage, publish/revoke/reissue, verification, history.

Seating plans and marks entry are out of scope.

## Authoritative data (no duplicates)

| Need | Source |
|------|--------|
| Student identity | `users`, `student_profiles` |
| Enrollment | `student_academic_records`, `enrollment_roster_entries` |
| Attendance | `StudentDataReader.attendance_summary` |
| Fees | `examination_fee_payments` + `examination_registration_windows` |
| Arrear | `student_arrear_references` |
| Session / deadlines | `exam_sessions` (Phase 1) |
| Schedule on ticket | Published `exam_timetable_entries` (Phase 2) |
| Assessment attendance threshold | `exam_assessment_configs` (Phase 2) |

Cell-owned collections (not copies of student master data):

- `exam_eligibility_records`, `exam_eligibility_rule_results`
- `exam_registrations`, `exam_registration_subjects`, `exam_registration_history`
- `exam_hall_tickets`, `exam_hall_ticket_subjects`, `exam_hall_ticket_history`

Legacy `student_exam_registrations` / `examination_hall_tickets` remain for the student portal; the examination cell module uses the `exam_*` collections above.

## Permissions

`examination:eligibility:*`, `examination:registration:*`, `examination:hall_ticket:*` (+ existing `student:exam_registration:*` for self-service registration routes).

## API highlights (`/api/v1/examinations/cell`)

- `POST /eligibility/evaluate`
- `GET /eligibility/sessions/{session_id}/students/{student_id}`
- `POST /registrations`, `POST /registrations/bulk`
- `GET /sessions/{session_id}/registrations/summary`
- `POST /hall-tickets/generate`, `/generate/bulk`, `/verify`, `/{id}/download`

Hall ticket **verification** uses HMAC-SHA256 over `ticket_number` and `student_user_id` with server `jwt_secret`.

PDFs are stored under LMS storage (`data/lms/.../exam_hall_tickets/`).

## Tests

```bash
cd backend
py -m pytest tests/test_examination_cell_phase3.py -q
```

## Limitations

- Fee verification depends on finance module populating `examination_fee_payments` (no client-side payment trust).
- Eligibility does not expand per-student timetable clash against exam entries (group-level scheduling is Phase 2).
- Student self-registration on cell APIs does not auto-mirror into legacy `student_exam_registrations`.