# HR Phase 5 — Attendance & Work Schedules + Salary Structure

## API prefixes

| Module | Prefix |
|--------|--------|
| Attendance & schedules | `/api/v1/hr/attendance/` |
| Salary structure | `/api/v1/hr/salary/` |

## MongoDB collections

`hr_work_schedules`, `hr_shifts`, `employee_roster_assignments`, `employee_attendance_events`, `employee_attendance_records`, `employee_attendance_corrections` (extended), `employee_attendance_monthly_summaries`, `hr_salary_components`, `hr_salary_templates`, `employee_salary_assignments`, `employee_salary_revision_history`, `hr_shift_swap_requests`

## Integrations

- Leave → approved leave marks `ON_LEAVE` in day processing
- Academic calendar → institution holidays
- Legacy `employee_day_attendance` synced for dashboard compatibility
- Salary assignment snapshot → `EmployeeRecord.confidential_hr.salary_structure` (no payroll run)
- Statutory refs on components only (no rate hardcoding)

## Permissions

`hr:attendance:read|manage`, `hr:salary:read|manage`

## Tests

`backend/tests/test_hr_phase5.py`

## Out of scope (per spec)

Payroll processing, payslips, statutory tax configuration