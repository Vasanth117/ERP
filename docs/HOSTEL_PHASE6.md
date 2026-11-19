# Hostel Admin Phase 6

Communication & notifications (HA 11) and reports & analytics (HA 12). Follows `backend_and_frontend.md`.

## Reuse

- **Delivery:** `DomainOutboxEvent` for email/SMS/push (non–in-app channels).
- **In-app:** `hostel_notification_delivery_history` per recipient with dedupe keys.
- **Operational events:** `notify_hostel_student` also records in-app delivery rows.
- **Reports:** Live aggregation from existing hostel collections (no duplicate operational stores).

## APIs (`/api/v1/hostel`)

### Communication

| Method | Path |
|--------|------|
| GET | `/me/notifications/dashboard` |
| POST | `/me/notifications/audience/preview` |
| PUT/GET | `/me/notifications/templates` |
| POST | `/me/announcements`, `/me/announcements/{code}/transition` |
| POST | `/me/notifications/reminders/scan` |

Permissions: `hostel:notify:read` / `hostel:notify:manage`.

### Reports

| Method | Path |
|--------|------|
| GET | `/me/reports/catalog`, `/me/analytics/overview` |
| POST | `/me/reports/run`, `/me/reports/export` |
| PUT | `/me/reports/saved`, `/me/reports/schedules` |
| POST | `/me/reports/schedules/{code}/execute` |

Permissions: `hostel:reports:read`, `hostel:reports:export`, `hostel:reports:manage`.

### Student portal

| Method | Path |
|--------|------|
| GET | `/me/hostel/notifications` |
| POST | `/me/hostel/notifications/{id}/read`, `/me/hostel/notifications/acknowledge` |

## Collections

- `hostel_announcements`, `hostel_notification_templates`, `hostel_announcement_audience`, `hostel_announcement_acknowledgements`, `hostel_notification_delivery_history`
- `hostel_saved_reports`, `hostel_scheduled_reports`, `hostel_report_execution_history`

## Tests

```bash
cd backend
py -m pytest tests/test_hostel_phase6.py -q
```

## Limitations

- PDF export returns 501 (CSV/Excel-style via base64 CSV).
- No separate worker for scheduled reports (manual `execute` endpoint).
- Full custom field picker is saved-report metadata only; export uses report runner columns.
- Integrations and audit configuration modules explicitly out of scope.