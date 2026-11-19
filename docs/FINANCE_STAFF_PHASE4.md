# Finance Staff — Phase 4 (Ledger + Receipts)

Aligned with `backend_and_frontend.md`. Extends authoritative `student_financial_ledger` and `payment_receipts`; posting remains idempotent via `posting_key` + `student_ledger_posting_history`. Verified payments still flow through `payment_reconciliation.reconcile_successful_payment`.

## Collections

| Collection | Purpose |
|------------|---------|
| `student_financial_accounts` | Per-student balance aggregates |
| `student_financial_ledger` | Extended ledger rows (debit/credit, references, posting_key) |
| `student_ledger_posting_history` | Idempotent posting audit |
| `student_ledger_adjustments` | Adjustment workflow (reversal + correction) |
| `student_advance_payments` / `student_advance_allocations` | Advance tracking |
| `student_ledger_reconciliation_records` | Reconciliation exceptions |
| `payment_receipts` | Extended official receipts |
| `payment_receipt_versions` | Immutable receipt snapshots |
| `payment_receipt_cancellations` | Cancellation audit |
| `payment_receipt_number_sequences` | Tenant receipt numbering |
| `payment_receipt_document_history` | Issue / cancel / reissue history |

## APIs (`/api/v1/accounts-finance`)

### Ledger (`/ledger`)

- `GET /ledger/students/{student_user_id}/account` — overview balances
- `GET /ledger/students/{student_user_id}/statement` — filtered statement
- `GET /ledger/entries` — tenant ledger search
- `POST /ledger/adjustments?student_user_id=` — submit adjustment
- `POST /ledger/adjustments/{id}/approve` — post reversal + correction
- `POST /ledger/advances/{advance_id}/allocate` — allocate advance to invoice
- `POST /ledger/reconciliation/scan` — exception scan

### Receipts (`/receipts`)

- `GET /receipts` — search / filter
- `GET /receipts/register/daily?day=` — daily register
- `GET /receipts/by-number/{receipt_number}`
- `GET /receipts/{receipt_id}`
- `POST /receipts/generate/{transaction_id}` — manual issue (verified + posted)
- `POST /receipts/{receipt_id}/cancel`
- `POST /receipts/{receipt_id}/reissue`

## RBAC

- `finance:ledger:read`, `finance:ledger:manage`
- `finance:receipt:read`, `finance:receipt:issue`, `finance:receipt:manage`

Assigned on `FINANCE_STAFF`; read/issue subset on `ACCOUNTS_STAFF`.

## Integration

- Invoice issue → `ledger_posting_service.post_fee_invoice`
- Payment reconcile → `post_verified_payment` + `receipt_service.issue_receipt_from_payment`
- Parent portal continues to resolve `payment_receipts` by `receipt_id`
- Receipt publish → `finance_notify.enqueue_receipt_issued` outbox

## Tests

`backend/tests/test_finance_staff_phase4.py`

## Limitations (Phase 4 scope)

- Scholarships / refunds / GL posting modules not expanded — ledger types exist for future hooks
- PDF receipt documents use `storage_token` placeholder; template rendering deferred
- Bulk receipt generation API not added (search + manual generate per transaction)
- Cheque provisional vs final receipt policy uses standard verified-payment gate only