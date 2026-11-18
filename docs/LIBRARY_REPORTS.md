# Library Reports & Analytics (Module 12)

Read-only analytics over authoritative library collections. Reuses **dashboard aggregations** where possible and **department CSV export utilities** (`csv_safe`) — not a duplicate ERP reporting platform.

## API (`/api/v1/library/reports`)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/catalog` | Available report types (finance reports hidden without permission) |
| GET | `/{report_type}` | JSON snapshot with filters |
| POST | `/exports` | Generate CSV/JSON export job |
| GET | `/exports/{job_id}/download` | Download completed export |

### Filters (query / body)

`date_from`, `date_to`, `branch_code`, `category`, `member_category`, `status`

### Report types

`overview`, `catalogue_statistics`, `physical_inventory`, `circulation_summary`, `overdue_books`, `member_activity`, `circulation_history`, `reservation_statistics`, `fine_summary` (finance), `lost_damaged`, `acquisition_procurement`, `digital_usage`, `branch_performance`, `popular_books`

## Permissions

| Permission | Use |
|------------|-----|
| `library:report:read` | View reports |
| `library:report:export` | CSV export jobs |
| `library:report:finance` | Fine collection / balance reports |

College-admin `GET .../library-administration/reports/summary` delegates to overview metrics.

## Collections

- `library_report_jobs` — export jobs (72h retention)

## Tests

```bash
cd backend; py -m pytest tests/test_library_reports.py -q
```