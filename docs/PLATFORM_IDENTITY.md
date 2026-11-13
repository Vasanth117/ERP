# Platform operators (Phase 3)

## Identity model

- **Auth record:** `users` with `tenant_id = null` (shared auth subsystem; no duplicate password store).
- **Platform profile:** `platform_users` (`PlatformOperatorProfile`) — role, grants/denies, MFA, suspension, login metadata.
- **Assignments:** `platform_role_assignments` history.
- **Invitations:** `platform_invitations` (hashed tokens).
- **Sessions:** `platform_sessions` linked to refresh token families.

## Roles (least privilege)

| Role | Typical use |
|------|-------------|
| `platform_owner` | Full platform control |
| `platform_super_admin` | Operations without billing override |
| `platform_ops_admin` | Read/monitor + request support |
| `platform_support_operator` | Support workflow only |
| `platform_security_auditor` | Audit + security read/export |
| `platform_billing_admin` | Billing views |

Permissions are defined in `app/authorization/platform_roles.py`. Legacy `super_admin` users without a profile receive **owner-equivalent** permissions via the resolver.

## APIs

Base path: `/api/v1/platform/operators`

Seed role catalog:

```powershell
cd backend
python -m scripts.bootstrap_platform_roles
```
