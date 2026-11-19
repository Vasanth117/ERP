# Hostel Admin Phase 3

Resident management & check-in/out (HA 05) and visitor management (HA 07). Follows `backend_and_frontend.md`.

## APIs (`/api/v1/hostel`)

### Residents

| Method | Path |
|--------|------|
| GET | `/me/residents`, `/me/residents/awaiting-checkin`, `/me/residents/{resident_id}` |
| POST | `/me/residents/check-in`, `/me/residents/check-out`, `/me/residents/no-show` |

Permissions: `hostel:resident:read` / `hostel:resident:manage` (college `hostel:*` also accepted).

### Visitors

| Method | Path |
|--------|------|
| POST | `/me/visitors`, `/approve`, `/entry`, `/exit`, `/deny` |
| GET | `/me/visitors`, `/me/visitors/inside`, `/me/visitors/reports/daily` |
| PUT | `/me/visitors/restrictions` |

Permissions: `hostel:visitor:read` / `hostel:visitor:manage`.

## Collections (new)

- `hostel_residents`, `hostel_resident_status_history`, `hostel_resident_checkin_records`, `hostel_resident_checkout_records`, `hostel_resident_transfer_history`
- `hostel_visitor_entries`, `hostel_visitor_approvals`, `hostel_visitor_restrictions`, `hostel_visitor_profiles`, `hostel_visitor_activity_history`

Reuses: `hostel_allocations`, `hostel_beds`, `hostel_room_allocations`, `hostel_visitor_logs` (legacy sync on entry).

## Resident flow

1. Confirmed allocation → auto `hostel_residents` row (`awaiting_checkin`) via allocation service.
2. Check-in → resident `checked_in`, allocation `active`, bed allocated, student `hostel_room_allocations` published.
3. Check-out → resident `checked_out`, allocation closed, bed released; finance clearance only recorded as references (no settlement).

Student identity read from `student_profiles` / `users` at request time (not copied into resident document beyond links).

## Visitor policy

- `institution_settings.settings.hostel.visitor_policy` plus `hostel_visitor_restrictions` per hostel scope.
- Residents must be `checked_in` before visitor registration.

## Tests

```bash
cd backend
py -m pytest tests/test_hostel_phase3.py tests/test_hostel_phase2.py -q
```

## Limitations

- Mess enrollment and outpass modules not implemented (placeholder fields only).
- Financial clearance on checkout is reference-only.
- Resident confirmation by student not implemented (warden/admin only).