# HR Phase 6 — Payroll Processing & Payslips

## Implementation plan (reused infrastructure)

| Source | Reuse |
|--------|--------|
| Salary Structure (Phase 5) | Active `HrEmployeeSalaryAssignment` + template lines |
| Attendance (Phase 5) | `HrEmployeeAttendanceRecord` + monthly summary warnings |
| Leave (Phase 4) | Approved leave days; unpaid LOP deduction |
| Statutory config | `PayrollConfiguration.confidential_config.statutory_rates` (no hardcoded rates) |
| Finance | `DomainOutboxEvent` `finance.payroll.payment_batch_requested` |
| Employee self-service | `PayslipReference` on publish |
| Notifications | `hr.payslip.published` |

## APIs

- `/api/v1/hr/payroll/` — periods, runs, calculate, preview, transitions, payments, adjustments, reports
- `/api/v1/hr/payslips/` — generate, list, publish, revise

## Workflow states

`draft → calculating → validation_required → ready_for_review → under_review → approved → payment_processing → paid`

**Paid** only after payment reconciliation (`confirm-payment`), not on approval alone.

## Permissions (separation of duties)

`hr:payroll:read|prepare|approve|pay`, `hr:payslip:read|manage`

## Collections

As specified in Phase 6 prompt (`hr_payroll_periods`, `hr_payroll_runs`, `hr_employee_payroll_records`, etc.)

## Tests

`backend/tests/test_hr_phase6.py`

## Out of scope

Statutory Payroll & Tax Configuration module (rates are read from existing `PayrollConfiguration` only).

## Limitations

- PDF/binary document generation stores JSON payload + storage key (integrate document service for files).
- Full finance payment webhook reconciliation is via explicit `confirm-payment` API.
- Per-component proration rules use assignment proration factor + attendance warnings.