"""HR recruitment and applicant tracking services."""

from datetime import date, datetime
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.hr.employee_sync import log_hr_activity
from app.modules.hr.enums import (
    HrApplicationPipelineStage,
    HrEmploymentOfferStatus,
    HrInterviewStatus,
    HrJobOpeningStatus,
    HrJobRequisitionStatus,
    HrStaffActivityType,
)
from app.modules.hr.hr_notification_dispatch import enqueue_hr_notification
from app.modules.hr.policy import (
    authorize_hr_recruitment_approve,
    authorize_hr_recruitment_manage,
    authorize_hr_recruitment_manage_or_channel,
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
    HrRecruitmentPipelineConfig,
)
from app.modules.hr.recruitment_rules import DEFAULT_PIPELINE_STAGES, assert_stage_enabled, assert_stage_transition
from app.modules.hr.recruitment_schemas import (
    ApplicationAssignRecruiter,
    ApplicationCreate,
    ApplicationRead,
    ApplicationReviewNoteCreate,
    ApplicationStageTransition,
    CandidateRead,
    CandidateUpsert,
    InterviewFeedbackSubmit,
    InterviewRead,
    InterviewReschedule,
    InterviewSchedule,
    JobOpeningCreate,
    JobOpeningRead,
    JobOpeningUpdate,
    JobRequisitionCreate,
    JobRequisitionRead,
    OfferCreate,
    OfferDecision,
    OfferRead,
    RecruitmentDashboardFilters,
    RecruitmentDashboardStats,
    RequisitionDecision,
)
from app.modules.tenants.models import Department


async def _validate_department(tenant_id: PydanticObjectId, department_id: PydanticObjectId) -> Department:
    dept = await Department.get(department_id)
    if dept is None or dept.tenant_id != tenant_id:
        raise AppError(code="VALIDATION_ERROR", message="Invalid department", status_code=422)
    return dept


async def _record_stage(application: HrJobApplication, to_stage: HrApplicationPipelineStage, *, actor_id, reason: str | None) -> None:
    from_stage = application.stage.value
    application.stage = to_stage
    application.updated_at = utcnow()
    await application.save()
    await HrApplicationStageHistory(
        tenant_id=application.tenant_id,
        application_id=application.id,
        from_stage=from_stage,
        to_stage=to_stage.value,
        reason=reason,
        actor_id=actor_id,
    ).insert()


async def ensure_pipeline_config(tenant_id: PydanticObjectId) -> HrRecruitmentPipelineConfig:
    from app.modules.hr.recruitment_models import DEFAULT_APPLICATION_CHANNELS, DEFAULT_EVALUATION_CRITERIA

    doc = await HrRecruitmentPipelineConfig.find_one(Eq(HrRecruitmentPipelineConfig.tenant_id, tenant_id))
    if doc is None:
        doc = HrRecruitmentPipelineConfig(
            tenant_id=tenant_id,
            stages=[s.value for s in DEFAULT_PIPELINE_STAGES],
            application_channels=list(DEFAULT_APPLICATION_CHANNELS),
            evaluation_criteria=list(DEFAULT_EVALUATION_CRITERIA),
        )
        await doc.insert()
    return doc


async def _validate_application_channel(tenant_id: PydanticObjectId, channel: str) -> None:
    cfg = await ensure_pipeline_config(tenant_id)
    normalized = channel.strip().lower()
    allowed = {c.lower() for c in cfg.application_channels}
    if normalized not in allowed:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Application channel '{channel}' is not approved for this institution",
            status_code=422,
        )


async def create_job_requisition(scope: AccessScope, payload: JobRequisitionCreate) -> JobRequisitionRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    dept_id = to_object_id(payload.department_id, "department_id")
    await _validate_department(tenant_id, dept_id)
    code = payload.requisition_code.strip()
    if await HrJobRequisition.find_one(Eq(HrJobRequisition.tenant_id, tenant_id), Eq(HrJobRequisition.requisition_code, code)):
        raise AppError(code="CONFLICT", message="Requisition code already exists", status_code=409)
    campus_id = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    work_loc = to_object_id(payload.work_location_id, "work_location_id") if payload.work_location_id else None
    row = HrJobRequisition(
        tenant_id=tenant_id,
        requisition_code=code,
        job_title=payload.job_title.strip(),
        department_id=dept_id,
        campus_id=campus_id,
        positions_required=payload.positions_required,
        employment_type=payload.employment_type.strip(),
        work_location_id=work_loc,
        job_description=payload.job_description,
        qualifications=payload.qualifications,
        skills=payload.skills,
        experience_requirements=payload.experience_requirements,
        salary_range=payload.salary_range,
        reason_for_hiring=payload.reason_for_hiring,
        expected_joining_date=payload.expected_joining_date,
        hiring_priority=payload.hiring_priority,
        requested_by=to_object_id(payload.requested_by_user_id, "requested_by_user_id")
        if payload.requested_by_user_id
        else scope.user_id,
        actor_id=scope.user_id,
    )
    await row.insert()
    return JobRequisitionRead.from_document(row)


