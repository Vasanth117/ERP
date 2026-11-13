# Student Portal — Phase 7 (Grades, GPA/CGPA, Academic Documents)

## Central authority (reuse, do not duplicate)

| Data | Collection | Student portal |
|------|------------|----------------|
| Grading policy | `grading_policies` | Via `examinations/grading.py` + `grading_gpa.py` |
| Published results | `semester_result_publications`, `semester_result_subject_marks` | Read + **recompute** GPA/CGPA for display |
| Official documents | `academic_document_publications` | References + download tokens only |

**Not created:** `student_gpa_cgpa_snapshots`, `student_grade_summary_views`, `student_credit_summary_views` — values derived from authoritative published results and `student_academic_records`.

### Student collections

| Collection | Purpose |
|------------|---------|
| `student_marksheet_references` | Last viewed marksheets |
| `student_grade_card_references` | Per-season grade card pointer |
| `student_transcript_references` | Transcript pointer |
| `student_academic_document_requests` | Reissue / transcript requests |
| `student_document_download_logs` | Download audit |

## Permissions

- `student:grades:read`
- `student:academic_documents:read`
- `student:academic_documents:request`

## API routes (prefix `/api/v1/students`)

**Grades & GPA**

- `GET /me/grades/subjects`
- `GET /me/grades/gpa/semester/{season_id}`
- `GET /me/grades/gpa/cumulative`
- `GET /me/grades/performance`
- `GET /me/grades/history`
- `GET /me/grades/credits`
- `GET /me/grades/standing`
- `GET /me/grades/gpa/breakdown`

**Documents**

- `GET /me/academic-documents/grade-cards`
- `GET /me/academic-documents/marksheets`
- `GET /me/academic-documents/transcript`
- `GET /me/academic-documents/history`
- `POST /me/academic-documents/requests`
- `GET /me/academic-documents/requests/{request_id}`
- `GET /me/academic-documents/{document_id}`
- `POST /me/academic-documents/{document_id}/download`

## Security

- Published marks and documents only
- GPA/CGPA recalculated from published lines using tenant `grading_policies` (grade bands may include `points`)
- No student write on grades or official documents
- Expiring download tokens; `storage_token` on central documents required for download
- Audit on GPA breakdown view and document download

## Tests

```bash
cd backend
py -m pytest tests/test_student_grades_documents.py tests/test_permissions.py -q
```
