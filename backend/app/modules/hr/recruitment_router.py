"""HR recruitment routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.enums import HrApplicationPipelineStage, HrJobOpeningStatus
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
from app.modules.hr.recruitment_queries_service import (
    cancel_interview,
    consolidate_application_evaluation,
    get_application_history,
    get_application_workspace,
    get_candidate,
    get_interview_detail,
    get_job_opening,
    get_job_requisition,
    get_pipeline_config,
    get_recruiter_assignment_history,
    list_candidates,
    list_interviews_for_application,
    list_job_openings,
    list_job_requisitions,
    list_offers,
    recruitment_reports,
    compare_candidates_for_opening,
    get_application_recruitment_history,
    reject_application,
    request_additional_information,
    revise_offer,
    update_pipeline_config,
    withdraw_application,
)
from app.modules.hr.recruitment_schemas import (
    ApplicationRequestInfo,
    ApplicationWorkspaceRead,
    ChannelApplicationCreate,
    CandidateDetailRead,
    ConsolidatedEvaluationRead,
    InterviewDetailRead,
    JobRequisitionDetailRead,
    OfferRevise,
    PipelineConfigRead,
    PipelineConfigUpdate,
    RecruitmentReportRead,
)
from app.modules.hr.recruitment_service import (
    add_review_note,
    assign_recruiter,
    create_application,
    create_application_via_channel,
    create_job_opening,
    create_job_requisition,
    create_offer,
    decide_offer,
    list_applications,
    list_interviews_for_interviewer,
    recruitment_dashboard,
    reschedule_interview,
    review_job_requisition,
    schedule_interview,
    set_job_opening_status,
    submit_interview_feedback,
    submit_job_requisition,
    transition_application_stage,
    update_job_opening,
    upsert_candidate,
)

router = APIRouter(prefix="/recruitment", tags=["hr-recruitment"])


@router.get("/dashboard", response_model=ApiResponse[RecruitmentDashboardStats])
async def recruitment_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    department_id: str | None = None,
    job_opening_id: str | None = None,
    campus_id: str | None = None,
    application_stage: HrApplicationPipelineStage | None = None,
    requisition_id: str | None = None,
    job_title: str | None = None,
    period_from: date | None = None,
    period_to: date | None = None,
):
    filters = RecruitmentDashboardFilters(
        department_id=department_id,
        job_opening_id=job_opening_id,
        requisition_id=requisition_id,
        job_title=job_title,
        campus_id=campus_id,
        application_stage=application_stage,
        period_from=period_from,
        period_to=period_to,
    )
    return success_response(await recruitment_dashboard(scope, filters), request_id=get_request_id())


@router.get("/requisitions", response_model=ApiResponse[Page[JobRequisitionRead]])
async def list_requisitions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: str | None = None,
):
    return success_response(await list_job_requisitions(scope, pagination, status=status), request_id=get_request_id())


@router.get("/requisitions/{requisition_id}", response_model=ApiResponse[JobRequisitionDetailRead])
async def get_requisition_route(
    requisition_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await get_job_requisition(scope, requisition_id), request_id=get_request_id())


@router.post("/requisitions", response_model=ApiResponse[JobRequisitionRead])
async def create_requisition_route(
    payload: JobRequisitionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await create_job_requisition(scope, payload), request_id=get_request_id())


@router.post("/requisitions/{requisition_id}/submit", response_model=ApiResponse[JobRequisitionRead])
async def submit_requisition_route(
    requisition_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await submit_job_requisition(scope, requisition_id), request_id=get_request_id())


@router.post("/requisitions/{requisition_id}/review", response_model=ApiResponse[JobRequisitionRead])
async def review_requisition_route(
    requisition_id: str,
    payload: RequisitionDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await review_job_requisition(scope, requisition_id, payload), request_id=get_request_id())


@router.get("/openings", response_model=ApiResponse[Page[JobOpeningRead]])
async def list_openings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    requisition_id: str | None = None,
    department_id: str | None = None,
):
    return success_response(
        await list_job_openings(scope, pagination, requisition_id=requisition_id, department_id=department_id),
        request_id=get_request_id(),
    )


@router.get("/openings/{opening_id}", response_model=ApiResponse[JobOpeningRead])
async def get_opening_route(
    opening_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await get_job_opening(scope, opening_id), request_id=get_request_id())


@router.post("/openings", response_model=ApiResponse[JobOpeningRead])
async def create_opening_route(
    payload: JobOpeningCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await create_job_opening(scope, payload), request_id=get_request_id())


@router.patch("/openings/{opening_id}", response_model=ApiResponse[JobOpeningRead])
async def update_opening_route(
    opening_id: str,
    payload: JobOpeningUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await update_job_opening(scope, opening_id, payload), request_id=get_request_id())


@router.post("/openings/{opening_id}/status/{status}", response_model=ApiResponse[JobOpeningRead])
async def opening_status_route(
    opening_id: str,
    status: HrJobOpeningStatus,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await set_job_opening_status(scope, opening_id, status), request_id=get_request_id())


@router.get("/candidates", response_model=ApiResponse[Page[CandidateRead]])
async def list_candidates_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await list_candidates(scope, pagination), request_id=get_request_id())


@router.get("/candidates/{candidate_id}", response_model=ApiResponse[CandidateDetailRead])
async def get_candidate_route(
    candidate_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await get_candidate(scope, candidate_id), request_id=get_request_id())


@router.post("/candidates", response_model=ApiResponse[CandidateRead])
async def upsert_candidate_route(
    payload: CandidateUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await upsert_candidate(scope, payload), request_id=get_request_id())


@router.post("/channel-applications", response_model=ApiResponse[ApplicationRead])
async def channel_application_route(
    payload: ChannelApplicationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(
        await create_application_via_channel(
            scope,
            job_opening_id=payload.job_opening_id,
            candidate=payload.candidate,
            application_source=payload.application_source,
            document_refs=payload.document_refs,
        ),
        request_id=get_request_id(),
    )


@router.post("/applications", response_model=ApiResponse[ApplicationRead])
async def create_application_route(
    payload: ApplicationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await create_application(scope, payload), request_id=get_request_id())


@router.get("/applications", response_model=ApiResponse[Page[ApplicationRead]])
async def list_applications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    job_opening_id: str | None = None,
    stage: HrApplicationPipelineStage | None = None,
):
    return success_response(
        await list_applications(scope, pagination, job_opening_id=job_opening_id, stage=stage),
        request_id=get_request_id(),
    )


@router.get("/applications/{application_id}", response_model=ApiResponse[ApplicationWorkspaceRead])
async def application_workspace_route(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await get_application_workspace(scope, application_id), request_id=get_request_id())


@router.get("/openings/{opening_id}/candidate-comparison", response_model=ApiResponse[list])
async def compare_candidates_route(
    opening_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await compare_candidates_for_opening(scope, opening_id), request_id=get_request_id())


@router.get("/applications/{application_id}/recruitment-history", response_model=ApiResponse[dict])
async def recruitment_history_route(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await get_application_recruitment_history(scope, application_id), request_id=get_request_id())


@router.get("/applications/{application_id}/history", response_model=ApiResponse[list])
async def application_history_route(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await get_application_history(scope, application_id), request_id=get_request_id())


@router.get("/applications/{application_id}/recruiter-history", response_model=ApiResponse[list])
async def recruiter_history_route(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await get_recruiter_assignment_history(scope, application_id), request_id=get_request_id())


@router.post("/applications/{application_id}/request-info")
async def request_info_route(
    application_id: str,
    payload: ApplicationRequestInfo,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await request_additional_information(scope, application_id, payload), request_id=get_request_id())


@router.post("/applications/{application_id}/withdraw", response_model=ApiResponse[ApplicationRead])
async def withdraw_application_route(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    reason: str | None = None,
):
    return success_response(await withdraw_application(scope, application_id, reason=reason), request_id=get_request_id())


@router.post("/applications/{application_id}/reject", response_model=ApiResponse[ApplicationRead])
async def reject_application_route(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    reason: str | None = None,
):
    return success_response(await reject_application(scope, application_id, reason=reason), request_id=get_request_id())


@router.get("/applications/{application_id}/evaluation", response_model=ApiResponse[ConsolidatedEvaluationRead])
async def evaluation_route(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await consolidate_application_evaluation(scope, application_id), request_id=get_request_id())


@router.post("/applications/{application_id}/stage", response_model=ApiResponse[ApplicationRead])
async def transition_stage_route(
    application_id: str,
    payload: ApplicationStageTransition,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await transition_application_stage(scope, application_id, payload), request_id=get_request_id())


@router.post("/applications/{application_id}/notes")
async def review_note_route(
    application_id: str,
    payload: ApplicationReviewNoteCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await add_review_note(scope, application_id, payload), request_id=get_request_id())


@router.post("/applications/{application_id}/assign-recruiter", response_model=ApiResponse[ApplicationRead])
async def assign_recruiter_route(
    application_id: str,
    payload: ApplicationAssignRecruiter,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await assign_recruiter(scope, application_id, payload), request_id=get_request_id())


@router.post("/interviews", response_model=ApiResponse[InterviewRead])
async def schedule_interview_route(
    payload: InterviewSchedule,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await schedule_interview(scope, payload), request_id=get_request_id())


@router.get("/applications/{application_id}/interviews", response_model=ApiResponse[list[InterviewDetailRead]])
async def application_interviews_route(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await list_interviews_for_application(scope, application_id), request_id=get_request_id())


@router.get("/interviews/{interview_id}", response_model=ApiResponse[InterviewDetailRead])
async def interview_detail_route(
    interview_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await get_interview_detail(scope, interview_id), request_id=get_request_id())


@router.post("/interviews/{interview_id}/cancel", response_model=ApiResponse[InterviewDetailRead])
async def cancel_interview_route(
    interview_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    reason: str = "",
):
    return success_response(await cancel_interview(scope, interview_id, reason or "Cancelled"), request_id=get_request_id())


@router.post("/interviews/{interview_id}/reschedule", response_model=ApiResponse[InterviewRead])
async def reschedule_interview_route(
    interview_id: str,
    payload: InterviewReschedule,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await reschedule_interview(scope, interview_id, payload), request_id=get_request_id())


@router.post("/interviews/{interview_id}/feedback")
async def interview_feedback_route(
    interview_id: str,
    payload: InterviewFeedbackSubmit,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await submit_interview_feedback(scope, interview_id, payload), request_id=get_request_id())


@router.get("/interviews/mine", response_model=ApiResponse[Page[InterviewRead]])
async def my_interviews_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await list_interviews_for_interviewer(scope, pagination), request_id=get_request_id())


@router.post("/offers", response_model=ApiResponse[OfferRead])
async def create_offer_route(
    payload: OfferCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await create_offer(scope, payload), request_id=get_request_id())


@router.get("/offers", response_model=ApiResponse[Page[OfferRead]])
async def list_offers_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    application_id: str | None = None,
):
    return success_response(await list_offers(scope, pagination, application_id=application_id), request_id=get_request_id())


@router.patch("/offers/{offer_id}", response_model=ApiResponse[OfferRead])
async def revise_offer_route(
    offer_id: str,
    payload: OfferRevise,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await revise_offer(scope, offer_id, payload), request_id=get_request_id())


@router.post("/offers/{offer_id}/decision", response_model=ApiResponse[OfferRead])
async def offer_decision_route(
    offer_id: str,
    payload: OfferDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await decide_offer(scope, offer_id, payload), request_id=get_request_id())


@router.get("/pipeline-config", response_model=ApiResponse[PipelineConfigRead])
async def pipeline_get_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await get_pipeline_config(scope), request_id=get_request_id())


@router.put("/pipeline-config", response_model=ApiResponse[PipelineConfigRead])
async def pipeline_put_route(
    payload: PipelineConfigUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await update_pipeline_config(scope, payload), request_id=get_request_id())


@router.get("/reports", response_model=ApiResponse[RecruitmentReportRead])
async def recruitment_reports_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await recruitment_reports(scope), request_id=get_request_id())