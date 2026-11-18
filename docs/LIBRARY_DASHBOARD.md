# Library Dashboard (Librarian module — phase 1)

Backend-only dashboard for multi-tenant library operations. Follows `backend_and_frontend.md` / `ENGINEERING_GUIDE.md` layering: routes → services → repository → MongoDB.

## API (prefix `/api/v1/library`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/me/dashboard` | Full overview |
| GET | `/me/dashboard/catalogue` | Catalogue title count |
| GET | `/me/dashboard/copies` | Physical copy inventory |
| GET | `/me/dashboard/members` | Membership roll-up |
| GET | `/me/dashboard/circulation/today` | Issues/returns for a UTC day |
| GET | `/me/dashboard/reservations/pending` | Queued/ready reservations |
| GET | `/me/dashboard/fines/outstanding` | Open fines |
| GET | `/me/dashboard/acquisitions` | Recent + pending procurement |
| GET | `/me/dashboard/digital` | Digital resource counts |
| GET | `/me/dashboard/branches/inventory` | Branch-wise copy summary |
| GET | `/me/dashboard/due-dates` | Paginated upcoming due dates |
| GET | `/me/dashboard/activities` | Paginated circulation/inventory audit |
| GET | `/me/dashboard/alerts` | Overdue, lost, reservation, procurement alerts |

### Query parameters

- `branch_code` — validated against `library_branches` (tenant-scoped).
- `category` — exact match on `library_catalog_items.category`.
- `copy_status` — filter copy aggregates (`library_copies.status`).
- `anchor_date`, `range` (`today` \| `week` \| `month` \| `semester`) — window for acquisitions and activities.

## Authorization

- **Librarian:** `library:self:access`, `library:dashboard:read`.
- **College admin:** existing `college:library:read` also grants dashboard access.
- Tenant id is taken only from `AccessScope` (JWT/session), never from request body.

## Collections

| Metric | Collection(s) |
|--------|----------------|
| Catalogue titles | `library_catalog_items` (+ branch via `library_book_copies`) |
| Copy inventory | `library_copies` (+ branch via `library_book_copies`) |
| Overdue loans | `library_circulations` (`due_at`, `status`) |
| Members | `library_membership_references` + `institution_users` |
| Today issues/returns | `library_circulations` (`issued_at`, `returned_at`) |
| Reservations | `library_reservations` |
| Fines | `library_fines` |
| Acquisitions | `library_acquisitions` |
| Digital | `library_digital_resources` |
| Branch inventory | `library_book_copies`, `library_copies`, `library_branches` |
| Activities | `library_circulation_records`, `library_inventory_history` |

## Indexes added

- `library_circulations`: `circulation_issued_at`, `circulation_returned_at`, `circulation_due_status`
- `library_reservations`: `reservations_by_status`
- `library_book_copies`: `book_copies_by_branch`
- `library_acquisitions`: `acquisitions_by_status`

## Dependencies / limitations

- **Librarian branch assignment** module not built yet — branch filter validates branch existence; librarians are not restricted to assigned branches until that module exists.
- **Damaged copies** reported from `LibraryCopyStatus.MAINTENANCE` until a dedicated damaged status exists.
- Member inactive/suspended uses `library_membership_references.eligible` and `institution_users.account_status`.

## Tests

```bash
cd backend && pytest tests/test_library_dashboard.py tests/test_permissions.py -q
```