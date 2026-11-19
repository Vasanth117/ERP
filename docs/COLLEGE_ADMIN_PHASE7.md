# College Admin Phase 7

Hostel administration (module 13) and communication administration (module 14).

## Hostel (`/api/v1/college-admin/hostel-administration`)

- Inventory: buildings, blocks, rooms, beds (`hostel_*` collections)
- Applications review / waitlist (`hostel_applications`, `hostel_waiting_list`)
- Allocation approval with bed locking + partial unique indexes on active `hostel_allocations`
- Check-in / check-out → sync `hostel_room_allocations`, free beds on checkout
- Visitors, outpass decisions, maintenance, incidents, rules, mess plans
- Occupancy report

Permissions: `college:hostel:read`, `manage`, `allocate`

## Communication (`/api/v1/college-admin/communication-administration`)

- Institution announcements (draft / scheduled / published)
- Templates, audience groups, provider settings (`credential_ref` only — no raw secrets in API)
- Delivery logs, failed listing, retry (max 3)
- Summary report

Permissions: `college:communication:read`, `manage`, `publish`, `config` (separate publish from compose)

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase7.py tests/test_college_admin_phase1.py … phase6.py -q
```