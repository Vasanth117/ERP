# Finance Staff — Phase 2 (Assessment + Invoices)

Aligned with `backend_and_frontend.md`. Reuses `student_records`, enrollments, active `fee_structures`, `fee_concessions`, and authoritative `student_fee_demands` / `student_fee_invoices` / `student_financial_ledger` — no duplicate student or enrollment rows.

## APIs (`/api/v1/accounts-finance`)

### Assessments

| Method | Path | Permission |
|--------|------|------------|
| POST | `/assessments/preview` | `finance:assessment:manage` |
| POST | `/assessments` | `finance:assessment:manage` |
| POST | `/assessments/bulk` | `finance:assessment:manage` |
| GET | `/assessments` | `finance:assessment:read` |
| GET | `/assessments/{id}` | `finance:assessment:read` |
| POST | `/assessments/{id}/transitions` | manage / `finance:assessment:approve` |

Workflow: `draft` → `in_review` → `approved` | `returned` | `cancelled`. Posted legacy college-admin assessments remain `posted`.

### Invoices

| Method | Path | Permission |
|--------|------|------------|
| POST | `/invoices/preview` | `finance:invoice:manage` |
| POST | `/invoices/generate` | `finance:invoice:manage` |
| GET | `/invoices` | `finance:invoice:read` |
| GET | `/invoices/{id}` | `finance:invoice:read` |
| POST | `/invoices/{id}/issue` | `finance:invoice:issue` |
| POST | `/invoices/{id}/adjustments` | `finance:invoice:issue` |

Draft invoices become **issued** with atomic `finance_invoice_sequences` numbering. Issue posts ledger debit and enqueues `finance.invoice.issued` outbox (student/parent notify).

Payment display status is derived from demands + **verified** payments only (offline success or webhook-verified online).

## Collections

| Collection | Purpose |
|------------|---------|
| `student_fee_assessments` | Extended workflow fields on authoritative assessment |
| `student_fee_assessment_items` | Itemized components |
| `student_fee_assessment_history` | Workflow trail |
| `student_fee_assessment_exceptions` | Bulk preview/processing exceptions |
| `student_fee_invoices` | Extended invoice header (`invoice_number`, `invoice_status`, items via join) |
| `student_invoice_items` | Line items (immutable after issue; adjustments via credit/debit notes) |
| `student_invoice_history` | Issue/adjustment trail |
| `student_fee_demands` | Authoritative demands (reused) |
| `student_credit_notes` / `student_debit_notes` | Corrections |
| `invoice_adjustment_history` | Adjustment audit |
| `finance_invoice_sequences` | Per-tenant invoice numbers |

## Limitations (Phase 2)

- No online/offline payment capture APIs (read-only payment status sync).
- Scholarship monetary reduction uses concessions; approved scholarship apps without award amounts do not reduce net (count-only until award amounts exist).
- Revised invoice document type deferred; use credit/debit notes.

## Tests

```bash
cd backend
py -m pytest tests/test_finance_staff_phase2.py tests/test_finance_staff_phase1.py -q --disable-warnings
```