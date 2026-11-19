# Fines, Lost & Damaged Books (Librarian module — phase 8)

Overdue assessment, damage/lost charges, finance demands, verified payments, and approval-based waivers/write-offs.

## API (prefix `/api/v1/library/fines`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/policy` | Branch fine rules |
| POST | `/assess-overdue` | Batch overdue assessment |
| POST | `/reports` | Lost/damaged report + fine |
| GET | `` | Search fines |
| GET | `/{fine_id}` | Detail |
| POST | `/{fine_id}/demand` | Create `StudentFeeDemand` |
| POST | `/{fine_id}/verify-payment` | Mark paid from verified `PaymentTransaction` only |
| POST | `/{fine_id}/waiver-request` | Request waiver (librarian) |
| POST | `/{fine_id}/writeoff-request` | Request write-off |
| POST | `/{fine_id}/approval` | Approve/reject (`library:fine:approve`, not requester) |
| GET | `/{fine_id}/history` | Audit trail |

## Finance integration

- Fines post **debit** entries to `student_financial_ledger` on assessment.
- `StudentFeeDemand` links via `demand_id` on `library_fines`.
- `payment_reconciliation.reconcile_successful_payment` calls `on_demand_paid` — **webhook_verified SUCCESS only** updates fine balance.
- Librarian `verify-payment` re-checks transaction status; frontend cannot mark paid directly.

## Circulation hook

Returns run `process_return_fines`: overdue days × `fine_per_day` (policy), plus lost/damaged flat charges → `library_damage_reports`.

## Authorization

- **Librarian:** `library:fine:read`, `library:fine:manage` (no approve).
- **College admin:** `library:fine:approve` + manage bypass.
- Waiver/write-off: requester ≠ approver.

## Collections

`library_fines`, `library_fine_policies`, `library_fine_approvals`, `library_fine_history`, `library_damage_reports`

## Tests

```bash
cd backend && py -m pytest tests/test_library_fines.py -q
```