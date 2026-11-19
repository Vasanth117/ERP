# Department Admin — Phase 8

Phase 8: **Module 1 Reports & Analytics** and **Module 2 Data Import & Export**.

## Status

| Label | Meaning |
|-------|---------|
| **Implementation-complete** | APIs, RBAC, job metadata, unit tests delivered. |
| **Pending production verification** | Not production-ready without Mongo integration, load tests, and download security review. |

MongoDB integration tests **deferred**.

---

## Module 8.1 — Reports & Analytics

### Design

- **No duplicate reporting warehouse** — on-demand aggregates call existing Phase 1–7 services.
- **Catalogue** — `reports_catalog.py` (7 report types) with per-report permission.
- **Jobs** — `department_report_jobs` store metadata, preview, optional CSV artifact (base64), **72h retention**.
- **Large jobs** — optional `async_large` queues `department.report.generated` outbox (worker not implemented here).

### Permissions

- `department:reports:read` — catalogue, snapshots, job status, download (requester or generate permission).
- `department:reports:generate` — `POST /reports/generate`, download others’ artifacts.

### Report types

| Type | Source modules |
|------|----------------|
| `faculty_workload` | Faculty directory |
| `student_enrollment` | Dashboard student stats + programme performance |
| `attendance` | Attendance dashboard + shortages |
| `academic_performance` | Performance monitoring |
| `timetable` | Timetable dashboard |
| `examination_readiness` | Assessment / examination monitoring |
| `operations` | Requests summary + resource utilization |

### APIs (`/api/v1/department`)

| Method | Path |
|--------|------|
| GET | `/reports` |
| GET | `/reports/overview` |
| GET | `/reports/faculty-workload` |
| GET | `/reports/student-enrollment` |
| GET | `/reports/attendance` |
| GET | `/reports/academic-performance` |
| GET | `/reports/timetable` |
| GET | `/reports/examination-readiness` |
| POST | `/reports/generate` |
| GET | `/reports/jobs/{job_id}` |
| GET | `/reports/jobs/{job_id}/download` |

---

## Module 8.2 — Data Import & Export

### Design

- **Templates only** — no arbitrary collection import (`import_export_templates.py`).
- **CSV import** via base64 payload (max **2MB**, **5000** rows). **XLSX not implemented** — confirm before enabling.
- **Jobs** — `department_data_transfer_jobs` (import + export).
- **Import v1 template:** `faculty_course_assignment_rows` → creates **`department_faculty_assignment_requests`** (pending); does not alter college HR.
- **Exports:** `student_directory`, `faculty_directory`, `faculty_workload_summary` with **field allowlists**.
- **CSV formula injection** — cells prefixed in exports (`csv_safe.py`).
- Import file cleared from job document after successful execute (retain metadata).

### Permissions

- `department:data_transfer:read`
- `department:data_transfer:manage`

### APIs

| Method | Path |
|--------|------|
| GET | `/import-export/templates` |
| GET | `/import-export/datasets` |
| POST | `/import-export/import` |
| GET | `/import-export/imports/{job_id}` |
| POST | `/import-export/imports/{job_id}/validate` |
| POST | `/import-export/imports/{job_id}/execute` |
| GET | `/import-export/imports/{job_id}/errors` |
| POST | `/import-export/exports` |
| GET | `/import-export/exports/{job_id}` |
| GET | `/import-export/exports/{job_id}/download` |
| GET | `/import-export/history` |

---

## Assumptions (confirm)

1. Report/job artifacts stored as **base64 in MongoDB** (ephemeral); not object storage — suitable for dev/small exports only.
2. **No XLSX** parser in this phase (CSV only).
3. Import execute is **not transactional** across rows; partial row failures after crash require manual review.
4. Equipment/facility reports remain advisory (Phase 7 limitation).
5. Rate limits for upload/export **not** added yet (reuse college patterns later).

---

## Tests

- `backend/tests/test_department_admin_phase8.py` — RBAC, catalogue, CSV safety, template allowlist.
- Prior phase unit tests should still pass.

Run:

```text
python -m pytest tests/test_department_admin_phase8.py tests/test_department_admin_phase7.py -q
```

---

## Known limitations

- No malware scan hook on uploads.
- Report `operations` type requires both requests + resources read permissions indirectly via services.
- Synchronous report generation may timeout on very large faculties/student bodies (use filters).
- Does not replace `TenantExportRequest` college-wide export pipeline.

---

## Next phase

Phase 9 (Document Management / Security & Audit History) should wait until Phase 8 is reviewed.