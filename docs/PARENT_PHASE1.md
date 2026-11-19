# Parent / Guardian Portal — Phase 1

Dashboard & account management + student linking & relationship verification.

Follows `backend_and_frontend.md`: thin routers → schemas → services → Beanie models; tenant scope from `AccessScope`; student data access only through **active verified** `parent_student_relationships` + `parent_relationship_permissions`.

## API prefix

- Parent portal: `/api/v1/parents/me/*`
- College admin review: `/api/v1/college-admin/parent-administration/*`

### Module 1 — Dashboard & account

| Method | Path | Permission |
|--------|------|------------|
| GET | `/parents/me/dashboard` | `parent:dashboard:read` |
| GET | `/parents/me/profile` | `parent:profile:read` |
| PATCH | `/parents/me/profile` | `parent:profile:update` |
| PATCH | `/parents/me/profile/communication-preferences` | `parent:profile:update` |
| POST | `/parents/me/profile/contact-verification/start` | `parent:profile:update` |
| POST | `/parents/me/profile/contact-verification/confirm` | `parent:profile:update` |
| POST | `/parents/me/profile/correction-requests` | `parent:profile:update` |
| POST | `/parents/me/profile/deactivation-requests` | `parent:profile:update` |
| GET | `/parents/me/profile/security-activity` | `parent:profile:read` |
| GET | `/parents/me/relationships` | `parent:relationship:read` |

Dashboard query filters: `student_user_id`, `academic_year_label`, `semester_label`, `date_range`, `notification_category`, `request_status`.

Aggregates read from existing Student, Attendance, Examination, Finance, Communication, Hostel modules — **no duplicate official values**.

### Module 2 — Linking & verification

| Method | Path | Permission |
|--------|------|------------|
| POST | `/parents/me/linking/resolve-reference` | `parent:linking:manage` |
| POST | `/parents/me/linking/requests` | `parent:linking:manage` |
| GET | `/parents/me/linking/requests` | `parent:linking:manage` |

| Method | Path | Permission |
|--------|------|------------|
| GET | `/college-admin/parent-administration/link-requests` | `college:parent_admin:read` |
| POST | `/college-admin/parent-administration/link-requests/{id}/review` | `college:parent_admin:manage` |
| PATCH | `/college-admin/parent-administration/relationships/{id}` | `college:parent_admin:manage` |

## Collections

| Collection | Purpose |
|------------|---------|
| `parent_profiles` | Parent self-service profile & preferences |
| `parent_account_status_history` | Account lifecycle |
| `parent_contact_verifications` | Email/mobile verification tokens |
| `parent_profile_change_requests` | Institutional correction workflow |
| `parent_student_link_requests` | Linking workflow |
| `parent_student_relationships` | Authoritative parent–student links |
| `parent_relationship_permissions` | Per-relationship data grants |
| `parent_relationship_verification_history` | Verification decisions |
| `parent_relationship_status_history` | Status audit trail |
| `parent_relationship_documents` | Supporting document refs |
| `parent_link_reference_hints` | Short-lived student reference tokens |
| `parent_deactivation_requests` | Deactivation requests |

## Security

- `Role.PARENT` + `parent:self:access` on all `/parents/me/*` routes.
- Every student-scoped dashboard field checks `parent_student_relationships` status **active/verified** and `parent_relationship_permissions`.
- Client-supplied `student_user_id` validated against the parent’s verified links only.
- Student reference resolution returns **masked** hints only; full data after approval.

## Tests

```bash
cd backend
pytest tests/test_parent_phase1.py -q
```

## Out of scope (later phases)

Dedicated parent APIs for attendance detail, academics overview, fees payment initiation UI flows, meetings, and service requests beyond dashboard summaries.