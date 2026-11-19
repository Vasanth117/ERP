# Finance Staff — Phase 5 (Scholarships + Concessions)

Aligned with `backend_and_frontend.md`. Extends authoritative `scholarship_programs`, `official_scholarship_applications`, and `fee_concessions`; financial impact flows through `financial_aid_posting` → idempotent ledger credits (Phase 4).

## Collections

| Collection | Purpose |
|------------|---------|
| `scholarship_programs` | Extended programme metadata (codes, funding, eligibility, windows) |
| `scholarship_eligibility_rules` | Configurable rule rows per programme |
| `official_scholarship_applications` | Extended workflow fields + documents |
| `scholarship_application_reviews` | Reviewer recommendations |
| `student_scholarship_awards` | Approved/active awards |
| `scholarship_award_history` | Award lifecycle audit |
| `scholarship_funding_allocations` | Budget / committed / remaining |
| `scholarship_renewal_records` | Renewal decisions |
| `fee_concession_categories` | Concession type catalog |
| `fee_concession_policies` | Policy + stacking rules |
| `student_fee_concession_applications` | Concession requests |
| `student_fee_concession_awards` | Approved concessions |
| `student_fee_waivers` | Full/partial waivers |
| `fee_concession_approval_history` | Approval trail |
| `fee_concession_adjustment_history` | Ledger linkage |
| `fee_concessions` | Legacy published rows (dashboard + assessment compat) |

## APIs (`/api/v1/accounts-finance`)

### Scholarships (`/scholarships`)

- Programmes CRUD-lite (`POST /programs`, `GET /programs`)
- Eligibility rules (`POST /programs/{id}/rules`)
- Eligibility check (`GET /programs/{id}/eligibility`)
- Applications (`GET /applications`, review/approve/reject)
- Staff-recorded awards (`POST /awards/staff-recorded`)
- Funding (`POST|GET /programs/{id}/funding`)
- Renewals (`POST /awards/{id}/renewals`, `POST /renewals/{id}/decide`)
- Aid statement (`GET /students/{id}/aid-statement`)

### Concessions (`/concessions`)

- Categories & policies
- Applications submit/approve/reject
- Waivers (`POST /waivers`)
- Award revocation (`POST /awards/{id}/revoke`)

## RBAC

- `finance:scholarship:read|manage|approve`
- `finance:concession:read|manage|approve`

## Integration

- Student portal still uses `ScholarshipProgram.programme_id` + `OfficialScholarshipApplication`
- Fee assessment `_financial_aid()` reads active `StudentScholarshipAward` + `StudentFeeConcessionAward`
- Approved aid posts `scholarship_credit`, `concession_credit`, or `fee_waiver` ledger entries
- Invoice/demand amounts reduced when `invoice_id` is supplied (no silent ledger edits)

## Tests

`backend/tests/test_finance_staff_phase5.py`

## Limitations

- Multi-step approval hierarchies stored but not fully orchestrated (single finance approve step)
- Document verification is reference-token based; no new document store
- Revocation does not auto-post ledger reversal (requires Phase 4 adjustment workflow)
- GPA/attendance rules require configured `scholarship_eligibility_rules` + published eligibility rows
- Installments, late fees, refunds not in scope (Phase 5 only)