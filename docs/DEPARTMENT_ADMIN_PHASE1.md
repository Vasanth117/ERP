# Department Admin — Phase 1 (Dashboard + Profile & Settings)

## Scope

- **Module 1:** Department dashboard (aggregated reads scoped to the authenticated department admin's `users.department_id` / central `departments` row, linked to `institution_departments`).
- **Module 2:** Department profile extensions, allowlisted settings, sensitive-field change requests (college approval not implemented in Phase 1 — requests remain `submitted`).

## Data ownership

| Collection | Purpose |
|------------|---------|
| `institution_departments` | Master department row (college admin authority) |
| `departments` | Central department id on users/profiles |
| `department_profile_details` | Dept-admin editable contact/description fields |
| `department_settings` | Allowlisted department settings |
| `department_settings_history` | Setting change history |
| `department_profile_change_requests` | Workflow for name/code/status/HOD changes |

No dashboard snapshot collection — metrics are computed from existing modules.

## Permissions

| Code | Use |
|------|-----|
| `department:self:access` | Route gate |
| `department:dashboard:read` | Dashboard endpoints |
| `department:profile:read` / `update` | Profile |
| `department:settings:read` / `manage` | Settings |
| `department:academic_config:read` | Read-only academic visibility |

## API prefix

`/api/v1/department/*`

Key routes: `GET /dashboard`, `/dashboard/overview`, `/dashboard/students`, …, `GET|PATCH /profile`, `GET|PATCH /settings/{key}`, `POST /profile/change-requests`, `GET /academic-config/visibility`.

## Assumptions / limitations

- **Curriculum coverage** and **new admissions count** are not computed until college-defined rules are confirmed.
- **Attendance/timetable** scoping uses faculty linked to the central department id.
- **Change requests** are recorded only; college admin approval actions are a follow-up integration.
- **Scheduling conflicts** not exposed until academics module publishes conflict records.

## Tests

```powershell
cd backend
pytest tests/test_department_admin_phase1.py -q
```