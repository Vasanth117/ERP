# Finance Staff — Phase 12 (Settings, Permissions & Audit)

Aligned with `backend_and_frontend.md`. Reuses **central RBAC** (`Permission`, `Role.FINANCE_STAFF`) and **institution audit** (`institution_audit_logs` via `append_institution_audit`). Does **not** store payment gateway secrets in settings documents.

## Finance settings (versioned)

| Collection | Purpose |
|------------|---------|
| `finance_general_settings` | Versioned general/fee/scholarship/installment/refund/accounting/budget/tax/reporting domains |
| `finance_payment_settings` | Payment policy versions (no credentials) |
| `finance_receipt_settings` | Receipt numbering / publication policy |
| `finance_fee_settings` | Reserved collection for fee-domain splits (optional; general collection used by API) |
| `finance_setting_history` | Status transitions (draft → review → approved → active) |
| `finance_approval_workflows` / `finance_approval_workflow_versions` | Configurable approval stages |
| `finance_access_assignments` | Campus/department/cost-centre scope (complements RBAC) |
| `finance_temporary_access_grants` | Time-bound extra permissions |
| `finance_access_review_history` | Access change trail |

APIs: `/accounts-finance/settings/*` — dashboard, active domain payload, version workflow, workflows, access assignments, temporary grants.

Statuses: `draft`, `under_review`, `approved`, `active`, `superseded` (see `FinanceSettingStatus`).

## Audit & transaction history

| Source | Purpose |
|--------|---------|
| `institution_audit_logs` | Searchable finance audit (`module=accounts_finance`) |
| `student_invoice_history`, `student_ledger_posting_history`, … | Module-native histories (not duplicated) |
| `finance_transaction_relationships` | Cross-module trace index |
| `finance_audit_export_history` | Export audit |

APIs: `/accounts-finance/audit/*` — dashboard, search, trace `{root_type}/{root_id}`, CSV export.

## Permissions

- `finance:settings:read`, `finance:settings:manage`, `finance:settings:approve`
- `finance:audit:read`, `finance:audit:export`, `finance:audit:investigate`

## Limitations

- Approval workflows stored as configuration; runtime enforcement remains in source modules (refunds, journals, etc.).
- `assert_finance_scope()` is a stub — campus/department enforcement requires callers to consult `finance_access_assignments`.
- Full transaction search across amount/student/vendor uses module APIs; audit search filters institution logs only.
- Separation-of-duties on self-approval not globally enforced in Phase 12 (workflow rules are declarative).

## Tests

```bash
cd backend && py -m pytest tests/test_finance_staff_phase12.py -q
```