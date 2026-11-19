# Hostel Admin Phase 5

Maintenance & complaints (HA 09) and rules & incidents (HA 10). Follows `backend_and_frontend.md`.

## APIs (`/api/v1/hostel`)

### Maintenance & complaints

| Method | Path |
|--------|------|
| GET | `/me/maintenance/dashboard` |
| POST | `/me/complaints`, `/me/complaints/assign`, `/me/complaints/status` |
| GET | `/me/complaints` |
| PUT | `/me/maintenance/schedules` |
| POST | `/me/maintenance/facility-availability` |

Permissions: `hostel:maintenance:read` / `hostel:maintenance:manage`.

### Rules & incidents

| Method | Path |
|--------|------|
| PUT | `/me/rules`, POST `/me/rules/publish`, GET `/me/rules/published` |
| GET | `/me/incidents/overview`, POST `/me/incidents`, GET `/me/incidents`, GET `/me/incidents/{id}` |
| POST | `/me/incidents/status`, `/investigation`, `/evidence`, `/disciplinary` |

Permissions: `hostel:rules:*`, `hostel:incident:read|manage|investigate`.

### Student portal

| Method | Path |
|--------|------|
| POST/GET | `/api/v1/students/me/hostel/complaints` (+ clarification, feedback) |
| GET/POST | `/api/v1/students/me/hostel/rules`, `/rules/acknowledge` |

## Collections

See `maintenance_models.py` and `rules_incident_models.py`. Legacy `hostel_maintenance_requests` retained and linked via `complaint_id`.

## Tests

```bash
cd backend
py -m pytest tests/test_hostel_phase5.py -q
```

## Limitations

- Helpdesk module not fully merged; complaints are hostel-scoped.
- Document storage uses reference strings only (no upload handler in this phase).
- Disciplinary outcomes do not update academic standing.
- Allegations remain `allegation_only` until investigation findings explicitly recorded.
- Communications/reports modules not implemented (per scope).