async def submit_job_requisition(scope: AccessScope, requisition_id: str) -> JobRequisitionRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(requisition_id, "requisition_id")
    row = await HrJobRequisition.get(rid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Requisition not found", status_code=404)
    if row.status not in {HrJobRequisitionStatus.DRAFT, HrJobRequisitionStatus.RETURNED_FOR_CLARIFICATION}:
        raise AppError(code="CONFLICT", message="Requisition cannot be submitted", status_code=409)
    row.status = HrJobRequisitionStatus.HR_REVIEW
    row.updated_at = utcnow()
    await row.save()
    return JobRequisitionRead.from_document(row)


async def review_job_requisition(scope: AccessScope, requisition_id: str, payload: RequisitionDecision) -> JobRequisitionRead:
    tenant_id = require_hr_tenant_scope(scope)
    rid = to_object_id(requisition_id, "requisition_id")
    row = await HrJobRequisition.get(rid)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Requisition not found", status_code=404)

    if payload.decision == "hr_approve":
        authorize_hr_recruitment_manage(scope)
        if row.status not in {HrJobRequisitionStatus.SUBMITTED, HrJobRequisitionStatus.HR_REVIEW}:
            raise AppError(code="CONFLICT", message="Requisition is not awaiting HR review", status_code=409)
        row.status = HrJobRequisitionStatus.PENDING_MANAGEMENT_APPROVAL
        row.hr_review_note = payload.note
        row.approved_position_ref = payload.approved_position_ref
    elif payload.decision == "return":
        authorize_hr_recruitment_manage(scope)
        row.status = HrJobRequisitionStatus.RETURNED_FOR_CLARIFICATION
        row.hr_review_note = payload.note
    elif payload.decision == "approve":
        authorize_hr_recruitment_approve(scope)
        if row.status != HrJobRequisitionStatus.PENDING_MANAGEMENT_APPROVAL:
            raise AppError(code="CONFLICT", message="Requisition is not pending management approval", status_code=409)
        row.status = HrJobRequisitionStatus.APPROVED
        row.management_decision_note = payload.note
    elif payload.decision == "reject":
        authorize_hr_recruitment_approve(scope)
        row.status = HrJobRequisitionStatus.REJECTED
        row.management_decision_note = payload.note
    else:
        raise AppError(code="VALIDATION_ERROR", message="Invalid decision", status_code=422)

    row.updated_at = utcnow()
    row.actor_id = scope.user_id
    await row.save()
    return JobRequisitionRead.from_document(row)


async def create_job_opening(scope: AccessScope, payload: JobOpeningCreate) -> JobOpeningRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    req_id = to_object_id(payload.requisition_id, "requisition_id")
    req = await HrJobRequisition.get(req_id)
    if req is None or req.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Requisition not found", status_code=404)
    if req.status != HrJobRequisitionStatus.APPROVED:
        raise AppError(code="CONFLICT", message="Requisition must be approved", status_code=409)
    code = payload.opening_code.strip()
    if await HrJobOpening.find_one(Eq(HrJobOpening.tenant_id, tenant_id), Eq(HrJobOpening.opening_code, code)):
        raise AppError(code="CONFLICT", message="Opening code already exists", status_code=409)
    vacancies = payload.vacancies or req.positions_required
    opening = HrJobOpening(
        tenant_id=tenant_id,
        opening_code=code,
        requisition_id=req.id,
        job_title=req.job_title,
        department_id=req.department_id,
        campus_id=req.campus_id,
        vacancies=vacancies,
        application_deadline=payload.application_deadline,
        job_description=req.job_description,
        qualifications=req.qualifications,
        selection_criteria=payload.selection_criteria,
        interview_stages=payload.interview_stages,
        actor_id=scope.user_id,
    )
    await opening.insert()
    return JobOpeningRead.from_document(opening)


async def update_job_opening(scope: AccessScope, opening_id: str, payload: JobOpeningUpdate) -> JobOpeningRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    oid = to_object_id(opening_id, "opening_id")
    opening = await HrJobOpening.get(oid)
    if opening is None or opening.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Job opening not found", status_code=404)
    if opening.status not in {HrJobOpeningStatus.DRAFT, HrJobOpeningStatus.PAUSED, HrJobOpeningStatus.PUBLISHED}:
        raise AppError(code="CONFLICT", message="Opening cannot be edited", status_code=409)
    if payload.job_description is not None:
        opening.job_description = payload.job_description
    if payload.qualifications is not None:
        opening.qualifications = payload.qualifications
    if payload.selection_criteria is not None:
        opening.selection_criteria = payload.selection_criteria
    if payload.interview_stages is not None:
        opening.interview_stages = payload.interview_stages
    if payload.application_deadline is not None:
        opening.application_deadline = payload.application_deadline
    if payload.vacancies is not None:
        opening.vacancies = payload.vacancies
    opening.updated_at = utcnow()
    await opening.save()
    return JobOpeningRead.from_document(opening)


async def set_job_opening_status(scope: AccessScope, opening_id: str, status: HrJobOpeningStatus) -> JobOpeningRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    oid = to_object_id(opening_id, "opening_id")
    opening = await HrJobOpening.get(oid)
    if opening is None or opening.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Job opening not found", status_code=404)
    if status == HrJobOpeningStatus.PUBLISHED:
        opening.published_at = utcnow()
    elif status in {HrJobOpeningStatus.CLOSED_FILLED, HrJobOpeningStatus.CLOSED_CANCELLED}:
        terminal = {
            HrApplicationPipelineStage.OFFER_ACCEPTED,
            HrApplicationPipelineStage.REJECTED,
            HrApplicationPipelineStage.WITHDRAWN,
            HrApplicationPipelineStage.POSITION_CLOSED,
        }
        apps_to_close = await HrJobApplication.find(
            Eq(HrJobApplication.tenant_id, tenant_id),
            Eq(HrJobApplication.job_opening_id, opening.id),
        ).to_list()
        for app in apps_to_close:
            if app.stage not in terminal:
                await _record_stage(
                    app,
                    HrApplicationPipelineStage.POSITION_CLOSED,
                    actor_id=scope.user_id,
                    reason=f"Opening {status.value}",
                )
    opening.status = status
    opening.updated_at = utcnow()
    await opening.save()
    return JobOpeningRead.from_document(opening)


async def upsert_candidate(scope: AccessScope, payload: CandidateUpsert) -> CandidateRead:
    authorize_hr_recruitment_manage_or_channel(scope)
    tenant_id = require_hr_tenant_scope(scope)
    email_norm = str(payload.email).strip().lower()
    existing = await HrCandidate.find_one(
        Eq(HrCandidate.tenant_id, tenant_id),
        Eq(HrCandidate.email_normalized, email_norm),
    )
    if existing:
        existing.full_name = payload.full_name.strip()
        existing.phone = payload.phone
        existing.address = payload.address
        existing.qualifications = payload.qualifications
        existing.work_experience = payload.work_experience
        existing.previous_employment = payload.previous_employment
        existing.skills = payload.skills
        if payload.resume_file_ref:
            existing.resume_file_ref = payload.resume_file_ref
        if payload.supporting_document_refs:
            existing.metadata = {**existing.metadata, "supporting_document_refs": payload.supporting_document_refs}
        existing.updated_at = utcnow()
        await existing.save()
        return CandidateRead.from_document(existing)
    row = HrCandidate(
        tenant_id=tenant_id,
        full_name=payload.full_name.strip(),
        email=str(payload.email).strip(),
        email_normalized=email_norm,
        phone=payload.phone,
        address=payload.address,
        qualifications=payload.qualifications,
        work_experience=payload.work_experience,
        previous_employment=payload.previous_employment,
        skills=payload.skills,
        resume_file_ref=payload.resume_file_ref,
        metadata={"supporting_document_refs": payload.supporting_document_refs},
    )
    await row.insert()
    return CandidateRead.from_document(row)


async def create_application(scope: AccessScope, payload: ApplicationCreate) -> ApplicationRead:
    authorize_hr_recruitment_manage_or_channel(scope)
    tenant_id = require_hr_tenant_scope(scope)
    opening_id = to_object_id(payload.job_opening_id, "job_opening_id")
    candidate_id = to_object_id(payload.candidate_id, "candidate_id")
    opening = await HrJobOpening.get(opening_id)
    if opening is None or opening.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Job opening not found", status_code=404)
    if opening.status != HrJobOpeningStatus.PUBLISHED:
        raise AppError(code="CONFLICT", message="Job opening is not accepting applications", status_code=409)
    if opening.application_deadline and opening.application_deadline < utcnow():
        raise AppError(code="CONFLICT", message="Application deadline has passed", status_code=409)
    candidate = await HrCandidate.get(candidate_id)
    if candidate is None or candidate.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Candidate not found", status_code=404)
    if await HrJobApplication.find_one(
        Eq(HrJobApplication.tenant_id, tenant_id),
        Eq(HrJobApplication.job_opening_id, opening_id),
        Eq(HrJobApplication.candidate_id, candidate_id),
    ):
        raise AppError(code="CONFLICT", message="Duplicate application for this opening", status_code=409)
    await _validate_application_channel(tenant_id, payload.application_source)

    app_code = f"APP-{uuid4().hex[:10].upper()}"
    application = HrJobApplication(
        tenant_id=tenant_id,
        application_code=app_code,
        job_opening_id=opening.id,
        candidate_id=candidate.id,
        requisition_id=opening.requisition_id,
        department_id=opening.department_id,
        campus_id=opening.campus_id,
        application_source=payload.application_source,
        document_refs=payload.document_refs,
        actor_id=scope.user_id,
    )
    await application.insert()
    await enqueue_hr_notification(
        tenant_id,
        event_type="hr.recruitment.application_ack",
        aggregate_type="hr_job_application",
        aggregate_id=str(application.id),
        title="Application received",
        body=f"Your application {app_code} has been received.",
        recipient_email=candidate.email,
        dedupe_key=f"hr:app_ack:{application.id}",
    )
    await log_hr_activity(
        tenant_id,
        HrStaffActivityType.RECRUITMENT_UPDATE,
        f"Application {app_code} created",
        actor_id=scope.user_id,
        department_id=opening.department_id,
        resource_type="hr_job_application",
        resource_id=str(application.id),
        status_label=application.stage.value,
    )
    return ApplicationRead.from_document(application)


async def transition_application_stage(
    scope: AccessScope,
    application_id: str,
    payload: ApplicationStageTransition,
) -> ApplicationRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    application = await HrJobApplication.get(aid)
    if application is None or application.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    cfg = await ensure_pipeline_config(tenant_id)
    assert_stage_enabled(cfg.stages, payload.target_stage)
    assert_stage_transition(application.stage, payload.target_stage)
    await _record_stage(application, payload.target_stage, actor_id=scope.user_id, reason=payload.reason)
    candidate = await HrCandidate.get(application.candidate_id)
    if candidate and payload.target_stage == HrApplicationPipelineStage.SHORTLISTED:
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.recruitment.shortlisted",
            aggregate_type="hr_job_application",
            aggregate_id=str(application.id),
            title="Application shortlisted",
            body=f"Your application {application.application_code} has been shortlisted.",
            recipient_email=candidate.email,
            dedupe_key=f"hr:shortlist:{application.id}",
        )
    if candidate and payload.target_stage == HrApplicationPipelineStage.REJECTED:
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.recruitment.rejected",
            aggregate_type="hr_job_application",
            aggregate_id=str(application.id),
            title="Application update",
            body=payload.reason or "Thank you for your interest.",
            recipient_email=candidate.email,
            dedupe_key=f"hr:reject:{application.id}",
        )
    if candidate and payload.target_stage == HrApplicationPipelineStage.WITHDRAWN:
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.recruitment.withdrawn",
            aggregate_type="hr_job_application",
            aggregate_id=str(application.id),
            title="Application withdrawn",
            body=payload.reason or "Application has been withdrawn.",
            recipient_email=candidate.email,
            dedupe_key=f"hr:withdraw:{application.id}",
        )
    if candidate and payload.target_stage == HrApplicationPipelineStage.SELECTED:
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.recruitment.selected",
            aggregate_type="hr_job_application",
            aggregate_id=str(application.id),
            title="Selection update",
            body=f"Your application {application.application_code} has been selected.",
            recipient_email=candidate.email,
            dedupe_key=f"hr:selected:{application.id}",
        )
    return ApplicationRead.from_document(application)


