# Finance Staff — Phase 7 (Refunds + Payment Reconciliation)

Aligned with `backend_and_frontend.md`. Extends `refund_records`, `refund_requests`, and `payment_reconciliation_records`; authoritative workflows live in Phase 7 collections. Original `payment_transactions` are never deleted.

## Collections

### Refunds & reversals
- `student_refund_requests`, `student_refund_approval_history`, `student_refund_transactions`, `student_refund_references`
- `student_payment_reversal_requests`, `student_payment_reversal_history`
- `PaymentTransaction.refunded_total` / `reversed_total` for cumulative limits

### Reconciliation
- `payment_reconciliation_periods`, `payment_reconciliation_batches`, `payment_reconciliation_imports`
- `payment_reconciliation_source_records`, `payment_reconciliation_matches`, `payment_reconciliation_exceptions`
- `payment_settlement_records`, `payment_reconciliation_history`

## APIs (`/api/v1/accounts-finance`)

### Refunds (`/refunds`)
- Dashboard, list, eligibility
- Create → approve → complete (requires `payout_reference`)
- Reversals create → approve (ledger `payment_reversal`)

### Reconciliation (`/reconciliation`)
- Periods, batches, CSV import, auto-match, confirm/unmatch, batch confirm
- Settlement fee capture, exceptions list, dashboard

## RBAC
`finance:refund:read|manage|approve`, `finance:reconciliation:read|manage|confirm`

## Integration
- Refund completion posts idempotent `refund` ledger debit; updates demand status when applicable
- Confirmed matches update legacy `payment_reconciliation_records`
- Financial period `closed` blocks new refund requests

## Tests
`backend/tests/test_finance_staff_phase7.py`

## Limitations
- Gateway payout API not integrated (manual `payout_reference` on completion)
- Excel import not implemented (CSV only)
- Multi-level refund approval rules stored via status workflow only (single approve step)
- Financial period closing / GL posting not in Phase 7 scope