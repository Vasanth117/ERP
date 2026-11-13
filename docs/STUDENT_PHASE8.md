# Student Portal — Phase 8 (Arrear / Supplementary + Exam Review)

## Central authority

| Domain | Collections |
|--------|-------------|
| Supplementary exams | `supplementary_examination_seasons`, `arrear_eligibility_records`, `examination_attempt_records` |
| Review windows / fees | `examination_review_windows`, `examination_review_fee_payments` |
| Results & marks | `semester_result_subject_marks` (published only) |

**Not created:** `student_backlog_summary_views` — backlog summary computed from refs + results.

### Student collections

| Collection | Purpose |
|------------|---------|
| `student_arrear_references` | Backlog status per course |
| `student_exam_attempt_history` | Student-visible attempt timeline |
| `student_supplementary_registrations` | Supplementary exam registration |
| `student_revaluation_requests` | Revaluation applications |
| `student_rechecking_requests` | Rechecking applications |
| `student_marks_correction_requests` | Student-initiated corrections (separate from faculty `marks_correction_requests`) |
| `student_exam_review_request_history` | Workflow audit |
| `student_exam_review_payment_references` | Fee verification linkage |

## Permissions

- `student:arrear:read` / `manage`
- `student:exam_review:read` / `manage`

## API routes (prefix `/api/v1/students`)

**Arrear / supplementary**

- `GET /me/arrears/subjects`
- `GET /me/arrears/attempt-history`
- `GET /me/arrears/supplementary/{id}/eligibility`
- `GET /me/arrears/supplementary/schedules`
- `GET /me/arrears/supplementary/{id}/fees`
- `POST /me/arrears/supplementary/registrations`
- `GET /me/arrears/supplementary/registrations`
- `GET /me/arrears/backlog-summary`
- `GET /me/arrears/supplementary/{id}/results`

**Revaluation / rechecking**

- `GET /me/exam-review/eligible-subjects?season_id=`
- `GET /me/exam-review/fees?season_id=&review_type=`
- `POST /me/exam-review/revaluation`
- `POST /me/exam-review/rechecking`
- `POST /me/exam-review/marks-correction`
- `GET /me/exam-review/requests/{request_id}`
- `POST /me/exam-review/requests/{request_id}/withdraw`
- `GET /me/exam-review/history`
- `GET /me/exam-review/revised-marks?season_id=`

## Security

- Eligibility from published `arrear_eligibility_records` only
- Fee status from `examination_fee_payments` / `examination_review_fee_payments`
- Duplicate supplementary registration blocked (unique index)
- Duplicate active rechecking blocked
- Revised marks only when request `completed` and `revised_mark_published` with published result lines
- Audit on supplementary registration and review submissions

## Tests

```bash
cd backend
py -m pytest tests/test_student_arrear_exam_review.py tests/test_permissions.py -q
```
