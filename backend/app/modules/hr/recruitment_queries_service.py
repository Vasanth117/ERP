"""Read models, workspace, history, reports, and pipeline configuration."""

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.hr.enums import (
    HrApplicationPipelineStage,
    HrEmploymentOfferStatus,
    HrInterviewStatus,
    HrJobRequisitionStatus,
    TERMINAL_APPLICATION_STAGES,
)
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.policy import (
    authorize_hr_recruitment_manage,
    authorize_hr_recruitment_read,
    require_hr_tenant_scope,
)
from app.modules.hr.recruitment_models import (
    HrApplicationReviewNote,
    HrApplicationStageHistory,
    HrCandidate,
    HrEmploymentOffer,
    HrInterviewFeedback,
    HrInterviewSession,
    HrJobApplication,
    HrJobOpening,
    HrJobRequisition,
    HrRecruiterAssignmentHistory,
)
from app.modules.hr.recruitment_repository import HrRecruitmentRepository
from app.modules.hr.recruitment_rules import DEFAULT_PIPELINE_STAGES, assert_stage_transition
from app.modules.hr.recruitment_schemas import (
    ApplicationHistoryItem,
    ApplicationRead,
    ApplicationRequestInfo,
    ApplicationWorkspaceRead,
    CandidateDetailRead,
    CandidateRead,
    ConsolidatedEvaluationRead,
    InterviewDetailRead,
    JobOpeningRead,
    JobRequisitionDetailRead,
    JobRequisitionRead,
    OfferRead,
    OfferRevise,
    PipelineConfigRead,
    PipelineConfigUpdate,
    RecruitmentReportRead,
)
from app.modules.hr.recruitment_service import _record_stage, ensure_pipeline_config, transition_application_stage
from app.modules.hr.recruitment_schemas import ApplicationStageTransition

_repo = HrRecruitmentRepository()


def _skills_overlap(opening: HrJobOpening, candidate: HrCandidate) -> float:
    req_skills = set(s.lower() for s in opening.qualifications.lower().split() if len(s) > 3)
    cand_skills = set(s.lower() for s in candidate.skills)
    if not req_skills:
        return 100.0 if cand_skills else 0.0
    if not cand_skills:
        return 0.0
    overlap = len(req_skills & cand_skills)
    return round(100.0 * overlap / max(len(req_skills), 1), 2)


async def list_job_requisitions(scope: AccessScope, pagination: Pagination, status: str | None = None) -> Page[JobRequisitionRead]:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(HrJobRequisition.tenant_id, tenant_id)]
    if status:
        filters.append(Eq(HrJobRequisition.status, HrJobRequisitionStatus(status)))
    query = HrJobRequisition.find(*filters)
    total = await query.count()
    rows = await query.sort(-HrJobRequisition.created_at).skip(pagination.skip).limit(pagination.limit).to_list()
    return Page(items=[JobRequisitionRead.from_document(r) for r in rows], total=total, page=pagination.page, size=pagination.size)


async def get_job_requisition(scope: AccessScope, requisition_id: str) -> JobRequisitionDetailRead:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(requisition_id, "requisition_id")
    row = await HrJobRequisition.get(rid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Requisition not found", status_code=404)
    progress = await _repo.requisition_progress(tenant_id, row.id)
    return JobRequisitionDetailRead.from_document(row, recruitment_progress=progress)


async def list_job_openings(
    scope: AccessScope,
    pagination: Pagination,
    *,
    requisition_id: str | None = None,
    department_id: str | None = None,
) -> Page[JobOpeningRead]:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(HrJobOpening.tenant_id, tenant_id)]
    if requisition_id:
        filters.append(Eq(HrJobOpening.requisition_id, to_object_id(requisition_id, "requisition_id")))
    if department_id:
        filters.append(Eq(HrJobOpening.department_id, to_object_id(department_id, "department_id")))
    query = HrJobOpening.find(*filters)
    total = await query.count()
    rows = await query.sort(-HrJobOpening.created_at).skip(pagination.skip).limit(pagination.limit).to_list()
    return Page(items=[JobOpeningRead.from_document(r) for r in rows], total=total, page=pagination.page, size=pagination.size)


