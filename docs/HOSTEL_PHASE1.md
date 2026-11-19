# Hostel Admin Phase 1

Dashboard (HA 01) and Hostel & Building Management (HA 02). Follows `backend_and_frontend.md`: thin routers → schemas → services → Beanie models; tenant scope from `AccessScope` only.

## API prefix

`/api/v1/hostel`

### Dashboard

| Method | Path | Permission |
|--------|------|------------|
| GET | `/me/dashboard` | `hostel:dashboard:read` or `college:hostel:read` |
| GET | `/me/dashboard/drill-down/{metric}` | same |

Query filters: `academic_year_label`, `hostel_code`, `building_code`, `block_code`, `floor_id`, `room_type`, `department_id`, `resident_status`, `allocation_status`, `mess_status`, `maintenance_status`, `anchor_date`, `range`.

Drill metrics: `hostels_active`, `beds_available`, `beds_occupied`, `residents_checked_in`, `applications_pending`, `waiting_list`, `visitors_inside`, `maintenance_open`, `incidents_open`, `outpass_overdue`.

### Infrastructure

| Method | Path | Permission |
|--------|------|------------|
| POST | `/me/infrastructure/hostels` | `hostel:infrastructure:manage` or `college:hostel:manage` |
| GET | `/me/infrastructure/hostels` | `hostel:infrastructure:read` or college hostel read |
| GET/PATCH | `/me/infrastructure/hostels/{hostel_code}` | read / manage |
| GET | `/me/infrastructure/hostels/{hostel_code}/capacity` | read |
| GET | `/me/infrastructure/hostels/{hostel_code}/history` | read |
| POST | `/me/infrastructure/buildings` | manage |
| PATCH | `/me/infrastructure/buildings/{building_code}` | manage |
| POST | `/me/infrastructure/buildings/{building_code}/deactivate` | manage |
| POST | `/me/infrastructure/blocks` | manage |
| POST | `/me/infrastructure/floors` | manage |
| POST | `/me/infrastructure/rooms` | manage |
| POST | `/me/infrastructure/beds` | manage |
| POST/PATCH | `/me/infrastructure/facilities` | manage |

Phase 1 does **not** expose allocation, applications, or resident assignment APIs (college-admin routes remain for those workflows until later phases).

## Collections

| Collection | Role |
|------------|------|
| `hostels` | **New** — institution hostels |
| `hostel_floors` | **New** |
| `hostel_facilities` | **New** |
| `hostel_facility_history` | **New** |
| `hostel_management_history` | **New** — operational history + links to institution audit |
| `hostel_buildings`, `hostel_blocks`, `hostel_rooms`, `hostel_beds` | **Reused/extended** (`hostel_code`, floor, room type, statuses) |
| Existing operational data | Dashboard read-only: `hostel_allocations`, `hostel_applications`, `hostel_visitor_logs`, `hostel_mess_plans`, `student_fee_demands` (mess label), etc. |

## RBAC

`Role.HOSTEL_ADMIN`: `hostel:self:access`, `hostel:dashboard:read`, `hostel:infrastructure:read`, `hostel:infrastructure:manage`, `tenant:read`.

College admin retains `college:hostel:*` and can use the same dashboard/infrastructure APIs.

## Tests

```bash
cd backend
py -m pytest tests/test_hostel_phase1.py tests/test_college_admin_phase7.py -q
```

## Known limitations

- Mess enrollment and plan-change approval counts are placeholders until Phase 6.
- Visitor expected/approval queues need pre-registration workflow.
- Per-administrator hostel assignment scope not enforced (filter validates hostel codes only).
- Finance mess outstanding uses open `student_fee_demands` with description matching `mess` (no independent balance ledger).