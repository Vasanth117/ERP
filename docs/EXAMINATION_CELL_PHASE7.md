# Examination Cell — Phase 7 (Backend)

## Scope

1. **Revaluation & supplementary** — applications linked to approved published results, fee verification, evaluator assignment, approved mark changes with history, GPA recalculation, revised publication.
2. **Incidents & malpractice** — investigation workflow, evidence references, disciplinary decisions, optional result withholding.

Does not replace Finance or full Student Management modules.

## Authoritative inputs

| Need | Source |
|------|--------|
| Published results | `exam_student_subject_results` (status `approved`) + `exam_result_publications` |
| Fees | `examination_review_windows`, `examination_review_fee_payments` |
| Arrear eligibility | `student_arrear_references` |
| Exam registration (supplementary) | Existing `exam_registrations` via registration service |

Original published rows are preserved in `exam_revaluation_history.before_snapshot`; approved changes move subject results to `provisional` and trigger recalculation + `revise_publication`.

## Collections

- `exam_revaluation_applications`, `exam_revaluation_evaluations`, `exam_revaluation_approvals`, `exam_revaluation_history`
- `exam_supplementary_registrations`, `exam_supplementary_attempts`
- `exam_incident_records`, `exam_malpractice_cases`, `exam_incident_evidence`, `exam_investigation_records`, `exam_disciplinary_decisions`, `exam_incident_history`

## Permissions

- `examination:revaluation:read|manage`
- `examination:supplementary:read|manage`
- `examination:incident:read|manage|investigate` (restricted case/evidence access)

## API highlights (`/api/v1/examinations/cell`)

**Revaluation**
- `POST /revaluation/applications`
- `POST .../assign-evaluator`, `/evaluation`, `/decide`

**Supplementary**
- `GET /supplementary/students/{id}/eligibility`
- `POST /supplementary/registrations`

**Incidents**
- `POST /incidents`, `POST /malpractice/cases`
- `GET /malpractice/cases/{id}` (investigator/manage only)
- `POST .../assign-investigator`, `/statements`, `/findings`, `/disciplinary-decisions`
- `POST /incidents/{id}/evidence`

## Tests

```bash
cd backend
py -m pytest tests/test_examination_cell_phase7.py -q
```

Full cell suite:

```bash
py -m pytest tests/test_examination_cell_phase*.py -q
```