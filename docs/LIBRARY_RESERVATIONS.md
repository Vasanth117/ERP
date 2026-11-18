# Book Reservations & Hold Queue (Librarian module — phase 7)

FIFO hold queues per book and branch, copy allocation with concurrency controls, hold expiry, and in-app notifications.

## API (prefix `/api/v1/library/reservations`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `` | Create reservation for a member |
| GET | `` | Search reservations |
| GET | `/queue/{book_id}` | Ordered queue |
| POST | `/policy` | Branch reservation rules |
| GET | `/{reservation_id}` | Detail |
| POST | `/{reservation_id}/cancel` | Cancel |
| POST | `/{reservation_id}/allocate` | Assign copy (optional `copy_id`) |
| POST | `/{reservation_id}/fulfill` | Mark picked up |
| GET | `/{reservation_id}/history` | Audit trail |

Statuses: `queued`, `ready`, `fulfilled`, `cancelled`, `expired`.

## Rules

- **Policies** (`library_reservation_policies`): `hold_hours`, `max_active_per_member`, `reserve_only_when_unavailable`.
- **Queue:** priority desc, then `created_at` asc; positions renumbered on cancel.
- **Allocation:** atomic copy `available → reserved` + reservation `queued → ready`; partial unique index on `copy_id` for `ready`.
- **Return hook:** circulation return on `available` copies calls `offer_next_for_book`.
- **Notifications:** `library_reservation_notifications` (in-app).

## Authorization

`library:reservation:read` / `library:reservation:manage` (librarian); college admin bypass.

## Tests

```bash
cd backend && py -m pytest tests/test_library_reservations.py tests/test_student_portal_phase10.py -q
```