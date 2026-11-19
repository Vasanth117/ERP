# Finance Staff — Phase 11 (Tax & Notifications)

Aligned with `backend_and_frontend.md`. Tax rates come from authoritative `hr_statutory_rule_versions` via `finance_tax_config_references` — **no hardcoded statutory rates** in finance logic. Notifications use existing `domain_outbox_events` (`finance.notification.dispatch`) plus finance-local delivery tracking.

## Tax & Regulatory

| Collection | Purpose |
|------------|---------|
| `finance_tax_config_references` | Map transaction types → HR `component_code` |
| `finance_tax_transaction_records` | Idempotent tax register (`posting_key`) |
| `finance_tax_adjustments` | Approved corrections (original rows preserved) |
| `finance_regulatory_reports` / `finance_regulatory_report_versions` | Period summaries + snapshots |
| `finance_regulatory_filing_history` | **Filing recorded only with `external_acknowledgment`** |
| `finance_tax_exceptions` | Compliance gaps |

APIs: `/accounts-finance/tax/*` — overview, config, sync, register export, adjustments, regulatory report workflow, filing record.

Vendor invoice verification auto-captures indirect tax when `tax_amount` > 0.

## Notifications & Reminders

| Collection | Purpose |
|------------|---------|
| `finance_reminder_policies` | Schedules, templates, channels |
| `finance_scheduled_reminders` | Last/next run audit |
| `finance_notification_events` / `history` / `failures` | Finance dashboard |
| `finance_notification_escalations` | Overdue fee escalations |

APIs: `/accounts-finance/notifications/*` — dashboard, reminder policies, `POST .../reminders/run-fee-due`.

Existing `finance_notify.py` (invoice/receipt/installment/late fee) **unchanged** — continues to enqueue domain events.

Duplicate prevention: unique `dedupe_key` on `finance_notification_events` and outbox idempotency keys.

## Permissions

- `finance:tax:read`, `finance:tax:manage`, `finance:tax:approve`
- `finance:notify:read`, `finance:notify:manage`

## Limitations

- No government portal e-filing integration.
- PDF export for regulatory returns not implemented (JSON register only).
- SMS/push delivery depends on central outbox worker (not in Phase 11).
- Parent recipient resolution reuses outbox payload flags; full audience preview API minimal.

## Tests

```bash
cd backend && py -m pytest tests/test_finance_staff_phase11.py -q
```