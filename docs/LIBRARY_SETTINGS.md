# Library Settings & Borrowing Policies (Module 13)

Versioned borrowing rules with branch, member-category and resource-type scope. Active loans store **`applied_policy_snapshot`** on `library_circulations` so renewals and fines use the policy at issue time.

## API (`/api/v1/library/settings/policies/borrowing`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `` | Create draft rule |
| GET | `` | Search rules |
| GET | `/preview` | Evaluate effective policy |
| GET | `/{policy_id}` | Latest version |
| PATCH | `/{policy_id}` | Edit draft |
| POST | `/{policy_id}/activate` | Activate (retires overlapping active rules) |
| POST | `/{policy_id}/retire` | Retire active rule |
| GET | `/{policy_id}/history` | Change log |

College-admin `PUT .../borrowing-policy` delegates here.

## Precedence

Among **active** rules matching effective dates: branch + member category + resource type (specificity). Fallback: legacy `library_borrowing_policies`, fine and reservation collections.

## Integration

- **Circulation:** issue stores snapshot; renew uses snapshot limits.
- **Fines:** overdue / lost / damaged use snapshot when present.
- **Reservations:** hold hours and max active from resolved policy.

## Permissions

`library:settings:read|manage|approve` (librarian: read+manage; college admin: all).

## Collections

- `library_borrowing_rules`
- `library_policy_history`

## Tests

```bash
cd backend; py -m pytest tests/test_library_settings.py -q
```