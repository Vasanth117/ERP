# Finance Staff — Phase 8 (Reports & Period Closing)

Aligned with `backend_and_frontend.md`. Aggregations read authoritative student finance, payment, scholarship, refund, and reconciliation collections only — no duplicate ledgers. Accounting GL reports return `available: false` until a General Ledger module exists.

## Module 1 — Financial Reports & Analytics

- **Workspace:** `GET /accounts-finance/reports/workspace` — dashboard metrics plus net operating position (collections minus institution expenses; not GL).
- **Categories:** `GET /accounts-finance/reports/categories`
- **Preview:** `POST /accounts-finance/reports/preview` with `{ category, filters }`
- **Saved reports:** `POST/GET /accounts-finance/reports/saved`, `POST .../saved/{id}/run`
- **Export:** `POST /accounts-finance/reports/export/csv` (same RBAC as preview + `finance:report:export`)

Collections: `finance_saved_reports`, `finance_scheduled_reports`, `finance_report_execution_history`.

## Module 2 — Financial Period Closing

- **Financial years:** `POST /accounts-finance/periods/years`
- **Accounting periods:** `PUT/GET /accounts-finance/periods` (extends `financial_periods` with lifecycle metadata separate from academic years)
- **Closing workflow:** `POST /accounts-finance/periods/{code}/closing-runs` → pre-closing checks → `POST .../closing-runs/{id}/approve`
- **Reopening:** `POST .../reopen-requests` → `POST .../reopen-requests/{id}/approve` (preserves prior closing summary; requires re-close)

Collections: `financial_years`, `financial_period_closing_runs`, `financial_period_closing_checks`, `financial_period_closing_summaries`, `financial_period_reopening_requests`, `financial_period_status_history`.

**Period lock:** `period_lock_service.assert_period_open_for_date` enforced on refund requests and invoice issue; closed/locked periods block backdated mutations.

## Permissions

- `finance:report:read`, `finance:report:manage`, `finance:report:export`
- `finance:period:read`, `finance:period:manage`, `finance:period:close`, `finance:period:reopen_approve`

## Limitations

- XLSX/PDF export not implemented (CSV only).
- Trial balance, income statement, balance sheet, journal register require future GL.
- Year-end income/expense closure and retained-earnings transfer not implemented without GL.
- Pre-closing checks are read-only scans; blocking severity is informational until approval policy is configured.

## Tests

```bash
cd backend && py -m pytest tests/test_finance_staff_phase8.py -q
```