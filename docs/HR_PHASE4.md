# HR Phase 4 — Employment Changes, Offboarding, Leave

Aligned with `backend_and_frontend.md`: thin routers, tenant-scoped services, audited balances, domain outbox for notifications/payroll/identity.

## API map (`/api/v1/hr/`)

| Area | Prefix | Highlights |
|------|--------|------------|
| Employment | `employment-changes/` | Overview KPIs, detail (current vs proposed), multi-step approval, scheduled apply, probation approaching, contracts + expiry reminders |
| Offboarding | `offboarding/` | Resignation workflow, notice waiver/extension, checklist, exit interview, final separation |
| Leave | `leave/` | Types, policies, applications, manager→HR approval, balances, adjustments, reports |

## Requirement trace (Modules 7 & 8)

| Spec item | Backend |
|-----------|---------|
| Employment workspace KPIs | `GET employment-changes/overview` |
| Change comparison & documents | `GET employment-changes/{id}` |
| Approval ladder | `manager_approve` → `hr_validate` → `approve` (management) |
| Probation (no auto-confirm) | Reviews + `probation-reviews/{id}/decide` |
| Contract expiry reminders | `POST employment-changes/contracts/reminders` |
| Resignation + notice | Resignation APIs + `notice-period` updates |
| Offboarding clearances | Template tasks + completion gate |
| Payroll settlement | Outbox `hr.payroll.final_settlement_requested` only |
| Leave calendar duration | `leave_working_days` + academic calendar holidays |
| Leave reports | `GET leave/reports` |

## Permissions (HR_STAFF)

`hr:employment:*`, `hr:offboarding:*`, `hr:leave:read|manage`, legacy `hr:leave:review` on dashboard.

## Tests

`backend/tests/test_hr_phase4.py`