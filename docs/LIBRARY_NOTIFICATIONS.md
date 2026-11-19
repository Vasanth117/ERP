# Library Notifications & Communication (Module 11)

Event-driven library messaging reusing **DomainOutboxEvent** (`library.notification.dispatch`) and **CommunicationDeliveryLog** for email channel tracking — not a separate notification platform.

## Events

`issue`, `return_reminder`, `due_upcoming`, `overdue`, `reservation_ready`, `reservation_expiry`, `fine`, `membership_expiry`, `announcement`

Hooks: circulation issue, fine assess, reservation ready (still writes `library_reservation_notifications` for compat).

## API (`/api/v1/library/notifications`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `` | Notification history |
| GET/PATCH | `/preferences/{user_id}` | Per-user library comms prefs |
| POST | `/send` | Manual message |
| POST | `/announcements` | Branch library announcement |
| POST | `/announcements/{id}/publish` | Fan-out to members |
| POST | `/batch/run` | Due/overdue/reservation/membership jobs |
| GET | `/{id}/deliveries` | Delivery status |
| POST | `/deliveries/{id}/retry` | Retry failed delivery |

Students see library items in `/api/v1/students/me/notifications` when `library_enabled` in communication preferences.

## Collections

- `library_notifications` (dedupe key)
- `library_notification_deliveries`
- `library_notification_preferences`
- `library_announcements`

## Permissions

`library:notification:read|manage|publish|run` (college admin all; librarian read/manage/run).

## Tests

```bash
cd backend; py -m pytest tests/test_library_notifications.py -q
```