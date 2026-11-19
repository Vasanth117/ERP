# HR Phase 7 — Statutory Payroll & Tax + Employee Self-Service

## Scope

- Module 1: Statutory component configuration, financial years, tax regimes/slabs, employee tax profiles, declaration workflow, proof verification, compliance report, payroll integration.
- Module 2: Employee self-service workspace (profile, documents, attendance, leave, salary/payslips, tax, requests, employment, onboarding stub, benefits stub, notifications).
- **Not implemented:** Benefits & Claims (stub only).

## Implementation plan (reuse)

| Area | Reuse |
|------|--------|
| Payroll statutory rates | `resolve_statutory_rates_for_employee` + legacy `PayrollConfiguration.confidential_config.statutory_rates` fallback |
| Payslip access | `HrEmployeePayslip` + `get_payslip_for_employee_self` |
| Profile correction | `submit_profile_correction` |
| Leave application | Same balance rules as HR leave module |
| Notifications | `DomainOutboxEvent` (`hr.*` events) |

## APIs

| Prefix | Audience |
|--------|----------|
| `/api/v1/hr/statutory-tax/` | HR staff (`hr_staff_user`) |
| `/api/v1/hr/self-service/` | Employees (`employee_self_user`, `FACULTY_SELF_SERVICE_*` or `hr:self:access`) |

### Statutory / tax (HR)

- Components, rule versions, financial years, regimes, slabs
- Employee tax profiles
- Declarations: draft, submit, review, proofs, proof review
- `GET /compliance-report`

### Self-service (employee)

- `GET/POST` profile, documents, attendance, leave, salary, payslips, tax declarations, requests, employment, onboarding, notifications
- `GET /benefits` → phase stub

## Collections

`hr_statutory_components`, `hr_statutory_rule_versions`, `hr_tax_financial_years`, `hr_tax_regime_configurations`, `hr_tax_slabs`, `employee_tax_profiles`, `employee_tax_declarations`, `employee_tax_proofs`, `employee_tax_review_history`, `employee_self_service_requests`, `employee_self_service_request_history`

## Permissions

- `hr:statutory:read`, `hr:statutory:manage`
- `hr:tax:read`, `hr:tax:manage`, `hr:tax:review`
- Employee access: `faculty:self_service:read|manage` or `hr:self:access`

## Payroll integration

`calculate_payroll_run` resolves per-employee statutory rules effective on period end date, merges warnings, and stores rule references in `input_snapshot.statutory_rule_refs`.

**Finalized payroll runs are not altered** when configuration changes later.

## Tests

```bash
cd backend && pytest tests/test_hr_phase7.py -q
```

## Limitations

1. TDS estimate uses configured slabs with simplified annualization; not a full statutory engine.
2. Tax proof upload uses metadata refs only (no dedicated storage pipeline in this phase).
3. Benefits & Claims not integrated (stub response).
4. Self-service document upload routes reuse HR document APIs only where employee has access; bulk mandatory checklist for self-service is minimal (listed documents only).
5. `list_tax_financial_years` requires `hr:tax:manage` (HR admin path).