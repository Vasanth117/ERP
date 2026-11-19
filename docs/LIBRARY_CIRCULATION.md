# Book Issue, Return & Renewal (Librarian module — phase 6)

Authoritative circulation for physical copies. Follows `backend_and_frontend.md` layering and reuses membership, inventory, catalogue and `library_borrowing_policies`.

## API (prefix `/api/v1/library/circulation`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/issue` | Issue copy to eligible member |
| POST | `/{circulation_id}/return` | Return loan (good / damaged / lost) |
| POST | `/{circulation_id}/renew` | Renew active/overdue loan |
| GET | `` | Search loans |
| GET | `/{circulation_id}` | Loan detail (overdue sync on read) |
| GET | `/{circulation_id}/history` | Audit trail |

College admin paths `POST /college-admin/library-administration/circulation/*` delegate to the same service.

## Business rules

- **Eligibility:** `library_membership_references` + institution account status (via member module).
- **Limits:** `min(policy.max_books, membership.borrowing_limit)` active/overdue loans per member.
- **Due date:** `loan_days` from policy (branch-specific, else tenant default); renewals extend from `max(due_at, today)`.
- **Renewals:** Capped by `policy.renewal_limit`.
- **Concurrency:** Copy claimed with MongoDB `find_one_and_update` on `status=available`; partial unique index blocks duplicate active loans per copy.
- **Return dispositions:** `good` → copy available; `damaged` → `damaged`; `lost` → `lost`.
- **Fines:** Not created by this module (fine workflows remain out of scope).

## Authorization

- **Librarian:** `library:circulation:read`, `library:circulation:manage`.
- **College admin:** `college:library:*` bypass on manage.
- Branch-scoped librarians require facility assignment for the branch (except college admin).

## Collections

| Collection | Use |
|------------|-----|
| `library_circulations` | Active loan records |
| `library_circulation_records` | Transaction history |
| `library_inventory_history` | Copy issue/return events |
| `library_copies` | Atomic status updates |

## Tests

```bash
cd backend && py -m pytest tests/test_library_circulation.py tests/test_college_admin_phase6.py -q
```