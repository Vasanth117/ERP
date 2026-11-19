# College Admin Phase 12

Institutional Finance Extensions (22) and Institutional Operations Extensions (23).

## Gap analysis

| Area | Core module | Phase 12 extensions |
|------|-------------|---------------------|
| Student fees, demands, payments, refunds, ledger | `finance_admin_*` | **Out of scope** — not duplicated |
| Fee periods, assessments, reconciliation | `finance_admin_*` | **Out of scope** |
| Institutional budgets & department allocations | — | `finance_ext_*` |
| Institutional expenses & approvals | `FinancialApprovalRecord` | `institution_expense_records` + workflow `finance_approval` |
| Vendors, PR/PO, invoices (institutional) | — | `institution_*` procurement collections |
| Campus assets, maintenance, inventory, facilities | — | `operations_ext_*` |
| Student/hostel/library operational modules | respective modules | Read-only integration hooks via shared tenant scope |

## Finance API (`/api/v1/college-admin/finance-extensions`)

- `PUT /budgets` — upsert institutional budget (periods, totals)
- `GET /budgets/{budget_id}/utilization`
- `PUT /budgets/allocations` — department allocation
- `POST /expenses`, `POST /expenses/{id}/approve`
- `PUT /vendors`, `POST /purchase-requests`, approve, `POST /purchase-orders`, `POST /vendor-invoices`
- `GET /budgets/{budget_id}/report`

**Permissions:** `college:finance_ext:read`, `manage`, `approve`, `budget`

**Collections:** `institution_budgets`, `department_budget_allocations`, `institution_budget_transactions`, `institution_expense_records`, `institution_vendor_records`, `institution_purchase_requests`, `institution_purchase_orders`, `institution_vendor_invoices`

## Operations API (`/api/v1/college-admin/operations-extensions`)

- Assets, allocations, facilities, maintenance (+ assign), inventory, stock movements, service contracts, incidents, `GET /reports/summary`

**Permissions:** `college:operations_ext:read`, `manage`, `maintenance`, `inventory`

**Collections:** `institution_asset_records`, `institution_asset_allocations`, `institution_facilities`, `institution_maintenance_requests`, `institution_inventory_items`, `institution_stock_movements`, `institution_service_contracts`, `institution_operational_incidents`, `institution_operations_history`

## Security & audit

- Tenant-scoped queries on all documents; closed budgets cannot be modified.
- Separate permissions for budget edit, expense/PR create vs approve, inventory vs maintenance.
- `append_institution_audit` on sensitive finance/ops actions; `FinancialApprovalRecord` for expense and procurement approvals.

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase1.py … tests/test_college_admin_phase12.py -q
```