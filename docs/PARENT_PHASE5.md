# Parent / Guardian Portal — Phase 5

Parent–college meetings; student services visibility; consolidated reports; account security.

Aligned with `backend_and_frontend.md`. Reuses hostel/transport/library readers, finance/exam/attendance parent services, `RefreshToken` session revocation, and audit logs — no duplicate operational systems.

## Module 1 — Meetings

**Prefix:** `/api/v1/parents/me/meetings` (categories, representatives, availability, dashboard)  
**Per student:** `/api/v1/parents/me/students/{id}/meetings/*`

| Capability | Permission | Relationship |
|------------|------------|--------------|
| View dashboard, lists | `parent:meeting:read` | `request_meetings` |
| Create / reschedule / cancel | `parent:meeting:manage` | `request_meetings` |

**Collections:** `parent_meeting_categories`, `parent_meeting_availability`, `parent_meeting_requests`, `parent_meeting_appointments`, `parent_meeting_history`, `parent_meeting_outcomes`, `parent_meeting_followups`

**Admin:** `GET /college-admin/parent-administration/meeting-requests`, `POST .../decide`, `POST .../meeting-appointments/{id}/outcome`

Staff internal notes (`staff_preparation_notes`, `staff_internal_notes`) are **not** returned on parent APIs.

## Module 2 — Student services, reports, security

### Student services (per student)

`GET .../services/overview|hostel|transport|library|mess` — `parent:services:read` + `view_hostel|view_transport|view_library`

`POST/GET .../services/enquiries` — `parent_student_service_enquiries`

### Reports

- `GET /me/reports/dashboard`
- `GET /me/reports/export?category=...&student_user_id=...`
- `GET .../students/{id}/reports/export?category=...`

Permission: `parent:reports:read`. Export records `parent_report_access_history`. PDF format accepted as parameter; payload is structured JSON with export token (institution PDF renderer can consume).

### Account security

**Prefix:** `/api/v1/parents/me/security`

| Route | Permission |
|-------|------------|
| account, sessions, login-activity | `parent:security:read` |
| revoke-all sessions, contact-change, relationship review | `parent:security:manage` |

Collections: `parent_account_contact_change_requests`, `parent_relationship_access_review_requests`

## Defaults

`request_meetings` default grant on approved relationships: **true**.

## Tests

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_parent_phase5.py -rs -q
```

## Limitations

- Mess module integration not present — returns disabled summary.
- Meeting reminders not pushed via outbox in this phase (status/history only).
- PDF binary generation delegated to future document service; export token + JSON payload provided.
- Real-time transport tracking intentionally excluded.

## Stop boundary

Phase 5 complete. Parent portal backend phases 1–5 delivered as scoped.