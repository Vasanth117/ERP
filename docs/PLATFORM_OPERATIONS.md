# Platform operations (Phase 4)

## Health

`GET /api/v1/platform/operations/health` aggregates:

- API application
- MongoDB, Redis, RabbitMQ (broker connect)
- Celery workers (inspect — **unknown** if no workers; not reported as healthy)
- Queue stats from `background_job_registry`
- Integration webhook failure counts

Snapshots stored in `service_health_snapshots` (no secrets).

## Incidents

Statuses: `open` → `acknowledged` → `investigating` → `identified` → `monitoring` → `resolved` → `closed`

APIs under `/api/v1/platform/operations/incidents`.

## Background jobs

`background_job_registry` stores **summary only** (no sensitive payloads). Retry allowed only for allowlisted types (`erp.jobs.ping`, `tenant.provisioning`) via `POST .../jobs/{id}/retry`.

## Permissions

- `platform:ops:read` / `platform:ops:manage`
- `platform:integration:read` / `platform:integration:manage`