async def create_application_via_channel(
    scope: AccessScope,
    *,
    job_opening_id: str,
    candidate: CandidateUpsert,
    application_source: str,
    document_refs: list[str] | None = None,
) -> ApplicationRead:
    from app.modules.hr.policy import authorize_hr_recruitment_channel_apply

    authorize_hr_recruitment_channel_apply(scope)
    cand = await upsert_candidate(scope, candidate)
    return await create_application(
        scope,
        ApplicationCreate(
            job_opening_id=job_opening_id,
            candidate_id=cand.id,
            application_source=application_source,
            document_refs=document_refs or [],
        ),
    )


async def add_review_note(scope: AccessScope, application_id: str, payload: ApplicationReviewNoteCreate) -> dict:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    application = await HrJobApplication.get(aid)
    if application is None or application.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    note = HrApplicationReviewNote(
        tenant_id=tenant_id,
        application_id=application.id,
        author_id=scope.user_id,
        note=payload.note,
        visible_to_candidate=payload.visible_to_candidate,
    )
    await note.insert()
    return {"note_id": str(note.id)}


async def assign_recruiter(scope: AccessScope, application_id: str, payload: ApplicationAssignRecruiter) -> ApplicationRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    aid = to_object_id(application_id, "application_id")
    recruiter_id = to_object_id(payload.recruiter_user_id, "recruiter_user_id")
    application = await HrJobApplication.get(aid)
    if application is None or application.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    application.assigned_recruiter_id = recruiter_id
    application.updated_at = utcnow()
    await application.save()
    from app.modules.hr.recruitment_queries_service import log_recruiter_assignment

    await log_recruiter_assignment(tenant_id, application.id, recruiter_id, scope.user_id)
    return ApplicationRead.from_document(application)


