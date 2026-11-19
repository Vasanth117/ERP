# HR Phase 9 — Notifications & Communication + Reports & Analytics

## Scope

- **Module 1:** HR notification dashboard, templates, announcements, audience resolution/preview, broadcast, delivery history, employee inbox (read/ack), preferences; integrates with `DomainOutboxEvent` for non–in-app channels.
- **Module 2:** Analytics dashboard, report catalog, run/preview, CSV export, saved reports, scheduled reports (manual execute), field permission checks per report.
- **Not in scope:** HR Settings & Policies, dedicated Audit History & Access Management module.

## Reuse

| Layer | Reuse |
|-------|--------|
| Event delivery | Existing `DomainOutboxEvent` + `enqueue_hr_notification` pattern from Phases 3–8 |
| Analytics slices | `HrDashboardRepository`, module aggregates (leave/payroll/benefits data read-only) |
| Exports | `department_admin.csv_safe` (formula-safe CSV base64) |
| Institution reports | Legacy `InstitutionReport*` collections untouched; HR uses `hr_saved_reports` / `hr_scheduled_reports` |

## APIs

| Prefix | Highlights |
|--------|------------|
| `/api/v1/hr/communications/` | Dashboard, templates, audience preview, announcements, broadcast, history, inbox, preferences |
| `/api/v1/hr/reports/` | Analytics dashboard, catalog, run, export/download, saved, scheduled execute |

## Collections

- `hr_notification_templates`
- `hr_announcements`
- `hr_announcement_audience`
- `hr_notification_preferences`
- `hr_notification_delivery_history`
- `hr_saved_reports`
- `hr_scheduled_reports`
- `hr_report_execution_history`

## Permissions (HR_STAFF)

`hr:notify:read|manage`, `hr:reports:read|manage|export`  
Per-report access also requires underlying module read permission (e.g. payroll report → `hr:payroll:read`).

## Delivery semantics

- **In-app:** marked `delivered` immediately in `hr_notification_delivery_history`.
- **Email/SMS/push:** queued as `sent` on outbox creation; **not** marked `delivered` without provider confirmation (future worker).
- **Dedupe:** unique `dedupe_key` per recipient/channel/message.

## Tests

```bash
cd backend
py -m pytest tests/test_hr_phase9.py -q
```

## Limitations

1. Reminder/escalation jobs not implemented (schema-ready via templates/categories).
2. PDF/XLSX export returns validation error; CSV only in this phase.
3. Scheduled reports: `next_run_at` set but no background cron — use `POST .../scheduled/{id}/execute`.
4. Automatic sync from legacy `enqueue_hr_notification` into delivery history not wired (domain events remain in outbox).
5. SMS/push provider delivery confirmation not implemented.