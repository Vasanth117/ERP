# College ERP — Database (living doc)

## Database

- **Engine:** MongoDB 7 (replica set `rs0` for transactions)
- **Default DB:** `erp` (development)

## Active collections

| Collection | Purpose |
|------------|---------|
| `tenants` | Colleges |
| `departments` | Departments per college |
| `users` | Login accounts (`tenant_id` null = platform) |
| `refresh_tokens` | Refresh token hashes (TTL on `expires_at`) |
| `audit_logs` | Security and admin actions |

## Platform collections (Super Admin Phase 1)

See [PLATFORM_DATABASE.md](./PLATFORM_DATABASE.md) for `tenant_onboarding`, `tenant_domains`, `tenant_admin_invitations`, `tenant_provisioning_jobs`, `tenant_status_history`, `platform_metrics_snapshots`, and `platform_alerts`.

## User indexes

- Unique `(tenant_id, email)` for college users
- Unique `email` where `tenant_id` is null for platform users

## Migrations

After model/index changes:

```powershell
cd backend
python -m scripts.migrate_indexes
```

Legacy `unique_user_email` index may need manual drop once per environment when upgrading from early schemas.
