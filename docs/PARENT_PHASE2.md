# Parent / Guardian Portal — Phase 2

Student profile & academic overview + attendance monitoring & alerts.

Follows `backend_and_frontend.md`. All routes require `Role.PARENT`, active verified `parent_student_relationships`, and granular `parent_relationship_permissions` (`view_profile`, `view_attendance`, `view_results`).

## API prefix

`/api/v1/parents/me/students/{student_user_id}/*`

### Module 1 — Profile & academic overview

| Method | Path | Permission |
|--------|------|------------|
| GET | `.../profile` | `parent:academic:read` + `view_profile` |
| GET | `.../academics/overview` | `parent:academic:read` |
| GET | `.../academics/history` | `parent:academic:read` |
| POST | `.../academics/enquiries` | `parent:academic:read` |
| GET | `.../academics/enquiries` | `parent:academic:read` |

Reads: `student_profiles`, `student_academic_records`, enrollment rosters, course catalogue, institution profile/campus. Progress/CGPA only when `view_results` is granted.

### Module 2 — Attendance

| Method | Path | Permission |
|--------|------|------------|
| GET | `.../attendance/dashboard` | `parent:attendance:read` + `view_attendance` |
| GET | `.../attendance/subjects` | same |
| GET | `.../attendance/daily` | same |
| GET | `.../attendance/history` | same |
| GET | `.../attendance/shortages` | same |
| GET | `.../attendance/alerts` | same |
| POST | `.../attendance/alerts/{id}/acknowledge` | same |
| POST | `.../attendance/enquiries` | `parent:attendance:enquiry` |
| GET | `.../attendance/enquiries` | `parent:attendance:read` |

Percentages use `AttendancePolicyReference.rules` and `policy_engine.calculate_percentage` — same as the student portal.

### College admin — enquiries

| Method | Path |
|--------|------|
| GET | `/college-admin/parent-administration/attendance-enquiries` |
| POST | `/college-admin/parent-administration/attendance-enquiries/{id}/respond` |
| GET | `/college-admin/parent-administration/academic-enquiries` |
| POST | `/college-admin/parent-administration/academic-enquiries/{id}/respond` |

## Collections

| Collection | Purpose |
|------------|---------|
| `parent_academic_enquiries` | Profile/academic discrepancy requests |
| `parent_attendance_enquiries` | Attendance enquiries |
| `parent_attendance_enquiry_history` | Enquiry status trail |
| `parent_attendance_alerts` | Shortage alerts (deduped by `alert_key`) |
| `parent_attendance_alert_acknowledgements` | Parent ack records |

## Tests

```bash
cd backend
pytest tests/test_parent_phase2.py -q
```

## Out of scope (later phases)

Examination results detail, fees/payments, dedicated notification push delivery, automated event-driven alert workers (alerts sync on parent attendance reads).