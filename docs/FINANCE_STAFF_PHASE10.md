# Finance Staff — Phase 10 (Procurement & Expenses)

Aligned with `backend_and_frontend.md`. **Authoritative vendor / PR / PO / vendor invoice masters** remain `institution_vendor_records`, `institution_purchase_requests`, `institution_purchase_orders`, `institution_vendor_invoices` (extended, not duplicated). Finance-specific workflow, payables, bank details, and employee claims use Phase 10 collections.

## Procurement

| Extension collection | Purpose |
|---------------------|---------|
| `finance_vendors` | Restricted bank refs (hashed); not full PAN/account in API |
| `finance_vendor_verification_history` | Verification audit |
| `purchase_request_approval_history` | PR decisions |
| `purchase_order_items` / `purchase_order_history` | PO lines and audit |
| `vendor_invoice_verification_history` | PO/invoice matching |
| `vendor_payables` / `vendor_payments` | Payable balance and confirmed payments |
| `vendor_credit_notes` | Model ready; API via future enhancement |

APIs: `/accounts-finance/procurement/*` — vendors, PR/PO, invoices, verify, payments, summary reports.

Budget commitments use Phase 9 `finance_budgets` via `record_commitment` on issued POs.

GL: `vendor_invoice`, `vendor_payment` mapping events (`POST /general-ledger/mappings` seed via `phase10_gl_seed`).

## Expenses

| Collection | Purpose |
|------------|---------|
| `finance_expense_categories` / `finance_expense_policies` | Category and limits |
| `employee_expense_claims` (+ items, approval history) | Reimbursement workflow |
| `expense_payment_records` | Verified reimbursement payments |
| `employee_advance_records` / `employee_advance_settlements` | Advances |
| `department_expense_records` | Operational departmental expenses |

APIs: `/accounts-finance/expenses/*`

GL: `expense_reimbursement`, `expense_payment` events on approve/pay.

## Security

- `finance:vendor:bank` required for bank storage/view.
- Self-approval blocked for PR and expense claims.
- Invoice paid only after verification + `payment_reference`.

## Limitations

- Goods receipt / inventory three-way match is PO+amount only (no stock module hook).
- Vendor credit note API stub in model only.
- Employee identity uses ERP `User` ids; full HR employee linkage optional later.
- No notification module integration (Phase 10 scope).

## Tests

```bash
cd backend && py -m pytest tests/test_finance_staff_phase10.py -q
```