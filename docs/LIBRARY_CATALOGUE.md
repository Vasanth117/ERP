# Book Catalogue Management (Librarian module — phase 3)

Authoritative bibliographic data is stored in **`library_catalog_items`**. Physical copies remain in **`library_copies`** (not managed by this module).

## API prefix

`/api/v1/library/catalogue`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/records` | Create catalogue title |
| GET | `/records` | Search / filter / sort (paginated) |
| GET | `/records/{book_id}` | View record |
| PATCH | `/records/{book_id}` | Partial update |
| POST | `/records/{book_id}/archive` | Archive (unpublish) |
| GET | `/duplicates` | ISBN / title-publisher duplicate check |
| POST | `/import` | Bulk import (dry-run supported) |
| GET | `/records/{book_id}/history` | Catalogue change history |

## Data model (`library_catalog_items`)

Bibliographic fields: ISBN-10/13, title, subtitle, authors, publisher, publication details, edition, volume, language, category/subcategory, subject, academic classification, keywords, tags, description, metadata, cover references (`cover_url`, `cover_storage_key`), optional `primary_library_code`.

`archived=true` forces `published=false` (student catalogue hides archived titles).

## History & audit

- `library_catalog_history` — per-title snapshots
- `append_institution_audit` — `library_catalogue.*` actions

## Indexes

- Unique `(tenant_id, book_id)`
- Partial unique ISBN-10 / ISBN-13 per tenant
- Category and library code indexes

## RBAC

- `library:catalogue:read` / `library:catalogue:manage`
- College admin: `college:library:read` / `manage`

## Tests

```bash
cd backend && py -m pytest tests/test_library_catalogue.py -q
```