# Student Portal — Phase 3 (Timetable + Attendance)

## Scope

| Module | Prefix | Source of truth |
|--------|--------|-----------------|
| 5 — Timetable & calendar | `/students/me/timetable/*` | `timetable_entries`, `class_sessions`, `academic_calendar_events`, `examination_schedules` |
| 6 — Attendance | `/students/me/attendance/*` | `attendance_sessions`, `attendance_records`, `attendance_policy_references` |

## Portal-only collections

| Collection | Purpose |
|------------|---------|
| `student_timetable_views` | UI filters (course, hide cancelled, lab-only) |
| `academic_calendar_references` | Holidays / overlays (merged with central calendar) |
| `student_attendance_discrepancy_requests` | Student correction requests (does not alter marks) |
| `attendance_notification_records` | Shortage + timetable change notifications |

`attendance_policy_references` remains the **central** attendance module collection (read, not duplicated).

Attendance percentages use `attendance.policy_engine.calculate_percentage` with institutional weights. Missing marks on submitted sessions are treated as **absent** for percentage math; `data_status` marks `partial` when sessions are not yet submitted.

## Permissions

- `student:timetable:read`
- `student:attendance:read`
- `student:attendance:discrepancy` — submit discrepancy only

## API summary

**Timetable:** daily, weekly, semester, calendar, deadlines, examinations, changes, notifications, cancelled/rescheduled sessions

**Attendance:** summary, subjects, daily, history, shortages, eligibility, export (CSV payload), discrepancy CRUD (own)

## Tests

```bash
cd backend
py -m pytest tests/test_student_phase3.py tests/test_permissions.py -q
```

## Integrations

- Roster (`enrollment_rosters`) defines which course/section rows a student sees
- Faculty display names from `faculty_assignments` + `users`
- Timetable change logs filtered by faculties teaching the student’s courses
