# Book Acquisition & Procurement (Librarian module — phase 9)

Library-side workflows for book requests, quotations, receiving, catalogue linkage and inventory registration. **Does not duplicate** institution Finance/Procurement — references `InstitutionVendorRecord`, `InstitutionPurchaseRequest` and `InstitutionPurchaseOrder` from college-admin finance extensions.

Follows `backend_and_frontend.md` layering: routes → `acquisition_service` → Beanie models / finance ext readers.

## API (prefix `/api/v1/library/acquisitions`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `` | Create acquisition / suggestion |
| POST | `/{id}/submit` | Submit for approval |
| POST | `/{id}/approval` | Approve or reject (SoD: approver ≠ submitter) |
| POST | `/{id}/quotations` | Add vendor quotation |
| POST | `/{id}/quotations/{quotation_id}/select` | Select winning quote → `ordered` |
| POST | `/{id}/procurement` | Link PR/PO ids (procure permission) |
| POST | `/{id}/receipts` | Record delivery (partial allowed) |
| POST | `/{id}/catalogue` | Link to `LibraryCatalogItem` |
| POST | `/{id}/inventory-registration` | Request copy registration from received qty |
| GET | `` | Search |
| GET | `/{id}` | Detail |
| GET | `/{id}/history` | Acquisition audit trail |

Legacy college-admin `create_acquisition` delegates to the same service.

## Status flow

`draft` → `submitted` / `pending_approval` → `approved` | `rejected` → `quoted` → `ordered` → `partial_received` → `received` → `registered` (after inventory registration request).

## Authorization

| Permission | Roles (default) |
|------------|-----------------|
| `library:acquisition:read` | Librarian, college admin |
| `library:acquisition:manage` | Librarian, college admin |
| `library:acquisition:approve` | College admin |
| `library:acquisition:procure` | College admin (PR/PO link) |

Branch-scoped librarians require facility assignment when `branch_code` is set.

## Collections

| Collection | Use |
|------------|-----|
| `library_acquisitions` | Main request (extended fields + PR/PO refs) |
| `library_acquisition_quotations` | Vendor quotes |
| `library_acquisition_receipts` | Receipt lines |
| `library_acquisition_history` | Module history |
| `library_inventory_registration_requests` | Post-receive catalogue registration |

Institution audit: `library_acquisition.*` via `append_institution_audit`.

## Tests

```bash
cd backend && py -m pytest tests/test_library_acquisition.py -q
```

Broader librarian suite:

```bash
cd backend && py -m pytest tests/test_library_acquisition.py tests/test_library_fines.py tests/test_library_reservations.py tests/test_library_circulation.py tests/test_library_members.py tests/test_library_dashboard.py tests/test_college_admin_phase6.py tests/test_permissions.py -q
```