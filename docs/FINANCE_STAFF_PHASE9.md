# Finance Staff — Phase 9 (General Ledger & Budget)

Aligned with `backend_and_frontend.md`. Institutional **double-entry GL** is separate from the **student financial sub-ledger** (`student_financial_ledger`). System journals are posted idempotently via `posting_key` (`gl:{event}:{source}`) and versioned **accounting mapping rules** (no hardcoded accounts in business logic).

## General Ledger

### Collections

| Collection | Purpose |
|------------|---------|
| `chart_of_accounts` | Account master |
| `account_groups` | Hierarchical groups |
| `accounting_dimensions` | Department/campus/cost-centre refs |
| `accounting_mapping_versions` / `accounting_mapping_rules` | Approved event → DR/CR mapping |
| `journal_entries` / `journal_entry_lines` | Journal workflow |
| `journal_approval_history` | Status audit |
| `general_ledger_entries` | Posted lines (reporting source) |
| `account_opening_balances` | Year opening |
| `accounting_reversal_history` | Reversal audit |

### APIs (`/api/v1/accounts-finance/general-ledger`)

- Chart: `POST /chart/seed`, `GET|PUT /chart/accounts`, deactivate
- Mappings: versions, rules, `POST /mappings/seed-default`, activate
- Journals: create → submit → approve → post; reversal
- Reports: trial balance, account ledger, income & expenditure, balance sheet
- `POST /opening-balances`

### Automatic integration

After each student sub-ledger post (`ledger_posting_service.post_ledger_entry`), `gl_integration.mirror_student_ledger_to_gl` applies the **active mapping** when configured. Missing mappings are skipped (sub-ledger still authoritative).

## Budget

Collections: `finance_budgets`, `finance_budget_lines`, `finance_budget_allocations`, `finance_budget_revisions`, `finance_budget_commitments`, `finance_budget_approval_history`.

APIs under `/api/v1/accounts-finance/budgets` — overview, create, lines, submit/approve, allocations, commitments (idempotent by `reference_type` + `reference_id`), utilization, revisions.

Does not replace `institution_budgets` (college admin); Finance Staff budgets are the module specified for Phase 9.

## Permissions

- `finance:gl:read`, `finance:gl:manage`, `finance:gl:approve`, `finance:gl:journal_post`
- `finance:budget:read`, `finance:budget:manage`, `finance:budget:approve`

## Limitations

- Cash flow statement not implemented.
- MongoDB multi-document transactions not used; posting relies on idempotent keys and ordered writes.
- Vendor, payroll, and expense reimbursement auto-mapping awaits those modules.
- Budget “actual expenditure” tracks commitments only until expense posting integration.

## Tests

```bash
cd backend && py -m pytest tests/test_finance_staff_phase9.py -q
```