async def get_job_opening(scope: AccessScope, opening_id: str) -> JobOpeningRead:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    oid = to_object_id(opening_id, "opening_id")
    opening = await HrJobOpening.get(oid)
    if opening is None or opening.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Job opening not found", status_code=404)
    return JobOpeningRead.from_document(opening)


async def list_candidates(scope: AccessScope, pagination: Pagination) -> Page[CandidateRead]:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    query = HrCandidate.find(Eq(HrCandidate.tenant_id, tenant_id))
    total = await query.count()
    rows = await query.sort(-HrCandidate.created_at).skip(pagination.skip).limit(pagination.limit).to_list()
    return Page(items=[CandidateRead.from_document(r) for r in rows], total=total, page=pagination.page, size=pagination.size)


async def get_candidate(scope: AccessScope, candidate_id: str) -> CandidateDetailRead:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    cid = to_object_id(candidate_id, "candidate_id")
    row = await HrCandidate.get(cid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Candidate not found", status_code=404)
    return CandidateDetailRead.from_document(row)


async def get_application_workspace(scope: AccessScope, application_id: str) -> ApplicationWorkspaceRead:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    application = await HrJobApplication.get(aid)
    if application is None or application.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    candidate = await HrCandidate.get(application.candidate_id)
    opening = await HrJobOpening.get(application.job_opening_id)
    if candidate is None or opening is None:
        raise AppError(code="NOT_FOUND", message="Related records missing", status_code=404)
    notes = await HrApplicationReviewNote.find(
        Eq(HrApplicationReviewNote.tenant_id, tenant_id),
        Eq(HrApplicationReviewNote.application_id, application.id),
        Eq(HrApplicationReviewNote.visible_to_candidate, False),
    ).to_list()
    history = await HrApplicationStageHistory.find(
        Eq(HrApplicationStageHistory.tenant_id, tenant_id),
        Eq(HrApplicationStageHistory.application_id, application.id),
    ).sort(-HrApplicationStageHistory.created_at).to_list()
    return ApplicationWorkspaceRead(
        application=ApplicationRead.from_document(application),
        candidate=CandidateDetailRead.from_document(candidate),
        opening=JobOpeningRead.from_document(opening),
        internal_notes=[n.note for n in notes],
        stage_history=[ApplicationHistoryItem.from_document(h) for h in history],
        requirement_fit_percent=_skills_overlap(opening, candidate),
    )


async def get_application_history(scope: AccessScope, application_id: str) -> list[ApplicationHistoryItem]:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    rows = await HrApplicationStageHistory.find(
        Eq(HrApplicationStageHistory.tenant_id, tenant_id),
        Eq(HrApplicationStageHistory.application_id, aid),
    ).sort(-HrApplicationStageHistory.created_at).to_list()
    return [ApplicationHistoryItem.from_document(r) for r in rows]


async def get_recruiter_assignment_history(scope: AccessScope, application_id: str) -> list[dict]:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    rows = await HrRecruiterAssignmentHistory.find(
        Eq(HrRecruiterAssignmentHistory.tenant_id, tenant_id),
        Eq(HrRecruiterAssignmentHistory.application_id, aid),
    ).sort(-HrRecruiterAssignmentHistory.created_at).to_list()
    return [
        {
            "recruiter_user_id": str(r.recruiter_user_id),
            "assigned_by": str(r.assigned_by),
            "assigned_at": r.created_at.isoformat(),
        }
        for r in rows
    ]


async def request_additional_information(scope: AccessScope, application_id: str, payload: ApplicationRequestInfo) -> dict:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    application = await HrJobApplication.get(aid)
    if application is None or application.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    candidate = await HrCandidate.get(application.candidate_id)
    await HrApplicationReviewNote(
        tenant_id=tenant_id,
        application_id=application.id,
        author_id=scope.user_id,
        note=payload.message,
        visible_to_candidate=True,
    ).insert()
    if candidate:
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.recruitment.additional_info",
            aggregate_type="hr_job_application",
            aggregate_id=str(application.id),
            title="Additional information required",
            body=payload.message,
            recipient_email=candidate.email,
            dedupe_key=f"hr:more_info:{application.id}:{utcnow().isoformat()}",
        )
    return {"requested": True}


