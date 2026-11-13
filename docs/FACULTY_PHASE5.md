# Faculty / Professor — Phase 5 (Final)

Phase 5 completes the Faculty Portal backend with **Communication & Notifications** and **Self-Service / Personal Records**.

## Module 9 — Communication

| Collection | Purpose |
|------------|---------|
| `faculty_announcements` | Course/section announcements with publish history |
| `academic_messages` | Reminders and academic messages |
| `communication_recipients` | Authorized roster recipients per announcement |
| `faculty_notification_preferences` | Email/push/digest preferences |
| `faculty_notification_delivery_logs` | Channel dispatch audit |

Reuses `faculty_notifications`, `faculty_timetable_notifications` for inbox aggregation.

**APIs:** `/api/v1/faculty/me/communication/*`  
Includes `GET /me/communication/history`, `POST /me/communication/assignment-updates`.  
Rate limit: 5 announcements/min/faculty (Redis).

## Module 10 — Self-Service

| Collection | Purpose |
|------------|---------|
| `leave_requests` | Central HR leave records (`app/modules/hr`) |
| `payslip_references` | Payroll document pointers (owner-only) |
| `employee_profile_snapshots` | Permitted HR employment fields |
| `faculty_personal_documents` | Authorized personal files |
| `faculty_report_exports` | Generated reports + expiring tokens |
| `faculty_document_access_logs` | Document/report access audit |
| `faculty_activity_logs` | Reused for academic activity history |

**APIs:** `/api/v1/faculty/me/self-service/*`

Payroll returns `status: unavailable` when `PAYROLL_INTEGRATION_ENABLED=false` and no payroll integration provider is registered.

## Permissions

- `faculty:communication:read|manage`
- `faculty:self_service:read`

## Security

- Announcements require active course/section assignment.
- Recipients derived from enrollment rosters only.
- Leave and payslips scoped to `employee_user_id == authenticated user`.
- Report downloads use hashed tokens + optional HMAC signature + expiry.

## Tests

```bash
cd backend
pytest tests/test_faculty_phase5.py -q
```

## Faculty portal phases

| Phase | Modules |
|-------|---------|
| 1 | Dashboard, profile |
| 2 | Course content, timetable |
| 3 | Attendance, LMS |
| 4 | Assessment, student support |
| 5 | Communication, self-service |

See `docs/ARCHITECTURE.md` for the living system diagram.
