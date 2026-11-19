# Finance Staff — Phase 1 (Dashboard + Fee Structure Management)

Aligned with `backend_and_frontend.md`. Authoritative student fee demands, invoices, payments and ledger remain in central finance collections — this module adds finance-staff configuration (`fee_categories`, `fee_structures`, …) and read aggregations for the staff dashboard.

## API prefix

`/api/v1/accounts-finance`

### Dashboard

| Method | Path | Permission |
|--------|------|------------|
| GET | `/dashboard` | `finance:dashboard:read` (or `college:finance:read`) |

Query filters: financial year, academic year, semester, programme, department, campus, fee category, invoice/payment status, payment method, date range.

Metrics read from `student_fee_assessments`, `student_fee_demands`, `student_fee_invoices`, `payment_transactions`, `refund_records`, `fee_concessions`, `official_scholarship_applications`, `payment_reconciliation_records`, and finance extensions where available. **Verified collections** count only offline-success or webhook-verified online success — pending gateway traffic is excluded.

Accounting GL balances return `availability.available=false` with reason when GL is not configured (Phase 1).

### Fee categories

| Method | Path | Permission |
|--------|------|------------|
| PUT | `/fee-categories` | `finance:fee_category:manage` |
| GET | `/fee-categories` | `finance:fee_category:read` |
| GET | `/fee-categories/{fee_code}` | `finance:fee_category:read` |

### Fee structures

| Method | Path | Permission |
|--------|------|------------|
| POST | `/fee-structures` | `finance:structure:manage` |
| GET | `/fee-structures` | `finance:structure:read` |
| GET | `/fee-structures/{structure_id}` | `finance:structure:read` |
| POST | `/fee-structures/{structure_id}/transitions` | manage (submit) / `finance:structure:approve` |
| POST | `/fee-structures/{structure_id}/revisions` | `finance:structure:manage` |

Lifecycle: `draft` → `submitted` → `approved` → (`scheduled`) → `active` | `suspended` | `expired` | `superseded` | `archived`.

**Active** structures sync to existing `student_fee_structures` and `institution_fee_structures` (no duplicate assessment/invoicing in Phase 1).

## Collections

| Collection | Model |
|------------|--------|
| `fee_categories` | `FinanceFeeCategory` |
| `fee_structures` | `FinanceFeeStructure` |
| `fee_structure_components` | `FinanceFeeStructureComponent` |
| `fee_structure_versions` | `FinanceFeeStructureVersion` |
| `fee_structure_approval_history` | `FinanceFeeStructureApprovalHistory` |

## Permissions

- `FINANCE_STAFF`: dashboard, categories, structures, approve, transactions read
- `ACCOUNTS_STAFF`: dashboard, categories, structures (no approve)
- `COLLEGE_ADMIN`: via existing `college:finance:*` overlay in policy

## Limitations (Phase 1)

- No student fee assessment, invoicing, or payment capture APIs in this module.
- No general ledger / journal posting; accounting overview uses finance extensions + explicit unavailability flags.
- Invoice “cancelled” derived from waived demands only.

## Tests

```bash
cd backend
py -m pytest tests/test_finance_staff_phase1.py -q --disable-warnings
```