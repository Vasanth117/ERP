# College Admin Phase 9

Workflow & approval management (module 17) and audit & security management (module 18).

## Workflow (`/api/v1/college-admin/workflow-administration`)

Configurable multi-stage approvals with sequential and parallel stages, conditional skip rules, delegation, escalation on deadlines, cancellation/resubmission, and full history. Built-in templates: `leave`, `attendance_correction`, `finance_approval`.

| Collection | Role |
|------------|------|
| `institution_workflow_definitions` | Workflow catalog + version |
| `institution_workflow_stages` | Stage config, permissions, deadlines |
| `institution_workflow_instances` | Running/completed instances |
| `institution_approval_tasks` | Pending tasks per approver permission |
| `institution_approval_history` | Immutable timeline |
| `institution_workflow_delegations` | Time-bound delegation |
| `institution_workflow_escalations` | Overdue task escalation |

**Permissions:** `college:workflow:read`, `manage`, `approve`, `delegate`

Self-approval blocked when definition disallows and `institution_security_policies.block_self_approval` is true.

## Security (`/api/v1/college-admin/security-administration`)

Tenant-scoped only; platform security remains Super Admin.

| Collection | Role |
|------------|------|
| `institution_audit_logs` | Hash-chained append-only institutional audit |
| `institution_security_events` | Tenant security incidents |
| `institution_login_activity` | Login success/failure rows |
| `institution_access_reviews` | Access review decisions |
| `institution_security_policies` | Tenant security policy |
| `institution_audit_exports` | Export metadata + expiring tokens |
| `institution_audit_data_access_logs` | Meta-audit for audit searches |

Searches merge `institution_audit_logs` with existing `audit_logs` for the tenant. Integrity check validates hash chain on institutional entries.

**Permissions:** `college:security:read`, `manage`, `export`, `session`

## Tests

```bash
cd backend
py -m pytest tests/test_college_admin_phase1.py … tests/test_college_admin_phase9.py -q
```