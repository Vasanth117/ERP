# Student Portal — Phase 4 (CIA + Continuous Assessment)

## Collection ownership

| Data | Owner collection | Student portal |
|------|------------------|----------------|
| Assessments & CIA components | `assessments`, `assessment_components` | Read via roster filter |
| CIA / internal marks | `student_assessment_marks` | **Published only** (`approved`, `locked`) |
| Marks corrections | `marks_correction_requests` | Read where `student_user_id` matches |
| Assignments | `course_assignments` | Published assignments only |
| Submissions | `assignment_submissions` | Read own row; **no student write** in Phase 4 |
| Evaluations / feedback | `assignment_evaluations`, `assignment_feedback` | Published evaluation marks + feedback |
| Quiz schedules | `upcoming_assessments` (`assessment_type` quiz/test) | Filtered by enrollment |
| Grading policy | `grading_policies` | Grade letters on published marks |

### Portal-only collections

| Collection | Purpose |
|------------|---------|
| `student_cia_view_preferences` | Display preferences |
| `student_assignment_progress` | Last viewed + cached status flags |
| `student_assessment_notifications` | Pending evaluation / marks notices |

No `student_quiz_attempts` — quizzes use central assessment + marks until a dedicated Quiz module exists.

## Permissions

- `student:cia:read`
- `student:continuous_assessment:read`

## API routes (prefix `/api/v1/students`)

**CIA:** `/me/cia/schedules`, `/components`, `/marks`, `/marks/subjects`, `/summary`, `/corrections`, `/history`, `/feedback/{assessment_id}/{component_id}`

**Continuous:** `/me/assessments/assignments`, `/quizzes/schedules`, `/marks`, `/progress`, submission + feedback + resubmission-eligibility per assignment

## Security

- Student identity from auth context only
- Roster check `(course_code, section)` for assignments
- Unpublished marks hidden from published endpoints; summary lists `missing` / `unpublished`
- Audit on CIA summary and feedback views

## Tests

```bash
cd backend
py -m pytest tests/test_student_phase4.py tests/test_permissions.py -q
```
