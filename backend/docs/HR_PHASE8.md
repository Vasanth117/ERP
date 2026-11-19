# HR Phase 8 — Benefits & Claims + Performance & Training

## Scope

- **Module 1:** Benefit programs, eligibility, enrollment, claims workflow, finance payment handoff, dashboard and reports.
- **Module 2:** Performance cycles, goals, self/manager/HR review flow, PIPs, development plans; training programs, enrollment, attendance, assessment, certification.
- **Not in scope:** HR Notifications module, HR Reports module (dedicated), legacy `employee_benefit_records` / `employee_performance_records` in college admin (unchanged).

## Reuse

| Integration | Pattern |
|-------------|---------|
| Finance | `DomainOutboxEvent` `finance.benefit.claim_payment_requested` |
| Payment confirm | `hr:benefits:pay` — claim → `paid` only after `payment_reference` |
| Employee access | `/benefits/self/*`, `/performance/self/*`, `/training/self/*`, `GET /self-service/benefits` |
| Notifications | `enqueue_hr_notification` on enrollment/claim review |
| Eligibility | `EmployeeRecord` + `HrEmployeeProfile` + program rules |

## API prefixes

- `/api/v1/hr/benefits/`
- `/api/v1/hr/performance/`
- `/api/v1/hr/training/`

## Permissions

`hr:benefits:read|manage|approve|pay`, `hr:performance:read|manage|review`, `hr:training:read|manage` on **HR_STAFF**.

## Collections

As specified in Phase 8 prompt (`hr_benefit_programs`, `employee_benefit_enrollments`, `employee_benefit_claims`, `hr_performance_cycles`, `employee_performance_goals`, `hr_training_programs`, etc.).

## Tests

```bash
cd backend
py -m pytest tests/test_hr_phase8.py -q
```

## Limitations

1. Multi-level claim approval is modeled as staged reviews in `employee_benefit_claim_reviews` with a single HR approve step in this phase.
2. Performance rating calculation is weighted-score average, not full calibration tooling.
3. Training certificates are metadata codes only (no PDF pipeline).
4. Benefit enrollment renewal/suspension rules are stored on programs but automated renewal jobs are not implemented.
5. Manager-only routes still require HR review permission unless `HR_PERFORMANCE_MANAGE` is granted (manager identity checked when `manager_user_id` is set).