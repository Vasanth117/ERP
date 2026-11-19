# Parent / Guardian Portal — Phase 4

Communication & notifications; documents; student-service requests; general support.

Aligned with `backend_and_frontend.md`. Reuses student notification sources, published academic documents, finance receipts, and institution helpdesk tickets — no parallel delivery or document stores.

## API overview

### Communication (parent scope)

Prefix: `/api/v1/parents/me/communications`

| Method | Path | Permission |
|--------|------|------------|
| GET | `/dashboard` | `parent:communication:read` |
| GET | `/notifications` | `parent:communication:read` |
| GET | `/notifications/{notification_key}` | `parent:communication:read` |
| POST | `/notifications/{notification_key}/read` | `parent:communication:manage` |
| POST | `/notifications/{notification_key}/acknowledge` | `parent:communication:manage` |
| GET/PUT | `/preferences` | read / manage |
| POST | `/support/enquiries` | `parent:support:submit` |
| GET | `/support/enquiries` | `parent:support:submit` |

Aggregates: institutional calendar & exam announcements, per-student feeds (attendance alerts, exam/finance/academic logs), parent-activity (linking, enquiry responses), service-request status updates. Filter by linked student, category, read state, priority, date range.

### Documents & service requests (per student)

Prefix: `/api/v1/parents/me/students/{student_user_id}`

| Method | Path | Permission | Relationship |
|--------|------|------------|--------------|
| GET | `/documents/dashboard` | `parent:document:read` | `view_results` / receipts |
| GET | `/documents` | `parent:document:read` | published only |
| GET | `/documents/{document_id}` | `parent:document:read` | |
| POST | `/documents/{document_id}/download` | `parent:document:read` | `view_results` |
| POST/GET | `/documents/requests` | `parent:document:read` | `submit_service_requests` |
| POST/GET | `/service-requests` | `parent:service_request:submit` | `submit_service_requests` |
| GET | `/service-requests/{request_id}` | same | |
| POST/GET | `/service-requests/{request_id}/comments` | same | |

`GET /api/v1/parents/me/service-request-types?category=...` — allowed request types per category.

### College admin

| Method | Path |
|--------|------|
| GET | `/college-admin/parent-administration/service-requests` |
| PATCH | `/college-admin/parent-administration/service-requests/{request_id}` |

## MongoDB collections (parent-only)

| Collection | Purpose |
|------------|---------|
| `parent_notification_preferences` | Channel/category preferences (mandatory categories cannot be disabled) |
| `parent_notification_read_history` | In-app read tracking |
| `parent_notification_acknowledgements` | Acknowledgement tracking |
| `parent_document_access_requests` | Parent-initiated document requests |
| `parent_document_access_history` | Download audit |
| `parent_student_service_requests` | Authoritative parent service requests |
| `parent_service_request_assignments` | Staff assignment trail |
| `parent_service_request_comments` | Parent/staff thread |
| `parent_service_request_history` | Status history |
| `parent_support_enquiries` | Portal support with `helpdesk_ticket_id` link |

## Key modules

- `communication_portal_service.py`, `integrations/communication_aggregator.py`
- `document_portal_service.py`
- `service_request_service.py`, `support_portal_service.py`
- `communication_router.py`

## Default permission change

`submit_service_requests` default grant on new approved relationships is **true** (Phase 4 workflows).

## Tests

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_parent_phase4.py -rs -q
```

## Limitations

- Email/SMS/push dispatch uses existing outbox/providers when wired; in-app feed does not imply external delivery success.
- Parent scholarship document uploads reuse attachment refs only (no new storage layer).
- PTM / meetings module explicitly out of scope.

## Stop boundary

Phase 4 only — no Parent–College Meetings or Student Services Reports until approved.