async def reject_application(scope: AccessScope, application_id: str, reason: str | None = None) -> ApplicationRead:
    from app.modules.hr.recruitment_service import _record_stage, transition_application_stage

    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    application = await HrJobApplication.get(aid)
    if application is None or application.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    if application.stage in TERMINAL_APPLICATION_STAGES:
        raise AppError(code="CONFLICT", message="Application already closed", status_code=409)
    try:
        assert_stage_transition(application.stage, HrApplicationPipelineStage.REJECTED)
        return await transition_application_stage(
            scope,
            application_id,
            ApplicationStageTransition(target_stage=HrApplicationPipelineStage.REJECTED, reason=reason),
        )
    except AppError as exc:
        if exc.code != "VALIDATION_ERROR":
            raise
    await _record_stage(application, HrApplicationPipelineStage.REJECTED, actor_id=scope.user_id, reason=reason)
    application = await HrJobApplication.get(aid)
    assert application is not None
    candidate = await HrCandidate.get(application.candidate_id)
    if candidate:
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.recruitment.rejected",
            aggregate_type="hr_job_application",
            aggregate_id=str(application.id),
            title="Application update",
            body=reason or "Thank you for your interest.",
            recipient_email=candidate.email,
            dedupe_key=f"hr:reject:{application.id}",
        )
    return ApplicationRead.from_document(application)


async def get_pipeline_config(scope: AccessScope) -> PipelineConfigRead:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    doc = await ensure_pipeline_config(tenant_id)
    return PipelineConfigRead(
        stages=doc.stages,
        application_channels=doc.application_channels,
        evaluation_criteria=doc.evaluation_criteria,
        updated_at=doc.updated_at,
    )


async def update_pipeline_config(scope: AccessScope, payload: PipelineConfigUpdate) -> PipelineConfigRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    allowed = {s.value for s in DEFAULT_PIPELINE_STAGES}
    invalid = [s for s in payload.stages if s not in allowed]
    if invalid:
        raise AppError(code="VALIDATION_ERROR", message=f"Unknown pipeline stages: {', '.join(invalid)}", status_code=422)
    doc = await ensure_pipeline_config(tenant_id)
    doc.stages = payload.stages
    if payload.application_channels is not None:
        doc.application_channels = payload.application_channels
    if payload.evaluation_criteria is not None:
        doc.evaluation_criteria = payload.evaluation_criteria
    doc.updated_by = scope.user_id
    doc.updated_at = utcnow()
    await doc.save()
    return PipelineConfigRead(
        stages=doc.stages,
        application_channels=doc.application_channels,
        evaluation_criteria=doc.evaluation_criteria,
        updated_at=doc.updated_at,
    )


async def compare_candidates_for_opening(scope: AccessScope, job_opening_id: str) -> list:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    oid = to_object_id(job_opening_id, "job_opening_id")
    opening = await HrJobOpening.get(oid)
    if opening is None or opening.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Job opening not found", status_code=404)
    apps = await HrJobApplication.find(
        Eq(HrJobApplication.tenant_id, tenant_id),
        Eq(HrJobApplication.job_opening_id, opening.id),
    ).to_list()
    items = []
    for app in apps:
        candidate = await HrCandidate.get(app.candidate_id)
        if not candidate:
            continue
        items.append(
            {
                "application_id": str(app.id),
                "application_code": app.application_code,
                "candidate_id": str(candidate.id),
                "candidate_name": candidate.full_name,
                "stage": app.stage.value,
                "requirement_fit_percent": _skills_overlap(opening, candidate),
            }
        )
    items.sort(key=lambda x: x["requirement_fit_percent"], reverse=True)
    return items


async def withdraw_application(scope: AccessScope, application_id: str, reason: str | None = None) -> ApplicationRead:
    return await transition_application_stage(
        scope,
        application_id,
        ApplicationStageTransition(target_stage=HrApplicationPipelineStage.WITHDRAWN, reason=reason),
    )


