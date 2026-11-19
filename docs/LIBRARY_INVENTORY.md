# Book Copy Inventory (Librarian module — phase 4)

Physical copies are authoritative in **`library_copies`** with admin metadata in **`library_book_copies`**. Catalogue titles remain in **`library_catalog_items`** (module 3).

## API prefix

`/api/v1/library/inventory`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/copies` | Register copy (auto `copy_id` if omitted) |
| GET | `/copies` | List/filter by `book_id`, `branch_code`, `status` |
| GET | `/copies/{copy_id}` | View copy |
| PATCH | `/copies/{copy_id}` | Update (optimistic `expected_version`) |
| POST | `/copies/{copy_id}/transfer` | Branch transfer |
| POST | `/adjustments` | Inventory adjustment workflow |
| GET | `/duplicates` | Duplicate barcode/accession aggregation |
| GET | `/missing` | Copies with `lost` status |
| GET | `/verifications` | List stock verification sessions |
| POST | `/verifications` | Start stock verification |
| POST | `/verifications/{id}/scan` | Scan barcode or copy_id |
| POST | `/verifications/{id}/complete` | Finalize missing/unexpected counts |
| GET | `/copies/{copy_id}/history` | `library_inventory_history` |

## Copy statuses

`available`, `issued`, `reserved`, `maintenance`, `damaged`, `lost`, `withdrawn`

## RBAC

- `library:inventory:read` / `library:inventory:manage`
- Branch-scoped manage uses staff assignments (module 2)
- College: `college:library:*`

## Collections

- `library_copies` — extended with branch, shelf, condition, version
- `library_book_copies` — accession, barcode, branch, shelf
- `library_inventory_adjustments`
- `library_stock_verifications` + `library_stock_verification_items`
- `library_inventory_history` — all changes (metadata JSON)

## Tests

```bash
cd backend && py -m pytest tests/test_library_inventory.py -q
```