async def schedule_interview(scope: AccessScope, payload: InterviewSchedule) -> InterviewRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    app_id = to_object_id(payload.application_id, "application_id")
    application = await HrJobApplication.get(app_id)
    if application is None or application.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    panel = [to_object_id(x, "panel_member_id") for x in payload.panel_member_ids]
    interviewers = [to_object_id(x, "interviewer_id") for x in payload.interviewer_ids]
    code = f"INT-{uuid4().hex[:10].upper()}"
    session = HrInterviewSession(
        tenant_id=tenant_id,
        application_id=application.id,
        interview_code=code,
        scheduled_at=payload.scheduled_at,
        mode=payload.mode,
        location_or_meeting=payload.location_or_meeting,
        panel_member_ids=panel,
        interviewer_ids=interviewers,
        actor_id=scope.user_id,
    )
    await session.insert()
    if application.stage != HrApplicationPipelineStage.INTERVIEW_SCHEDULED:
        await _record_stage(
            application,
            HrApplicationPipelineStage.INTERVIEW_SCHEDULED,
            actor_id=scope.user_id,
            reason="Interview scheduled",
        )
    candidate = await HrCandidate.get(application.candidate_id)
    if candidate:
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.recruitment.interview_scheduled",
            aggregate_type="hr_interview",
            aggregate_id=str(session.id),
            title="Interview scheduled",
            body=f"Interview {code} scheduled at {payload.scheduled_at.isoformat()}.",
            recipient_email=candidate.email,
            dedupe_key=f"hr:interview_sched:{session.id}",
        )
    return InterviewRead.from_document(session)


