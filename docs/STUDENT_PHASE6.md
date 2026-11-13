# Student Portal — Phase 6 (Exam Registration, Hall Tickets, Results)

## Collection ownership

| Data | Central (authoritative) | Student portal |
|------|-------------------------|----------------|
| Registration windows & fees | `examination_registration_windows`, `examination_fee_payments` | Submissions in `student_exam_registrations` |
| Eligibility | `student_examination_eligibility` | Read only (Phase 5) |
| Hall tickets | `examination_hall_tickets` | `student_hall_ticket_references`, `student_hall_ticket_download_logs` |
| Official marks / results | `semester_result_publications`, `semester_result_subject_marks` | **No duplicate** official marks |

### Required student collections

| Collection | Purpose |
|------------|---------|
| `student_exam_registrations` | Registration header |
| `student_exam_registration_subjects` | Per-subject lines (unique per season/course) |
| `student_exam_registration_history` | Audit trail |
| `student_hall_ticket_references` | Last viewed / availability cache |
| `student_hall_ticket_download_logs` | Download audit |
| `student_result_view_preferences` | UI preferences |
| `student_result_notifications` | Result notices |

## Permissions

- `student:exam_registration:read`
- `student:exam_registration:manage` (submit / cancel)
- `student:exam_results:read`

## API routes (prefix `/api/v1/students`)

**Registration**

- `GET /me/exam-registrations/eligible`
- `GET /me/exam-registrations/seasons/{season_id}/schedule`
- `GET /me/exam-registrations/seasons/{season_id}/eligibility`
- `GET /me/exam-registrations/seasons/{season_id}/subjects`
- `POST /me/exam-registrations`
- `GET /me/exam-registrations`
- `GET /me/exam-registrations/history`
- `GET /me/exam-registrations/{registration_id}`
- `POST /me/exam-registrations/{registration_id}/cancel`

**Hall tickets**

- `GET /me/hall-tickets/seasons/{season_id}/availability`
- `GET /me/hall-tickets/seasons/{season_id}`
- `POST /me/hall-tickets/seasons/{season_id}/download`

**Results**

- `GET /me/exam-results/seasons/{season_id}`
- `GET /me/exam-results/marks`
- `GET /me/exam-results/attempt-history`
- `GET /me/exam-results/arrears`
- `GET /me/exam-results/seasons/{season_id}/publication-status`
- `GET /me/exam-results/notifications`

## Security

- Fee status read only from `examination_fee_payments` (`paid` / `waived`)
- Duplicate registration blocked by unique index on `(tenant, user, season, course_code)`
- Hall tickets only when `examination_hall_tickets.status=published` and student matches
- Results endpoints require `semester_result_publications.status=published` and `semester_result_subject_marks.published=true`
- Audit: registration submit/cancel, hall ticket download, result summary view

## Tests

```bash
cd backend
py -m pytest tests/test_student_exam_registration_results.py tests/test_permissions.py -q
```

Integration tests require MongoDB and Redis.
