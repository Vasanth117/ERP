# College ERP — Backend Architecture (living doc)

## Current shape

- **Modular monolith** (`backend/app/modules/*`)
- **API version** `/api/v1`
- **Multi-tenant** shared MongoDB database with `tenant_id` on college-owned data
- **Auth** centralized JWT access tokens + rotating refresh tokens
- **Authorization** role → permission map (`app/authorization/permissions.py`)
- **Async jobs** Celery + RabbitMQ
- **Cache / rate limits** Redis

## Layers

1. Routers — HTTP only, envelope responses on active modules
2. Services — business rules and workflows
3. Repositories — tenant-scoped data access
4. Models — Beanie documents
5. Audit — `audit_logs` for security-sensitive actions

## Not in scope yet (deferred)

CI/CD, Prometheus/Grafana, production Nginx/TLS automation, full module catalogue, master data modules.

## Next implementation phases

1. Complete institutional master data (campus, programme, academic year, …)
2. Student + enrollment workflows
3. Remaining ERP domains per roadmap
