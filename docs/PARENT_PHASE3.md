# Parent / Guardian Portal — Phase 3

Examinations, results, timetable & academic calendar; fees, payments, scholarships, receipts and finance enquiries.

Aligned with `backend_and_frontend.md`. Authoritative examination and finance data remain in Examination Cell and Finance modules — the parent layer only reads published/authorized views and initiates payments into existing `PaymentTransaction` records.

## API prefix

`/api/v1/parents/me/students/{student_user_id}/*`

### Module 1 — Examinations & calendar

| Method | Path | Permission | Relationship data |
|--------|------|------------|-------------------|
| GET | `.../examinations/overview` | `parent:exam:read` | `view_exam_timetable` |
| GET | `.../examinations/timetable` | `parent:exam:read` | `view_exam_timetable` |
| GET | `.../examinations/notifications` | `parent:exam:read` | `view_exam_timetable` |
| GET | `.../examinations/results/{season_id}` | `parent:exam:read` | `view_results` (published only) |
| GET | `.../examinations/results` | `parent:exam:read` | `view_results` |
| GET | `.../examinations/result-status` | `parent:exam:read` | `view_results` |
| GET | `.../examinations/hall-ticket/{season_id}/availability` | `parent:exam:read` | `view_hall_ticket` (default off) |
| POST | `.../examinations/hall-ticket/{season_id}/download` | `parent:exam:read` | `view_hall_ticket` |
| GET | `.../examinations/reviews` | `parent:exam:read` | `view_results` |
| GET | `.../examinations/calendar` | `parent:exam:read` | `view_exam_timetable` |

Integrated readers: `semester_examination_reader`, `examination_results_reader`, `examination_registration_reader`, `AcademicCalendarEvent`.

### Module 2 — Finance

| Method | Path | Permission | Relationship data |
|--------|------|------------|-------------------|
| GET | `.../finance/dashboard` | `parent:finance:read` | `view_fees` |
| GET | `.../finance/statement` | `parent:finance:read` | `view_fees` |
| GET | `.../finance/installments` | `parent:finance:read` | `view_fees` |
| GET | `.../finance/scholarships` | `parent:finance:read` | `view_fees` |
| GET | `.../finance/receipts` | `parent:finance:read` | `view_receipts` |
| GET | `.../finance/payments` | `parent:finance:read` | `view_fees` |
| POST | `.../finance/payments/initiate` | `parent:finance:pay` | `pay_fees` |
| GET | `.../finance/payments/{transaction_id}` | `parent:finance:read` | `view_fees` |
| POST | `.../finance/enquiries` | `parent:finance:enquiry` | `view_fees` |
| GET | `.../finance/enquiries` | `parent:finance:read` | `view_fees` |

Payment initiation creates authoritative `payment_transactions` plus parent audit collections (`parent_payment_initiation_records`, `parent_payment_transaction_references`). Status treats gateway success without webhook verification as pending.

### College admin — finance enquiries

| Method | Path |
|--------|------|
| GET | `/college-admin/parent-administration/finance-enquiries` |
| POST | `/college-admin/parent-administration/finance-enquiries/{id}/respond` |

## MongoDB collections (parent-only)

| Collection | Purpose |
|------------|---------|
| `parent_exam_notifications` | Synced exam/academic notices for the parent portal |
| `parent_exam_document_access_history` | Hall ticket download audit |
| `parent_payment_initiation_records` | Who initiated payment, idempotency |
| `parent_payment_transaction_references` | Parent-scoped payment lookup |
| `parent_finance_enquiries` | Payment/refund/receipt enquiries |
| `parent_finance_enquiry_history` | Enquiry status trail |

## Key services

- `examination_portal_service.py`
- `finance_portal_service.py`

## Tests

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_parent_phase3.py -rs -q
```

## Limitations / not in Phase 3

- Live payment gateway webhooks (reuse Finance reconciliation when configured).
- Parent scholarship application uploads (read-only eligibility unless Scholarship module exposes parent workflow).
- Push notification delivery for exam notices (records sync on read).
- Communication, documents, meetings parent modules (later phases).

## Stop boundary

Phase 3 only. Do not implement Communication, Documents, or Parent Meetings until approved.