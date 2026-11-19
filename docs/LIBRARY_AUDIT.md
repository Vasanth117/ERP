# Library Audit History & Inventory Control (Module 14)

Unified library audit queries over **`library_audit_events`** (before/after deltas) and existing history collections (`library_inventory_history`, `library_circulation_records`, `library_catalog_history`, policy/fine/reservation/membership/acquisition/config histories). Institution audit chain reuse via `append_institution_audit`.

## API (`/api/v1/library/audit`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/events` | Search `LibraryAuditEvent` |
| GET | `/institution-logs` | Library rows from `institution_audit_logs` |
| GET | `/resources/{type}/{id}` | Federated resource timeline |
| GET | `/reports/summary` | Audit report snapshot |
| GET | `/inventory/discrepancies` | Stock audit discrepancies |
| POST | `/inventory/discrepancies/{id}/resolve` | Resolve/dismiss discrepancy |
| POST | `/inventory/adjustment-requests` | Propose stock correction (pending approval) |
| GET | `/inventory/adjustment-requests` | List adjustment requests |
| POST | `/inventory/adjustment-requests/{id}/approve` | Approve & apply (separation of duties) |
| POST | `/inventory/adjustment-requests/{id}/reject` | Reject proposal |

## Inventory control

- Completing a **stock verification** opens **discrepancy** rows for missing/unexpected scans.
- Copy changes from discrepancies use **adjustment requests**; authoritative copy records update only after **approval** (approver ≠ requester).
- Direct `/inventory/adjustments` remains for operational adjustments; both paths write audit events.

## Permissions

| Permission | Typical role |
|------------|----------------|
| `library:audit:read` | Librarian, college admin |
| `library:audit:export` | Librarian, college admin |
| `library:inventory:discrepancy:manage` | Librarian (propose/resolve) |
| `library:inventory:approve` | College admin only |

Audit documents are **append-only** (no update/delete APIs).

## Collections

- `library_audit_events`
- `library_stock_discrepancies`
- `library_stock_adjustment_requests`

## Reports

Report type `inventory_audit` in `/api/v1/library/reports/inventory_audit` aggregates open discrepancies and pending adjustment requests (see `LIBRARY_REPORTS.md`).

## Tests

```bash
cd backend; py -m pytest tests/test_library_audit.py -q
```