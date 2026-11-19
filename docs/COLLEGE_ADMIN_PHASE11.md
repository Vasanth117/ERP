# College Admin Phase 11

Helpdesk & support (module 21).

## API (`/api/v1/college-admin/helpdesk`)

| Collection | Purpose |
|------------|---------|
| `institution_support_categories` | Module/issue taxonomy |
| `institution_support_sla_policies` | First response & resolution SLAs |
| `institution_support_tickets` | Primary ticket records |
| `institution_support_assignments` | Assignment/reassignment history |
| `institution_support_comments` | Requester-visible thread |
| `institution_support_internal_notes` | Staff-only notes |
| `institution_support_attachments` | Validated files (tenant-scoped storage) |
| `institution_support_escalations` | Escalation audit |
| `institution_support_history` | Timeline |
| `institution_support_feedback` | Post-resolution ratings |

**Permissions:** `college:helpdesk:read`, `manage`, `assign`, `internal`

**Integrations:** `DomainOutboxEvent` notifications, `append_institution_audit`, dashboard `unresolved_support_requests` includes institution tickets.

**Rate limits:** Ticket create (10/min) and comments (30/min) via Redis when available.

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase1.py … tests/test_college_admin_phase11.py -q
```