# Library Member Management (Librarian module — phase 5)

Registers and manages library membership for existing institutional users (students, faculty, employees). Follows `backend_and_frontend.md` layering: routes → services → `library_membership_references` (+ history).

## API (prefix `/api/v1/library/members`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `` | Register membership (link `member_user_id`) |
| GET | `` | Search / filter members |
| GET | `/by-number/{membership_number}` | Member details |
| GET | `/by-user/{member_user_id}` | Lookup by user id |
| PATCH | `/{membership_number}` | Update eligibility, dates, branch, status |
| POST | `/{membership_number}/suspend` | Suspend with reason |
| POST | `/{membership_number}/reactivate` | Reactivate suspended/inactive |
| GET | `/{membership_number}/borrowing-summary` | Loans/fines rollup (read-only circulation data) |
| GET | `/{membership_number}/history` | Membership audit trail |

### Query parameters (search)

- `q` — name, email, or membership number
- `category`, `status`, `branch_code`, `eligible`
- Standard pagination (`limit`, `offset`)

## Authorization

- **Librarian:** `library:member:read`, `library:member:manage` (+ `library:self:access` on portal).
- **College admin:** `college:library:read` / `college:library:manage` and role bypass on manage paths.
- Tenant id from `AccessScope` only.

## Data model

| Collection | Role |
|------------|------|
| `library_membership_references` | Canonical membership row (`membership_number`, category, status, dates) |
| `library_membership_history` | Per-action change log |
| `library_circulations`, `library_fines` | Read-only inputs for borrowing summary |

Member categories: `student`, `faculty`, `employee` — validated against existing `User` / `EmployeeRecord`; no duplicate user profiles.

Statuses: `active`, `inactive`, `suspended`, `expired` (expiry applied on read when `expires_on` is in the past).

Borrowing eligibility: `eligible` + `active` status + not past `expires_on` + institution user not suspended/deactivated.

## College admin bridge

`POST /college-admin/library-administration/membership` (`set_membership`) still sets basic eligibility; new rows receive an auto-generated `membership_number`.

## Tests

```bash
cd backend && py -m pytest tests/test_library_members.py tests/test_library_dashboard.py tests/test_college_admin_phase6.py -q
```