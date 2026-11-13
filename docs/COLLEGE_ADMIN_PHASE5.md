# College Admin Phase 5

Examination administration (module 9) and finance administration (module 10).

Base path: `/api/v1/college-admin`

## Examination administration

Prefix: `/examination-administration`

| Endpoint | Description |
|---|---|
| `PUT /configurations` | Season config, components → `examination_configurations` + `assessment_components` |
| `POST /seasons`, `POST /sessions` | Seasons and sessions sync to `semester_examination_seasons` / `semester_examination_sessions`; admin schedule log in `college_examination_schedules` |
| `PUT /registration-windows` | `examination_registration_windows` |
| `PUT /eligibility`, `GET /eligibility/{season_id}` | Updates `student_examination_eligibility` + history |
| `POST /hall-tickets`, `POST .../publish` | `examination_hall_tickets` workflow |
| `GET /marks/pending`, `POST /marks/review` | `marks_submission_batches` approval |
| `POST /results/publish` | `semester_result_publications` (protected until publish permission) |
| `PUT /review-windows` | Revaluation/supplementary windows |
| `GET /reports/{season_id}`, `POST /centres` | Operational reports and centres |

Permissions: `college:examination:read`, `config`, `marks`, `publish` (separated).

## Finance administration

Prefix: `/finance-administration`

| Endpoint | Description |
|---|---|
| `PUT /fee-structures`, `POST .../publish` | `institution_fee_structures` → `student_fee_structures` |
| `POST /assessments` | Assessments, demands, invoices, ledger debit |
| `POST /collections/offline` | Idempotent `payment_transactions` + reconciliation |
| `GET /transactions`, `POST /reconciliation` | Ledger reconciliation records |
| `GET /ledger/{student_user_id}` | `student_financial_ledger` |
| `POST /concessions`, `POST .../approve` | `fee_concessions` with approval log |
| `POST /refunds`, `POST /refunds/decide` | `refund_records` + `refund_requests` |
| `PUT /periods`, `GET /reports/summary` | `financial_periods`, finance KPIs |

Permissions: `college:finance:read`, `config`, `manage`, `transactions`, `reconcile`, `approve`.

## Collections

**Examination admin overlays:** `examination_configurations`, `examination_sessions`, `examination_schedules`, `examination_eligibility_records`, `hall_ticket_records`, `examination_marks`, `examination_approval_records`, `examination_result_publications` (audit log).

**Finance admin overlays:** `institution_fee_structures`, `student_fee_assessments`, `financial_periods`, `payment_reconciliation_records`, `financial_approval_records`, `refund_requests`.

**Reused authoritative:** semester examination models, hall tickets, results, fee demands/invoices, ledger, `payment_transactions`, `payment_receipts`, concessions, refunds.

## Security

- Result and hall ticket publication require `college:examination:publish`
- Marks review requires `college:examination:marks`
- Refunds/concessions require `college:finance:approve`
- Offline/online payments use idempotency keys; webhook verification via existing `payment_verification`
- Tenant isolation on all queries

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase5.py tests/test_college_admin_phase1.py … phase4.py -q --disable-warnings
```