async def get_application_recruitment_history(scope: AccessScope, application_id: str):
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    application = await HrJobApplication.get(aid)
    if application is None or application.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    stage_history = await get_application_history(scope, application_id)
    recruiter_assignments = await get_recruiter_assignment_history(scope, application_id)
    interviews = await HrInterviewSession.find(
        Eq(HrInterviewSession.tenant_id, tenant_id),
        Eq(HrInterviewSession.application_id, aid),
    ).to_list()
    feedback = await HrInterviewFeedback.find(Eq(HrInterviewFeedback.tenant_id, tenant_id), Eq(HrInterviewFeedback.application_id, aid)).to_list()
    offers = await HrEmploymentOffer.find(Eq(HrEmploymentOffer.tenant_id, tenant_id), Eq(HrEmploymentOffer.application_id, aid)).to_list()
    return {
        "stage_history": stage_history,
        "recruiter_assignments": recruiter_assignments,
        "interviews": [
            {
                "interview_id": str(i.id),
                "interview_code": i.interview_code,
                "scheduled_at": i.scheduled_at.isoformat(),
                "status": i.status.value,
            }
            for i in interviews
        ],
        "interview_feedback": [
            {
                "feedback_id": str(f.id),
                "interviewer_id": str(f.interviewer_id),
                "recommendation": f.recommendation,
                "criteria_scores": f.criteria_scores,
            }
            for f in feedback
        ],
        "offers": [
            {
                "offer_id": str(o.id),
                "offer_code": o.offer_code,
                "status": o.status.value,
                "issued_at": o.issued_at.isoformat() if o.issued_at else None,
            }
            for o in offers
        ],
    }


async def cancel_interview(scope: AccessScope, interview_id: str, reason: str) -> InterviewDetailRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    iid = to_object_id(interview_id, "interview_id")
    session = await HrInterviewSession.get(iid)
    if session is None or session.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Interview not found", status_code=404)
    session.status = HrInterviewStatus.CANCELLED
    session.reschedule_reason = reason
    session.updated_at = utcnow()
    await session.save()
    application = await HrJobApplication.get(session.application_id)
    candidate = await HrCandidate.get(application.candidate_id) if application else None
    if candidate:
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.recruitment.interview_cancelled",
            aggregate_type="hr_interview",
            aggregate_id=str(session.id),
            title="Interview cancelled",
            body=reason,
            recipient_email=candidate.email,
            dedupe_key=f"hr:interview_cancel:{session.id}",
        )
    return await get_interview_detail(scope, interview_id)


async def get_interview_detail(scope: AccessScope, interview_id: str) -> InterviewDetailRead:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    iid = to_object_id(interview_id, "interview_id")
    session = await HrInterviewSession.get(iid)
    if session is None or session.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Interview not found", status_code=404)
    from app.authorization.permissions import Permission

    is_assigned = scope.user_id in session.interviewer_ids or scope.user_id in session.panel_member_ids
    is_hr_manager = Permission.HR_RECRUITMENT_MANAGE in scope.effective_permissions or Permission.HR_ADMIN_MANAGE in scope.effective_permissions
    if not is_assigned and not is_hr_manager:
        raise AppError(code="FORBIDDEN", message="Interview not assigned to you", status_code=403)

    application = await HrJobApplication.get(session.application_id)
    candidate = await HrCandidate.get(application.candidate_id) if application else None
    feedback = await HrInterviewFeedback.find(
        Eq(HrInterviewFeedback.tenant_id, tenant_id),
        Eq(HrInterviewFeedback.interview_id, session.id),
    ).to_list()
    cand_view = None
    if candidate and (is_hr_manager or is_assigned):
        cand_view = CandidateDetailRead.from_document(candidate) if is_hr_manager else CandidateRead.from_document(candidate)
    return InterviewDetailRead.from_session(session, candidate=cand_view, feedback_count=len(feedback))


async def list_interviews_for_application(scope: AccessScope, application_id: str) -> list[InterviewDetailRead]:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    sessions = await HrInterviewSession.find(
        Eq(HrInterviewSession.tenant_id, tenant_id),
        Eq(HrInterviewSession.application_id, aid),
    ).sort(-HrInterviewSession.scheduled_at).to_list()
    out: list[InterviewDetailRead] = []
    for session in sessions:
        out.append(await get_interview_detail(scope, str(session.id)))
    return out


