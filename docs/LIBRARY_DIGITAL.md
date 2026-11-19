# Digital Library & E-Resources (Librarian module — phase 10)

E-books, journals, papers and reference materials with metadata, catalogue links, licensing and secure file access. Binary content uses tenant-scoped **LMS file storage** (`app/modules/lms/storage.py`); MongoDB holds metadata and access logs only.

## API (prefix `/api/v1/library/digital-resources`)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `` | Register resource |
| GET | `` | Search / filter (category, type, published, `q`) |
| GET | `/{id}` | Detail (no storage key exposed) |
| PATCH | `/{id}` | Update metadata, license, eligibility |
| POST | `/{id}/file` | Attach file (base64 upload) |
| GET | `/{id}/download` | Authenticated download (increments counters) |
| GET | `/{id}/external-link` | Licensed external URL (logged) |
| GET | `/{id}/access-log` | Access history |

**Student portal:** `/api/v1/students/me/library/digital`, `.../{resource_id}/download`, `.../{resource_id}/external-link`

Legacy college-admin `POST .../digital-resources` delegates to the same register flow.

## Business rules

- **Types:** `ebook`, `journal`, `research_paper`, `reference`
- **Catalogue:** optional `book_id` → `LibraryCatalogItem`
- **License:** `license_expires_at` blocks patron access when expired
- **Downloads:** optional global `max_downloads` and `max_downloads_per_user`; enforced via `library_digital_access_logs`
- **Eligibility:** `requires_membership` + active `LibraryMembershipReference`; optional `eligibility_member_categories`
- **External links:** must be `http`/`https`; `allow_external_link` flag

## Authorization

| Permission | Roles (default) |
|------------|-----------------|
| `library:digital:read` | Librarian, college admin |
| `library:digital:manage` | Librarian, college admin |
| Patron access | `student:library:read` (students) or library digital read (staff preview) |

## Collections

| Collection | Use |
|------------|-----|
| `library_digital_resources` | Metadata, license, storage key reference |
| `library_digital_access_logs` | view / download / external_link |

## Tests

```bash
cd backend; py -m pytest tests/test_library_digital.py -q
```