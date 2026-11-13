# College Admin Phase 6

HR administration (module 11) and library administration (module 12).

Base path: `/api/v1/college-admin`

## HR administration

Prefix: `/hr-administration`

| Endpoint | Description |
|---|---|
| `PUT /policies`, `POST /policies/{code}/publish` | `hr_policies` |
| `POST /recruitment` | `recruitment_records` |
| `POST /onboarding`, `POST /onboarding/{user_id}/complete` | Onboarding workflow |
| `POST /offboarding` | Offboarding + employee status update |
| `PUT /leave-policies`, `GET /leave/pending`, `POST /leave/decide` | Policies + `leave_requests` + `employee_leave_approvals` |
| `PUT /payroll/configuration`, `GET /payroll/status` | `payroll_configuration` (confidential bands not exposed) |
| `GET /statistics`, `GET /reports/summary` | Workforce KPIs |

Reuses `employee_records`, `leave_requests`, `payslip_references`, `employee_profile_snapshots`. Payroll **payments** remain in Finance modules.

Permissions: `college:hr:read`, `manage`, `leave_approve`, `payroll_config`.

## Library administration

Prefix: `/library-administration`

| Endpoint | Description |
|---|---|
| `POST /branches` | `library_branches` |
| `POST /catalogue`, `POST /copies` | Syncs `library_catalog_items` + `library_copies`; admin accession in `library_book_copies` |
| `PUT /borrowing-policies`, `POST /membership` | Policies and eligibility |
| `POST /circulation/issue`, `/return`, `GET /circulation` | Authoritative `library_circulations` + audit `library_circulation_records` |
| `POST /reservations/fulfill` | `library_reservations` |
| `POST /fines/decide` | `library_fines` |
| `POST /acquisitions`, `/digital-resources` | Acquisitions + `library_digital_resources` |
| `GET /reports/summary` | Branch-aware inventory/circulation report |

Permissions: `college:library:read`, `manage` (branch validated when `branch_code` supplied).

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase6.py tests/test_college_admin_phase1.py … phase5.py -q --disable-warnings
```
