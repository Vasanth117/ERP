# Finance Staff — Phase 6 (Installments + Late Fees / Outstanding Dues)

Aligned with `backend_and_frontend.md`. Phase 6 adds staff-authoritative plans in `student_installment_schedules` while publishing read copies to legacy `fee_installment_schedules` for the student portal. Late fees post through Phase 4 `ledger_posting_service` (`late_fee` / `late_fee_waiver`).

## Collections

| Collection | Purpose |
|------------|---------|
| `student_payment_plans` | Plan templates |
| `student_payment_plan_assignments` | Student assignments |
| `student_installment_schedules` | Active schedules + line items |
| `student_installment_payments` | Payment-to-installment allocations |
| `student_installment_history` | Schedule change audit |
| `student_installment_reschedule_requests` | Reschedule workflow |
| `late_fee_policies` | Configurable late fee rules + ageing buckets |
| `student_late_fee_assessments` | Calculated charges |
| `student_late_fee_transactions` | Posted charge records (idempotent `posting_key`) |
| `student_late_fee_waivers` | Waiver audit + ledger link |

## APIs (`/api/v1/accounts-finance`)

### Installments (`/installments`)

- `GET|POST /plans`
- `POST /assignments`, `POST /assignments/{id}/approve`
- Reschedule submit/approve
- `GET /reports/summary`

### Dues (`/dues`)

- `GET /dashboard`
- `GET /students/overdue`, `GET /students/{id}/statement`
- Late fee policies, batch `POST /late-fee/process`, assessment approve, waivers

## RBAC

- `finance:installment:*`, `finance:late_fee:*`, `finance:outstanding:read`

## Integration

- `payment_reconciliation` → `apply_payment_to_installments` after verified payment
- Late fee batch is idempotent per demand period (`late_fee:{period_key}`)
- Notifications via `finance_notify` outbox events
- Outstanding dashboard uses demands, installments, ledger, aid awards

## Tests

`backend/tests/test_finance_staff_phase6.py`

## Limitations

- No cron worker bundled; staff (or external scheduler) calls `POST /dues/late-fee/process`
- Bulk group assignment uses repeated single assignment API
- Early settlement creates manual payment only (no dedicated API)
- Refunds/reconciliation modules not extended in Phase 6