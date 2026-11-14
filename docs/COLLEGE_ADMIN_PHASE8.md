# College Admin Phase 8

LMS administration (module 15) and reports & analytics (module 16).

## LMS (`/api/v1/college-admin/lms-administration`)

Institutional configuration only — faculty-owned `learning_materials`, `course_assignments`, and `assignment_submissions` are read for monitoring, not duplicated.

**Collections**

| Collection | Purpose |
|------------|---------|
| `institution_lms_settings` | Default access, content types, quiz/moderation, integration ref |
| `lms_course_mappings` | Course ↔ external LMS keys |
| `lms_content_categories` | Taxonomy for materials |
| `lms_publishing_policies` | Approval + publish windows; syncs `assignment_rules` |
| `lms_configuration_history` | Settings/mapping/policy snapshots |

**Endpoints**

- `GET/PATCH /settings`
- `GET/PUT /course-mappings`, `/content-categories`, `/publishing-policies`
- `GET /statistics`, `/monitoring`, `/configuration-history`, `/integrations`

**Permissions:** `college:lms:read`, `manage`, `config`

## Reports (`/api/v1/college-admin/reports-analytics`)

Aggregates at generation time via `OperationalDataReader` and LMS stats; snapshots stored in `institution_analytics_snapshots` (not full business data clones).

**Collections**

| Collection | Purpose |
|------------|---------|
| `institution_report_definitions` | Built-in + custom report catalog with required permission |
| `institution_report_filters` | Saved department/date/academic filters |
| `institution_report_jobs` | Generate + schedule jobs, failure tracking |
| `institution_report_exports` | Export metadata + hashed token |
| `institution_analytics_snapshots` | Point-in-time metrics JSON |
| `institution_report_access_logs` | Generate/export/download audit |

**Endpoints**

- `GET /dashboard` — institutional analytics summary (RBAC-redacted finance/HR/LMS)
- `GET/PUT /definitions`, `PUT /filters`
- `POST /generate`, `GET /jobs`, `GET /jobs/{id}`, `GET /snapshots/{id}`
- `POST /schedule`, `POST /exports`, `GET /exports/download?token=…`
- `GET /failures`

**Permissions:** `college:reports:read`, `generate`, `export`, `schedule`, `manage`

Export download tokens use Redis (`college:report_export:*`, 15 min TTL) when Redis is available.

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase1.py … tests/test_college_admin_phase8.py -q
```

**Current suite:** 40 passed (phases 1–8).