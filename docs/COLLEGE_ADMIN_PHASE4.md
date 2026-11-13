# College Admin Phase 4

Faculty & employee administration (module 7) and attendance administration (module 8).

Base path: `/api/v1/college-admin`

## Faculty & employee administration

Prefix: `/faculty-administration`

| Endpoint | Description |
|---|---|
| `POST/GET /faculty`, `GET/PATCH /faculty/{id}` | Create/list/update faculty; syncs `faculty_profiles`, `employee_records`, `employee_profile_snapshots` |
| `POST /faculty/{id}/departments` | Department/campus assignment history |
| `POST /faculty/{id}/teaching` | Creates authoritative `faculty_assignments` + admin log |
| `POST/GET /faculty/{id}/workload` | Updates `faculty_workloads` + history |
| `POST /faculty/{id}/transfer` | Transfer with employment history |
| `POST /faculty/{id}/documents` | `faculty_document_references` |
| `GET /faculty/{id}/history` | Employment, dept, teaching, workload history |
| `POST /faculty/bulk` | Bulk import (max 100) |

Salary and confidential HR data remain in `employee_records.confidential_hr` and are never returned via college-admin read schemas.

## Attendance administration

Prefix: `/attendance-administration`

| Endpoint | Description |
|---|---|
| `PUT/GET /policies` | `institution_attendance_policies`; student policies sync to `attendance_policy_references` |
| `GET /summaries/departments` | Department-level pending/submitted/correction counts |
| `POST /monitoring/refresh` | Snapshot pending rows into `attendance_submission_monitoring` |
| `GET /submissions/missing` | Institution-wide pending submissions |
| `GET /corrections`, `POST /corrections/decide` | Review/approve/reject; approved corrections patch `attendance_records` only (session stays `submitted`) |
| `GET /shortages` | Students below policy threshold |
| `GET /history` | Submitted session history |
| `POST /reports/compliance` | Persist `attendance_compliance_snapshots` |

## Collections

**Faculty:** `employee_records`, `faculty_records`, `faculty_employment_history`, `faculty_department_assignments`, `faculty_teaching_assignments`, `faculty_workload_records`, `faculty_document_references`.

**Attendance admin:** `institution_attendance_policies`, `attendance_submission_monitoring`, `attendance_correction_approvals`, `attendance_compliance_snapshots`.

**Reused:** `faculty_profiles`, `faculty_assignments`, `faculty_workloads`, `attendance_sessions`, `attendance_records`, `attendance_correction_requests`, `attendance_policy_references`, `pending_attendance_submissions`.

## Security

- Permissions: `college:faculty_admin:read|manage`, `college:attendance_admin:read|manage`
- Tenant isolation via `require_college_tenant_scope`
- Correction approval is audited (`attendance_correction_approvals` + `audit_logs`)
- No silent overwrite of submitted sessions — only targeted record updates on approved corrections

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase4.py tests/test_college_admin_phase1.py tests/test_college_admin_phase2.py tests/test_college_admin_phase3.py -q --disable-warnings
```
