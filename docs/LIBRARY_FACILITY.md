# Library & Branch Management (Librarian module — phase 2)

Institutional libraries, branches, schedules, holidays, staff assignments, sections, shelf locations, and configuration history. Reuses `library_branches`, `employee_records`, `institution_campuses`, and institution audit logging.

## API prefix

`/api/v1/library/facility`

See OpenAPI (`/docs`) for full request/response schemas.

### Libraries
- `POST /libraries` — create (college `college:library:manage` or institution-level manage)
- `GET /libraries` — paginated list
- `GET /libraries/{library_code}`
- `PATCH /libraries/{library_code}` — partial update

### Branches
- `POST /branches` — create under a library (`library_branches`, unique `branch_code` per tenant)
- `GET /branches` — filter `library_code`
- `GET /branches/{branch_code}`
- `PATCH /branches/{branch_code}`
- `GET /branches/{branch_code}/statistics` — copy/circulation/fine roll-up

### Operating hours
- `PUT /operating-hours` — weekly schedule with closed days and multiple sessions
- `GET /operating-hours?library_code=&branch_code=`

### Holidays
- `POST /holidays`, `GET /holidays`, `GET /holidays/{holiday_id}`, `PATCH /holidays/{holiday_id}` (deactivate via `is_active: false`)

### Staff
- `POST /staff-assignments`, `PATCH /staff-assignments/{assignment_id}`, `GET /staff-assignments`
- Validates `employee_records` (active employment only)

### Sections & shelf locations
- `POST|GET /sections?branch_code=`, `PATCH /sections/{branch_code}/{section_code}`
- `POST|GET /shelf-locations?branch_code=`, `PATCH /shelf-locations/{branch_code}/{location_code}`
- Parent hierarchy: floor → room → rack → shelf

### Configuration history
- `GET /configuration-history` — `library_configuration_history` (+ `append_institution_audit`)

## Collections

| Collection | Purpose |
|------------|---------|
| `library_institutions` | Parent library entity |
| `library_branches` | Extended branch records (existing) |
| `library_operating_hours` | Weekly schedules |
| `library_holidays` | Closures |
| `library_staff_assignments` | Employee ↔ library/branch |
| `library_sections` | Branch sections |
| `library_shelf_locations` | Hierarchical locations |
| `library_configuration_history` | Module change log |

## RBAC

| Permission | Use |
|------------|-----|
| `library:facility:read` | Read operations |
| `library:facility:manage` | Branch-scoped writes (with staff assignment) |
| `college:library:manage` | Full tenant library administration |
| `college:library:read` | Read-all |

Librarians without college manage must have an **active** `library_staff_assignments` row covering the library (all branches) or specific branch.

## Tests

```bash
cd backend && py -m pytest tests/test_library_facility.py tests/test_permissions.py -q
```