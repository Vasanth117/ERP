# Examination Cell — Phase 8 (Backend)

## Scope

- **Module 15** — examination-specific notifications (templates, deduplicated events, delivery logs, announcements) reusing `domain_outbox_events` and `communication_delivery_logs`.
- **Module 16** — analytics catalogue, live aggregations, CSV export jobs (`exam_report_jobs`).

No duplicate ERP-wide notification platform.

## Collections

| Collection | Purpose |
|------------|---------|
| `exam_notification_templates` | Tenant message templates + per-user delivery preferences (`user_id` set, `event_type=__user_preferences__`) |
| `exam_notification_events` | Idempotent notification history (`dedupe_key` unique per tenant) |
| `exam_notification_delivery_logs` | Per-channel status, retries, outbox linkage |
| `exam_announcement_records` | Cell announcements with audience targeting |
| `exam_report_jobs` | Short-lived export jobs (72h retention) |

## Permissions

- `examination:notification:read|manage|publish`
- `examination:report:read|export`
- Sensitive `incident_summary` report requires `examination:incident:investigate` or `examination:incident:manage`.

## APIs (`/api/v1/examinations/cell`)

**Notifications**
- `PUT /notifications/templates`
- `POST /notifications/send`
- `GET /notifications/history`
- `GET /notifications/events/{id}/deliveries`
- `GET|PATCH /notifications/preferences/me`
- `POST /notifications/announcements`, `POST .../publish`
- `POST /notifications/deliveries/process`

**Reports**
- `GET /reports/catalog`
- `POST /reports/{report_type}/snapshot`
- `POST /reports/exports`, `GET /reports/jobs/{id}`, `GET .../download`

## Event hooks

- `exam_cell_notification_triggers.notify_registration_confirmed` — called on confirmed registration.
- Additional triggers (`result_published`, `incident_workflow`) available for other modules.

## Tests

```bash
cd backend
py -m pytest tests/test_examination_cell_phase8.py -q
py -m pytest tests/ -k "examination_cell_phase" -q
```