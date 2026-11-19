# Hostel Admin Phase 2

Room & bed allocation (HA 03) and applications / waiting list (HA 04). Follows `backend_and_frontend.md`.

## APIs

Prefix: `/api/v1/hostel`

### Availability & allocation

| Method | Path | Permission |
|--------|------|------------|
| GET | `/me/availability/beds` | `hostel:allocation:read` |
| GET | `/me/availability/rooms` | read |
| POST | `/me/allocations` | `hostel:allocation:manage` or `college:hostel:allocate` |
| GET | `/me/allocations` | read |
| GET | `/me/allocations/{id}` | read |
| POST | `/me/allocations/confirm` | manage |
| POST | `/me/allocations/cancel` | manage |
| POST | `/me/allocations/extend` | manage |
| POST | `/me/transfers` | manage |
| POST | `/me/transfers/{id}/complete` | manage |

### Applications & waiting list

| Method | Path | Permission |
|--------|------|------------|
| GET/POST | `/me/applications` | read / manage |
| POST | `/me/applications/staff` | manage |
| POST | `/me/applications/review` | manage |
| GET/POST | `/me/waiting-list` | read / manage |
| POST | `/me/waiting-list/priority` | manage |
| POST | `/me/offers` | manage |

### Student portal

| Method | Path |
|--------|------|
| POST | `/api/v1/students/me/hostel/applications` |
| POST | `/api/v1/students/me/hostel/offers/respond` |

## Collections

| Collection | Notes |
|------------|-------|
| `hostel_applications` | **Extended** lifecycle fields |
| `hostel_allocations` | **Extended** dates, hostel_code, workflow |
| `hostel_waiting_list` | **Extended** `list_id`, priority |
| `hostel_waiting_lists` | **New** list definitions |
| `hostel_application_reviews` | **New** |
| `hostel_application_status_history` | **New** |
| `hostel_allocation_offers` | **New** |
| `hostel_allocation_history` | **New** |
| `hostel_room_transfer_requests` | **New** |

## Concurrency

Bed claim uses atomic `find_one_and_update` on `hostel_beds` with `status=available`. Duplicate active allocations blocked by partial unique indexes on student and bed.

## Eligibility

Tenant settings: `institution_settings.settings.hostel.eligibility_rules` (not hardcoded).

## Notifications

Domain outbox events `hostel.*` via `hostel_notify.py`.

## Tests

```bash
cd backend
py -m pytest tests/test_hostel_phase2.py tests/test_hostel_phase1.py tests/test_college_admin_phase7.py -q
```

## Limitations (Phase 2)

- Check-in/checkout and resident management deferred to later phases.
- `HostelRoomAllocation` student publish sync not yet wired from portal allocations (college-admin check-in flow unchanged).
- Transfer approval is two-step (create + complete); no UI workflow engine integration.