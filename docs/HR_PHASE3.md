# HR Staff — Phase 3 (Recruitment & Onboarding)

Implements **Module 5** and **Module 6** from the HR Staff backend spec, aligned with `backend_and_frontend.md`:

`routes` (`recruitment_router.py`, `onboarding_router.py`) → `services` (`recruitment_service.py`, `recruitment_queries_service.py`, `onboarding_service.py`) → `repository` (`recruitment_repository.py`) → Beanie `models`.

## Requirement coverage

| Spec area | Backend behaviour |
|-----------|-------------------|
| Recruitment dashboard | Full KPI set (requisitions, assessment, awaiting feedback, withdrawn, offer pending) + filters (department, campus, opening, requisition, job title, stage, period) |
| Application channels | Approved sources on pipeline config; `POST /recruitment/channel-applications` with `hr:recruitment:channel_apply` |
| Candidate comparison | `GET /recruitment/openings/{id}/candidate-comparison` |
| Offer lifecycle | `submit_approval` → approve → issue; `remind`; expiry on accept |
| Evaluation | Configurable criteria on pipeline config; validated on interview feedback |
| Recruitment history | `GET /applications/{id}/recruitment-history` (stages, recruiters, interviews, feedback, offers) |
| Job requisitions | CRUD list/get, full fields, submit, HR + management approval with notes |
| Requisition progress | Embedded in `GET /requisitions/{id}` via repository |
| Job openings | List/get, create from approved requisition, edit, publish/pause/close |
| Candidates | Upsert (dedupe email), list/get, resume + supporting docs + employment history |
| Applications | Create (no duplicate per opening), list, workspace (profile + fit %), stage transitions |
| Pipeline | Configurable stages `GET/PUT /pipeline-config`; transitions enforced in `recruitment_rules.py` |
| Review | Internal notes, assign recruiter + assignment history, request info, reject |
| Interviews | Schedule, reschedule, cancel, feedback, interviewer-scoped detail, “mine” list |
| Evaluation | Consolidated scores/recommendations per application |
| Offers | Create, approve, issue, accept/decline/withdraw, revise, expiry check, no employee until onboarding |
| Communication | Outbox events for ack, shortlist, interview, offer, rejection, selection, onboarding |
| Reports | `GET /recruitment/reports` — department counts, opening performance, time-to-fill, sources |
| Onboarding overview | `GET /onboarding/overview` |
| Checklists | Template upsert/list by employee category; tasks auto-spawned |
| Tasks | List per process, employee `GET /onboarding/tasks/mine`, status updates, overdue from dates |
| Documents | Mandatory codes verified via `HrEmployeeDocument` at completion |
| Completion | Mandatory tasks + documents; authorized waivers; welcome notification; activity log |
| Post-onboarding | Employee record via `register_employee`; legacy checklist sync; probation dates on profile at completion |
| Onboarding completion flow | `submit-completion` (PENDING_COMPLETION) → `complete`; auto overdue task status; pending approvals in overview |

## Permissions

`hr:recruitment:read|manage|approve`, `hr:onboarding:read|manage|complete` on `HR_STAFF`.

## Tests

```bash
cd backend
py -m pytest tests/test_hr_phase1.py tests/test_hr_phase2.py tests/test_hr_phase3.py -q
```

## Collections

`hr_job_requisitions`, `hr_job_openings`, `hr_candidates`, `hr_job_applications`, `hr_application_stage_history`, `hr_application_review_notes`, `hr_recruiter_assignment_history`, `hr_interview_sessions`, `hr_interview_feedback`, `hr_employment_offers`, `hr_recruitment_pipeline_config`, `hr_onboarding_checklist_templates`, `hr_onboarding_processes`, `hr_onboarding_tasks`, `hr_onboarding_waivers`