async def reschedule_interview(scope: AccessScope, interview_id: str, payload: InterviewReschedule) -> InterviewRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    iid = to_object_id(interview_id, "interview_id")
    session = await HrInterviewSession.get(iid)
    if session is None or session.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Interview not found", status_code=404)
    session.scheduled_at = payload.scheduled_at
    session.status = HrInterviewStatus.RESCHEDULED
    session.reschedule_reason = payload.reason
    session.updated_at = utcnow()
    await session.save()
    application = await HrJobApplication.get(session.application_id)
    if application:
        candidate = await HrCandidate.get(application.candidate_id)
        if candidate:
            await enqueue_hr_notification(
                tenant_id,
                event_type="hr.recruitment.interview_rescheduled",
                aggregate_type="hr_interview",
                aggregate_id=str(session.id),
                title="Interview rescheduled",
                body=payload.reason,
                recipient_email=candidate.email,
                dedupe_key=f"hr:interview_resched:{session.id}:{payload.scheduled_at.isoformat()}",
            )
    return InterviewRead.from_document(session)


async def submit_interview_feedback(
    scope: AccessScope,
    interview_id: str,
    payload: InterviewFeedbackSubmit,
) -> dict:
    tenant_id = require_hr_tenant_scope(scope)
    iid = to_object_id(interview_id, "interview_id")
    session = await HrInterviewSession.get(iid)
    if session is None or session.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Interview not found", status_code=404)
    if scope.user_id not in session.interviewer_ids and scope.user_id not in session.panel_member_ids:
        authorize_hr_recruitment_manage(scope)
    cfg = await ensure_pipeline_config(tenant_id)
    unknown = [k for k in payload.criteria_scores if k not in cfg.evaluation_criteria]
    if unknown:
        raise AppError(
            code="VALIDATION_ERROR",
            message=f"Unknown evaluation criteria: {', '.join(unknown)}",
            status_code=422,
        )
    feedback = HrInterviewFeedback(
        tenant_id=tenant_id,
        interview_id=session.id,
        application_id=session.application_id,
        interviewer_id=scope.user_id,
        criteria_scores=payload.criteria_scores,
        comments=payload.comments,
        recommendation=payload.recommendation,
    )
    await feedback.insert()
    session.status = HrInterviewStatus.COMPLETED
    session.updated_at = utcnow()
    await session.save()
    application = await HrJobApplication.get(session.application_id)
    if application and application.stage == HrApplicationPipelineStage.INTERVIEW_SCHEDULED:
        await _record_stage(
            application,
            HrApplicationPipelineStage.INTERVIEW_COMPLETED,
            actor_id=scope.user_id,
            reason="Interview feedback submitted",
        )
    return {"feedback_id": str(feedback.id)}


