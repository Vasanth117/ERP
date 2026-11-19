# Examination Cell — Phase 5 (Backend)

## Scope

1. **Grading policy & GPA/CGPA** — versioned policies, grade boundaries, provisional calculation from approved marks.
2. **Result review & approval** — department review, exam cell verification, approval with audit history.

Official result publication and transcripts are **not** in scope.

## Authoritative data

| Need | Source |
|------|--------|
| Approved marks | `exam_marks_submissions` / `exam_marks_entries` |
| Credit units | `course_catalog_references` |
| Session context | `exam_sessions` |
| Assessment thresholds | `exam_assessment_configs` (reference only) |

## Cell collections

- `exam_grading_policies`, `exam_grade_boundaries`, `exam_grading_policy_versions`
- `exam_student_subject_results`, `exam_semester_results`, `exam_gpa_calculations`, `exam_cgpa_calculations`
- `exam_result_review_records`, `exam_result_approval_workflows`, `exam_result_review_history`

Each calculation stores `policy_id`, `policy_version`, `calculation_inputs`, and timestamps for audit replay.

## Permissions

- `examination:grading:read|manage`
- `examination:result:review|approve`

## API highlights (`/api/v1/examinations/cell`)

- `POST /grading-policies`, `POST /grading-policies/{id}/activate`
- `POST /results/provisional/calculate`
- `GET /sessions/{id}/subject-results`, `/semester-results`
- `POST /results/review/start`
- `POST /results/workflows/{id}/department-comment`, `/verify`, `/approve`, `/resubmit`
- `GET /sessions/{id}/results/summary`, `/results/review-history`

## Tests

```bash
cd backend
py -m pytest tests/test_examination_cell_phase5.py -q
```

Full examination cell suite (phases 1–5):

```bash
py -m pytest tests/test_examination_cell_phase*.py -q
```