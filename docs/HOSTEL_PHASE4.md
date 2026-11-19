# Hostel Admin Phase 4

Mess management & billing (HA 06) and leave/outpass (HA 08). Follows `backend_and_frontend.md`.

## APIs (`/api/v1/hostel`)

### Mess

| Method | Path |
|--------|------|
| PUT | `/me/mess/facilities`, `/me/mess/plans`, `/me/mess/meal-categories`, `/me/mess/menus` |
| GET | `/me/mess/facilities`, `/me/mess/plans` |
| POST | `/me/mess/enrollments`, `/me/mess/enrollments/decide`, `/me/mess/attendance` |
| GET | `/me/mess/enrollments`, `/me/mess/reports/enrollment` |
| POST | `/me/mess/billing/periods`, `/me/mess/billing/calculate`, `/me/mess/billing/send-finance`, `/me/mess/billing/sync-payments/{period_id}`, `/me/mess/billing/adjustments` |
| POST | `/me/mess/billing/records/{record_id}/approve` |

Permissions: `hostel:mess:read` / `hostel:mess:manage`.

### Leave & outpass

| Method | Path |
|--------|------|
| GET | `/me/leave-outpass/overview`, `/me/leave/requests`, `/me/outpass/requests` |
| PUT | `/me/leave/types` |
| POST | `/me/leave-outpass/review`, `/me/leave-outpass/gate` |

Permissions: `hostel:leave:read` / `hostel:leave:manage` / `hostel:gate:manage`.

### Student portal

| Method | Path |
|--------|------|
| POST | `/api/v1/students/me/hostel/leave`, `/api/v1/students/me/hostel/outpass` |

## Collections

See `mess_models.py` and `leave_outpass_models.py`. Reuses `hostel_mess_plans` and `hostel_outpass_requests` (extended schemas).

Finance handoff creates `StudentFeeDemand` rows only; payment truth is synced from Finance via demand status.

## Tests

```bash
cd backend
py -m pytest tests/test_hostel_phase4.py -q
```

## Limitations

- Parent/guardian approval workflow is flag-only (`parent_approval_required` on leave types).
- Meal schedule special calendars and QR attendance integrations are stubbed via `capture_method`.
- No duplicate invoices; hostel billing records reference finance demands only.
- Maintenance, complaints and incidents remain out of scope.