async def create_offer(scope: AccessScope, payload: OfferCreate) -> OfferRead:
    authorize_hr_recruitment_manage(scope)
    tenant_id = require_hr_tenant_scope(scope)
    app_id = to_object_id(payload.application_id, "application_id")
    application = await HrJobApplication.get(app_id)
    if application is None or application.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Application not found", status_code=404)
    if application.stage not in {
        HrApplicationPipelineStage.SELECTED,
        HrApplicationPipelineStage.FINAL_EVALUATION,
        HrApplicationPipelineStage.INTERVIEW_COMPLETED,
    }:
        raise AppError(code="CONFLICT", message="Application is not ready for offer", status_code=409)
    dept_id = to_object_id(payload.department_id, "department_id")
    await _validate_department(tenant_id, dept_id)
    if await HrEmploymentOffer.find_one(
        Eq(HrEmploymentOffer.tenant_id, tenant_id),
        Eq(HrEmploymentOffer.application_id, application.id),
        In(HrEmploymentOffer.status, [HrEmploymentOfferStatus.DRAFT, HrEmploymentOfferStatus.PENDING_APPROVAL, HrEmploymentOfferStatus.APPROVED, HrEmploymentOfferStatus.ISSUED]),
    ):
        raise AppError(code="CONFLICT", message="Active offer already exists", status_code=409)
    code = f"OFR-{uuid4().hex[:10].upper()}"
    offer = HrEmploymentOffer(
        tenant_id=tenant_id,
        offer_code=code,
        application_id=application.id,
        candidate_id=application.candidate_id,
        job_opening_id=application.job_opening_id,
        designation=payload.designation,
        department_id=dept_id,
        employment_type=payload.employment_type,
        salary_details=payload.salary_details,
        expected_joining_date=payload.expected_joining_date,
        offer_valid_until=payload.offer_valid_until,
        status=HrEmploymentOfferStatus.DRAFT,
        actor_id=scope.user_id,
    )
    await offer.insert()
    return OfferRead.from_document(offer)


