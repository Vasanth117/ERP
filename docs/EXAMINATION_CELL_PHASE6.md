# Examination Cell — Phase 6 (Backend)

## Scope

1. **Result processing & publication** — validate approved workflow, build publication batches, schedule/publish, visibility and withholding.
2. **Transcripts & academic statements** — PDF documents from **published** results only, verification codes, secure download.

Revaluation and supplementary examination workflows are out of scope.

## Authoritative inputs (no conflicting calculation)

| Need | Source |
|------|--------|
| Approved marks/results | Phase 5 `exam_student_subject_results`, `exam_semester_results` (status `approved`) |
| Review gate | `exam_result_approval_workflows` (status `approved`) |
| Credits/GPA/CGPA | Stored on approved semester/subject rows (not recalculated at publish) |
| Policy trace | `policy_id` / `policy_version` copied into publication + documents |

## Cell collections

- `exam_result_publications`, `exam_publication_batches`, `exam_publication_history`, `exam_student_result_visibility`
- `exam_transcripts`, `exam_academic_statements`, `exam_result_documents`, `exam_document_verification_records`

Legacy `semester_result_publications` remains separate; official cell publication uses `exam_result_publications`.

## Permissions

- `examination:publication:read|manage|publish`
- `examination:document:read|generate`
- Students: existing `student:exam_results:read` for own published results/downloads

## API highlights (`/api/v1/examinations/cell`)

- `POST /publications/validate`, `POST /publications`
- `POST /publications/{id}/approve`, `/publish`, `/withhold`, `/release`, `/revise`
- `POST /publications/scheduled/execute`
- `GET /students/me/published-results`
- `POST /documents/generate`, `/generate/bulk`, `/verify`
- `GET /documents/{id}/download`

## Storage

PDFs under LMS storage category `exam_result_documents` (`data/lms/{tenant_id}/exam_result_documents/...`).

Verification: HMAC-SHA256 fragment over `document_id`, `student_user_id`, publication `version` (same pattern as hall tickets).

## Tests

```bash
cd backend
py -m pytest tests/test_examination_cell_phase6.py -q
```

All examination cell phases:

```bash
py -m pytest tests/test_examination_cell_phase*.py -q
```