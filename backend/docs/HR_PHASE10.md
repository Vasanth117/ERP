# HR Phase 10 — Settings, Policies, Audit & Access

## Scope

- **Module 1:** General HR settings, policy categories, versioned configurable policies (`hr_staff_policy_registry`), lifecycle transitions, approvals, acknowledgements.
- **Module 2:** Audit dashboard, unified search (`HrStaffActivityLog` + `InstitutionAuditLog` where `module=hr`), employee timeline, CSV export with retention metadata, HR access scopes, temporary grants, access reviews, role profile catalog (overlay on platform RBAC).

Legacy `college_admin` `HrPolicy` (`hr_policies` collection) is unchanged.

## Collections

| Collection | Model |
|------------|--------|
| `hr_general_settings` | `HrGeneralSettings` |
| `hr_policy_categories` | `HrPolicyCategory` |
| `hr_staff_policy_registry` | `HrConfigurablePolicy` |
| `hr_policy_versions` | `HrPolicyVersion` |
| `hr_policy_approvals` | `HrPolicyApproval` |
| `hr_policy_acknowledgements` | `HrPolicyAcknowledgement` |
| `hr_access_assignments` | `HrAccessScopeAssignment` |
| `hr_role_permission_mappings` | `HrRolePermissionMapping` |
| `hr_temporary_access_grants` | `HrTemporaryAccessGrant` |
| `hr_access_review_records` | `HrAccessReviewRecord` |
| `hr_audit_export_history` | `HrAuditExportHistory` |

Reused: `hr_staff_activity_logs`, `institution_audit_logs`, central `Permission` / `Role.HR_STAFF`.

## APIs (prefix `/api/v1/hr`)

### Settings — `/settings`

- `GET/PUT /general`
- `GET/PUT /policy-categories`
- `GET/PUT /policies`, `GET /policies/{id}`, `POST /policies/{id}/transition`
- `GET /policies/{id}/versions`, `GET /policies/{id}/approvals`
- `GET /acknowledgements/pending`, `POST /policies/{id}/acknowledge`

### Audit & access — `/audit`

- `GET /dashboard`, `POST /search`, `GET /employees/{id}/timeline`
- `POST /export`
- `GET/PUT /role-profiles`, `PUT /access-scopes`
- `POST /temporary-access`, `POST /temporary-access/{id}/approve`, `POST /temporary-access/expire-due`
- `GET/POST /access-reviews`

## Permissions

- `hr:settings:read`, `hr:settings:manage`
- `hr:audit:read`, `hr:audit:export`
- `hr:access:manage`

## Policy lifecycle

`draft` → `review` → `approved` → `published` / `scheduled` → `active` → `suspended` / `expired` / `superseded` / `archived`

## Limitations

- Policy settings are stored as JSON buckets per category; cross-module enforcement (leave accrual engine, payroll cut-off, etc.) still reads domain-specific configs until wired to active policy documents.
- Temporary grants are recorded and audited; they do not yet merge into `effective_permissions` at login (platform RBAC remains authoritative).
- On **publish/activate**, policies with `requires_acknowledgement` seed pending rows for active employees and enqueue `hr.policy.acknowledgement_required` notifications. Use `POST /settings/acknowledgements/remind` for reminders.
- `log_hr_activity` mirrors all HR staff activities to `institution_audit_logs` (`module=hr`).
- Institution `block_self_approval` is enforced on policy **approve** via `assert_block_self_approval`.
- `HrAccessScopeAssignment` is enforced on audit employee timeline/search when an assignment exists (`hr_access_enforcement.py`).
- No DELETE/UPDATE APIs for audit history (by design).

## Tests

```bash
py -m pytest tests/test_hr_phase10.py -q
```