async def decide_offer(scope: AccessScope, offer_id: str, payload: OfferDecision) -> OfferRead:
    tenant_id = require_hr_tenant_scope(scope)
    oid = to_object_id(offer_id, "offer_id")
    offer = await HrEmploymentOffer.get(oid)
    if offer is None or offer.tenant_id != tenant_id:
        raise AppError(code="NOT_FOUND", message="Offer not found", status_code=404)
    application = await HrJobApplication.get(offer.application_id)
    candidate = await HrCandidate.get(offer.candidate_id)

    if payload.decision == "submit_approval":
        authorize_hr_recruitment_manage(scope)
        if offer.status != HrEmploymentOfferStatus.DRAFT:
            raise AppError(code="CONFLICT", message="Only draft offers can be submitted for approval", status_code=409)
        offer.status = HrEmploymentOfferStatus.PENDING_APPROVAL
    elif payload.decision == "approve":
        authorize_hr_recruitment_approve(scope)
        if offer.status not in {HrEmploymentOfferStatus.DRAFT, HrEmploymentOfferStatus.PENDING_APPROVAL}:
            raise AppError(code="CONFLICT", message="Offer is not awaiting approval", status_code=409)
        offer.status = HrEmploymentOfferStatus.APPROVED
        offer.approved_by = scope.user_id
        offer.approved_at = utcnow()
        offer.approval_note = payload.note
    elif payload.decision == "issue":
        authorize_hr_recruitment_manage(scope)
        if offer.status != HrEmploymentOfferStatus.APPROVED:
            raise AppError(code="CONFLICT", message="Offer must be approved before issue", status_code=409)
        offer.status = HrEmploymentOfferStatus.ISSUED
        offer.issued_at = utcnow()
        if application:
            await _record_stage(application, HrApplicationPipelineStage.OFFER_ISSUED, actor_id=scope.user_id, reason=None)
    elif payload.decision == "accept":
        authorize_hr_recruitment_manage(scope)
        if offer.status != HrEmploymentOfferStatus.ISSUED:
            raise AppError(code="CONFLICT", message="Offer is not issued", status_code=409)
        if offer.offer_valid_until and offer.offer_valid_until < date.today():
            offer.status = HrEmploymentOfferStatus.EXPIRED
            offer.updated_at = utcnow()
            await offer.save()
            raise AppError(code="CONFLICT", message="Offer has expired", status_code=409)
        offer.status = HrEmploymentOfferStatus.ACCEPTED
        offer.decided_at = utcnow()
        if application:
            await _record_stage(application, HrApplicationPipelineStage.OFFER_ACCEPTED, actor_id=scope.user_id, reason=None)
        opening = await HrJobOpening.get(offer.job_opening_id)
        if opening:
            opening.filled_count += 1
            if opening.filled_count >= opening.vacancies:
                opening.status = HrJobOpeningStatus.CLOSED_FILLED
            opening.updated_at = utcnow()
            await opening.save()
    elif payload.decision == "decline":
        authorize_hr_recruitment_manage(scope)
        if offer.status != HrEmploymentOfferStatus.ISSUED:
            raise AppError(code="CONFLICT", message="Offer is not issued", status_code=409)
        offer.status = HrEmploymentOfferStatus.DECLINED
        offer.decided_at = utcnow()
        if application:
            await _record_stage(application, HrApplicationPipelineStage.OFFER_DECLINED, actor_id=scope.user_id, reason=payload.note)
    elif payload.decision == "withdraw":
        authorize_hr_recruitment_manage(scope)
        offer.status = HrEmploymentOfferStatus.WITHDRAWN
    elif payload.decision == "remind":
        authorize_hr_recruitment_manage(scope)
        if offer.status != HrEmploymentOfferStatus.ISSUED:
            raise AppError(code="CONFLICT", message="Only issued offers can be reminded", status_code=409)
        if candidate:
            await enqueue_hr_notification(
                tenant_id,
                event_type="hr.recruitment.offer_reminder",
                aggregate_type="hr_employment_offer",
                aggregate_id=str(offer.id),
                title="Offer reminder",
                body=f"Reminder: offer {offer.offer_code} is awaiting your response.",
                recipient_email=candidate.email,
                dedupe_key=f"hr:offer_remind:{offer.id}:{date.today().isoformat()}",
            )
    else:
        raise AppError(code="VALIDATION_ERROR", message="Invalid decision", status_code=422)

    offer.updated_at = utcnow()
    await offer.save()
    if candidate and payload.decision == "issue":
        await enqueue_hr_notification(
            tenant_id,
            event_type="hr.recruitment.offer_issued",
            aggregate_type="hr_employment_offer",
            aggregate_id=str(offer.id),
            title="Employment offer",
            body=f"Offer {offer.offer_code} has been issued.",
            recipient_email=candidate.email,
            dedupe_key=f"hr:offer_issue:{offer.id}",
        )
    return OfferRead.from_document(offer)