async def consolidate_application_evaluation(scope: AccessScope, application_id: str) -> ConsolidatedEvaluationRead:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    sessions = await HrInterviewSession.find(
        Eq(HrInterviewSession.tenant_id, tenant_id),
        Eq(HrInterviewSession.application_id, aid),
    ).to_list()
    session_ids = [s.id for s in sessions]
    feedback_rows: list[HrInterviewFeedback] = []
    if session_ids:
        feedback_rows = await HrInterviewFeedback.find(Eq(HrInterviewFeedback.tenant_id, tenant_id)).to_list()
        feedback_rows = [f for f in feedback_rows if f.interview_id in session_ids]
    criteria_totals: dict[str, list[float]] = {}
    recommendations: list[str] = []
    for fb in feedback_rows:
        recommendations.append(fb.recommendation)
        for key, score in fb.criteria_scores.items():
            criteria_totals.setdefault(key, []).append(score)
    averaged = {k: round(sum(v) / len(v), 2) for k, v in criteria_totals.items()}
    positive = sum(1 for r in recommendations if r in {"hire", "strong_hire", "yes"})
    decision = "proceed" if positive >= max(1, len(recommendations) // 2) else "hold"
    return ConsolidatedEvaluationRead(
        application_id=application_id,
        feedback_count=len(feedback_rows),
        averaged_scores=averaged,
        recommendations=recommendations,
        suggested_decision=decision,
    )


async def list_offers(scope: AccessScope, pagination: Pagination, application_id: str | None = None) -> Page[OfferRead]:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(HrEmploymentOffer.tenant_id, tenant_id)]
    if application_id:
        filters.append(Eq(HrEmploymentOffer.application_id, to_object_id(application_id, "application_id")))
    query = HrEmploymentOffer.find(*filters)
    total = await query.count()
    rows = await query.sort(-HrEmploymentOffer.created_at).skip(pagination.skip).limit(pagination.limit).to_list()
    return Page(items=[OfferRead.from_document(r) for r in rows], total=total, page=pagination.page, size=pagination.size)


async def revise_offer(scope: AccessScope, offer_id: str, payload: OfferRevise) -> OfferRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    oid = to_object_id(offer_id, "offer_id")
    offer = await HrEmploymentOffer.get(oid)
    if offer is None or offer.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Offer not found", status_code=404)
    if offer.status not in {HrEmploymentOfferStatus.DRAFT, HrEmploymentOfferStatus.APPROVED}:
        raise AppError(code="CONFLICT", message="Offer cannot be revised", status_code=409)
    if payload.designation is not None:
        offer.designation = payload.designation
    if payload.salary_details is not None:
        offer.salary_details = payload.salary_details
    if payload.expected_joining_date is not None:
        offer.expected_joining_date = payload.expected_joining_date
    if payload.offer_valid_until is not None:
        offer.offer_valid_until = payload.offer_valid_until
    if offer.status == HrEmploymentOfferStatus.APPROVED:
        offer.status = HrEmploymentOfferStatus.DRAFT
        offer.approved_by = None
        offer.approved_at = None
    offer.updated_at = utcnow()
    await offer.save()
    return OfferRead.from_document(offer)


async def recruitment_reports(scope: AccessScope) -> RecruitmentReportRead:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    return RecruitmentReportRead(
        department_application_counts=await _repo.department_application_counts(tenant_id),
        opening_performance=await _repo.opening_performance(tenant_id),
        time_to_fill=await _repo.time_to_fill_days(tenant_id),
        recruitment_sources=await _repo.recruitment_source_breakdown(tenant_id),
    )


async def log_recruiter_assignment(
    tenant_id: PydanticObjectId,
    application_id: PydanticObjectId,
    recruiter_id: PydanticObjectId,
    assigned_by: PydanticObjectId,
) -> None:
    await HrRecruiterAssignmentHistory(
        tenant_id=tenant_id,
        application_id=application_id,
        recruiter_user_id=recruiter_id,
        assigned_by=assigned_by,
    ).insert()