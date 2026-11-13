# College Admin Phase 2

## Modules

### User & role management

Base path: `/api/v1/college-admin`

| Endpoint | Description |
|---|---|
| `POST /users` | Create account + `institution_users` row |
| `POST /users/invite` | Secure invitation (hashed token) |
| `POST /users/invitations/accept` | Public accept + password |
| `GET /users`, `GET /users/{id}` | List / detail |
| `PATCH /users/{id}` | Permitted profile scope updates |
| `POST /users/{id}/activate` | Reactivate |
| `POST /users/{id}/suspend` | Suspend + revoke refresh tokens |
| `POST /users/{id}/deactivate` | Deactivate |
| `POST /users/{id}/roles` | Primary role + custom role assign |
| `POST /users/{id}/roles/revoke` | Revoke custom role |
| `POST /users/{id}/sessions/revoke` | Session revoke (`refresh_tokens`) |
| `POST /users/{id}/reset-access` | Revoke sessions + password reset token |
| `POST /users/password-reset/accept` | Complete reset |
| `POST /users/bulk` | Bulk create (max 100) |
| `GET /users/{id}/access-history` | Institution access history + login audits |
| `GET /roles`, `POST /roles`, `PATCH /roles/{id}` | Custom institutional roles |
| `GET /permissions` | Assignable permission catalogue |

### Department & organization

| Endpoint | Description |
|---|---|
| `POST /organization/units` | Schools, faculties, divisions |
| `GET /organization/units` | List units |
| `POST /departments` | Create department (syncs `departments` collection) |
| `GET /departments`, `GET /departments/{id}` | List / detail |
| `PATCH /departments/{id}` | Update hierarchy, campuses, programmes |
| `POST /departments/{id}/head` | Head assignment history |
| `POST /departments/{id}/transfer` | Parent / org unit transfer |
| `GET /departments/{id}/history` | Change log |
| `POST /departments/{id}/staff/{user_id}` | Staff association |

## Collections

`institution_users`, `institution_roles`, `institution_permissions`, `institution_role_assignments`, `institution_user_invitations`, `institution_access_history`, `institution_organization_units`, `institution_departments`, `department_hierarchy`, `department_head_assignments`, `department_staff_associations`, `department_history`.

Central identity remains `users`; refresh tokens remain in `refresh_tokens`.

## Security

- Permissions: `college:user:*`, `college:role:*`, `college:organization:*`, `college:user:privileged_assign`
- `rbac_policy.actor_may_assign_role` blocks platform roles and privilege escalation
- Custom role permissions must be in the institutional allowlist (no `platform:*`)
- Tenant isolation on every query via `require_college_tenant_scope`

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase2.py tests/test_college_admin_phase1.py tests/test_permissions.py -q --disable-warnings
```