async def recruitment_dashboard(scope: AccessScope, filters: RecruitmentDashboardFilters) -> RecruitmentDashboardStats:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    stats = RecruitmentDashboardStats()
    opening_query: dict = {"tenant_id": tenant_id}
    if filters.department_id:
        opening_query["department_id"] = to_object_id(filters.department_id, "department_id")
    if filters.campus_id:
        opening_query["campus_id"] = to_object_id(filters.campus_id, "campus_id")
    if filters.requisition_id:
        opening_query["requisition_id"] = to_object_id(filters.requisition_id, "requisition_id")
    openings = await HrJobOpening.find(opening_query).to_list()
    if filters.job_title:
        term = filters.job_title.strip().lower()
        openings = [o for o in openings if term in o.job_title.lower()]
    stats.total_job_openings = len(openings)
    reqs = await HrJobRequisition.find({"tenant_id": tenant_id}).to_list()
    if filters.department_id:
        dept_oid = to_object_id(filters.department_id, "department_id")
        reqs = [r for r in reqs if r.department_id == dept_oid]
    from app.modules.hr.enums import HrJobRequisitionStatus

    for r in reqs:
        if r.status == HrJobRequisitionStatus.DRAFT:
            stats.draft_requisitions += 1
        elif r.status in {
            HrJobRequisitionStatus.SUBMITTED,
            HrJobRequisitionStatus.HR_REVIEW,
            HrJobRequisitionStatus.PENDING_MANAGEMENT_APPROVAL,
            HrJobRequisitionStatus.APPROVED,
        }:
            stats.active_requisitions += 1
    for o in openings:
        if o.status == HrJobOpeningStatus.PUBLISHED:
            stats.active_job_openings += 1
        elif o.status == HrJobOpeningStatus.DRAFT:
            stats.draft_job_openings += 1
        elif o.status == HrJobOpeningStatus.CLOSED_FILLED:
            stats.positions_filled += o.filled_count

    app_query: dict = {"tenant_id": tenant_id}
    if filters.job_opening_id:
        app_query["job_opening_id"] = to_object_id(filters.job_opening_id, "job_opening_id")
    if filters.department_id:
        app_query["department_id"] = to_object_id(filters.department_id, "department_id")
    if filters.application_stage:
        app_query["stage"] = filters.application_stage.value
    apps = await HrJobApplication.find(app_query).to_list()
    if filters.period_from or filters.period_to:
        apps = [
            a
            for a in apps
            if (not filters.period_from or a.applied_at.date() >= filters.period_from)
            and (not filters.period_to or a.applied_at.date() <= filters.period_to)
        ]
    stats.applications_received = len(apps)
    for app in apps:
        if app.stage == HrApplicationPipelineStage.APPLICATION_SUBMITTED:
            stats.new_applications += 1
        elif app.stage in {HrApplicationPipelineStage.UNDER_REVIEW, HrApplicationPipelineStage.INITIAL_SCREENING}:
            stats.under_review += 1
        elif app.stage == HrApplicationPipelineStage.SHORTLISTED:
            stats.shortlisted += 1
        elif app.stage == HrApplicationPipelineStage.ASSESSMENT:
            stats.in_assessment += 1
        elif app.stage == HrApplicationPipelineStage.INTERVIEW_SCHEDULED:
            stats.interviews_scheduled += 1
        elif app.stage in {HrApplicationPipelineStage.INTERVIEW_COMPLETED, HrApplicationPipelineStage.FINAL_EVALUATION}:
            stats.awaiting_feedback += 1
        elif app.stage == HrApplicationPipelineStage.SELECTED:
            stats.selected += 1
        elif app.stage == HrApplicationPipelineStage.REJECTED:
            stats.rejected += 1
        elif app.stage == HrApplicationPipelineStage.WITHDRAWN:
            stats.withdrawn += 1

    offers = await HrEmploymentOffer.find(Eq(HrEmploymentOffer.tenant_id, tenant_id)).to_list()
    for offer in offers:
        if offer.status == HrEmploymentOfferStatus.PENDING_APPROVAL:
            stats.offers_pending_approval += 1
        if offer.status == HrEmploymentOfferStatus.ISSUED:
            stats.offers_issued += 1
        elif offer.status == HrEmploymentOfferStatus.ACCEPTED:
            stats.offers_accepted += 1
        elif offer.status == HrEmploymentOfferStatus.DECLINED:
            stats.offers_declined += 1
    return stats


async def list_applications(
    scope: AccessScope,
    pagination: Pagination,
    *,
    job_opening_id: str | None = None,
    stage: HrApplicationPipelineStage | None = None,
) -> Page[ApplicationRead]:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    filters = [Eq(HrJobApplication.tenant_id, tenant_id)]
    if job_opening_id:
        filters.append(Eq(HrJobApplication.job_opening_id, to_object_id(job_opening_id, "job_opening_id")))
    if stage:
        filters.append(Eq(HrJobApplication.stage, stage))
    query = HrJobApplication.find(*filters)
    total = await query.count()
    rows = await query.sort(-HrJobApplication.applied_at).skip(pagination.skip).limit(pagination.limit).to_list()
    items = [ApplicationRead.from_document(r) for r in rows]
    return Page(items=items, total=total, page=pagination.page, size=pagination.size)


async def list_interviews_for_interviewer(scope: AccessScope, pagination: Pagination) -> Page[InterviewRead]:
    authorize_hr_recruitment_read(scope)
    tenant_id = require_hr_tenant_scope(scope)
    all_rows = await HrInterviewSession.find(Eq(HrInterviewSession.tenant_id, tenant_id)).to_list()
    uid = scope.user_id
    filtered = [
        r
        for r in all_rows
        if uid in r.interviewer_ids or uid in r.panel_member_ids
    ]
    filtered.sort(key=lambda r: r.scheduled_at, reverse=True)
    page_rows = filtered[pagination.skip : pagination.skip + pagination.limit]
    items = [InterviewRead.from_document(v) for v in page_rows]
    return Page(items=items, total=len(filtered), page=pagination.page, size=pagination.size)