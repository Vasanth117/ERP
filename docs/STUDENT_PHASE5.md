# Student Portal — Phase 5 (Practical / Model Exams + Semester Examinations)

## Module ownership

| Area | Central collections | Student portal |
|------|---------------------|----------------|
| Lab subjects & practical slots | `timetable_entries` (`session_type=laboratory`), `class_sessions`, `examination_schedules` | Read via roster filter |
| Practical marks | `assessments`, `assessment_components`, `student_assessment_marks` | **Published only** (`approved`, `locked`) |
| Model exams | `examination_schedules` (`exam_type` model*), components named `model*` | Published marks only |
| Semester exams | `semester_examination_seasons`, `semester_examination_sessions`, `examination_centres`, `student_examination_eligibility`, `examination_regulations`, `examination_announcements`, `examination_schedule_changes` | Read published data only |
| Corrections | `marks_correction_requests` | Own rows only |

### Portal-only collections

| Collection | Purpose |
|------------|---------|
| `student_examination_preferences` | Calendar / eligibility display prefs |
| `student_examination_notifications` | Student-specific exam notices |

**Not created:** `student_practical_result_views`, `student_model_exam_result_views` — marks are read directly from central assessment collections (same pattern as CIA).

## Permissions

- `student:practical_examination:read`
- `student:semester_examination:read`

## API routes (prefix `/api/v1/students`)

**Practical / lab / model**

- `GET /me/laboratory/subjects`
- `GET /me/practical/schedules`
- `GET /me/practical/components`
- `GET /me/practical/marks`
- `GET /me/practical/marks/unpublished`
- `GET /me/model-examinations/schedules`
- `GET /me/model-examinations/marks`
- `GET /me/practical/feedback/{assessment_id}/{component_id}`
- `GET /me/laboratory/attendance` (requires attendance read)
- `GET /me/practical/history`
- `GET /me/practical/corrections`

**Semester examinations**

- `GET /me/semester-examinations/overview`
- `GET /me/semester-examinations/seasons`
- `GET /me/semester-examinations/calendar`
- `GET /me/semester-examinations/schedules`
- `GET /me/semester-examinations/sessions/{season_id}/{session_code}`
- `GET /me/semester-examinations/centres`
- `GET /me/semester-examinations/instructions`
- `GET /me/semester-examinations/eligibility`
- `GET /me/semester-examinations/regulations`
- `GET /me/semester-examinations/announcements`
- `GET /me/semester-examinations/schedule-changes`
- `GET /me/semester-examinations/history`
- `GET /me/semester-examinations/notifications`

## Security

- Student identity from auth context; roster / course enrollment gates all schedules and sessions
- Eligibility documents must be `published=True` before students can read them
- No student-facing write routes for schedules, eligibility, or marks
- Audit on calendar, eligibility, and practical feedback views

## Tests

```bash
cd backend
py -m pytest tests/test_student_practical_semester_examinations.py tests/test_permissions.py -q
```

Integration tests require MongoDB and Redis.
