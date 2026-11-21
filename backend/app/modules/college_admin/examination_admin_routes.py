"""College admin examination administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.examination_admin_schemas import (
    EligibilityUpsert,
    ExaminationConfigRead,
    ExaminationConfigUpsert,
    ExaminationSeasonCreate,
    ExaminationSessionCreate,
    HallTicketGenerate,
    MarksBatchDecision,
    RegistrationWindowUpsert,
    ResultPublishRequest,
    ReviewWindowUpsert,
)
from app.modules.college_admin.schemas import (
    ExamRegistrationBulkConfirmPayload,
    ExamRegistrationManagementPageRead,
    ExaminationConfigurationPageRead,
    ExaminationConfigurationSave,
    ExaminationDashboardPageRead,
    ExaminationSessionManagementPageRead,
    ExamTimetableManagementActionPayload,
    ExamTimetableManagementPageRead,
    ExaminationHallSeatingActionPayload,
    ExaminationHallSeatingManagementPageRead,
    HallTicketAdministrationActionPayload,
    HallTicketAdministrationPageRead,
    InternalExternalAssessmentPageRead,
    InternalExternalAssessmentSavePayload,
    InvigilatorAllocationActionPayload,
    InvigilatorAllocationPageRead,
    MarksEntryManagementActionPayload,
    MarksEntryManagementPageRead,
    ResultApprovalActionPayload,
    ResultApprovalPageRead,
    ResultProcessingActionPayload,
    ResultProcessingPageRead,
    ResultPublicationActionPayload,
    ResultPublicationPageRead,
    RevaluationManagementPageRead,
    StudentExamEligibilityPageRead,
    StudentExamEligibilityRerunPayload,
    SupplementaryExaminationCreateSessionPayload,
    SupplementaryExaminationManagementPageRead,
)
from app.modules.college_admin.exam_registration_management_page_service import (
    bulk_confirm_exam_registrations,
    get_exam_registration_management_page,
)
from app.modules.college_admin.examination_configuration_page_service import (
    get_examination_configuration_page,
    save_examination_configuration_page,
)
from app.modules.college_admin.examination_dashboard_page_service import get_examination_dashboard_page
from app.modules.college_admin.examination_session_management_page_service import (
    get_examination_session_management_page,
)
from app.modules.college_admin.exam_timetable_management_page_service import (
    get_exam_timetable_management_page,
    publish_exam_timetable_page,
    regenerate_exam_timetable_page,
)
from app.modules.college_admin.examination_hall_seating_management_page_service import (
    auto_allocate_hall_seating_page,
    confirm_hall_seating_page,
    get_examination_hall_seating_management_page,
)
from app.modules.college_admin.hall_ticket_administration_page_service import (
    generate_all_hall_tickets_page,
    get_hall_ticket_administration_page,
    release_hall_tickets_page,
)
from app.modules.college_admin.internal_external_assessment_page_service import (
    get_internal_external_assessment_page,
    save_internal_external_assessment_page,
)
from app.modules.college_admin.invigilator_allocation_page_service import (
    auto_assign_invigilators_page,
    get_invigilator_allocation_page,
    publish_invigilator_roster_page,
)
from app.modules.college_admin.marks_entry_management_page_service import (
    get_marks_entry_management_page,
    lock_marks_entry_page,
    send_marks_entry_reminders_page,
)
from app.modules.college_admin.result_approval_page_service import (
    approve_result_approval_page,
    get_result_approval_page,
    return_result_approval_page,
)
from app.modules.college_admin.result_processing_page_service import (
    get_result_processing_page,
    process_results_page,
)
from app.modules.college_admin.result_publication_page_service import (
    get_result_publication_page,
    publish_results_now_page,
    schedule_result_publication_page,
)
from app.modules.college_admin.revaluation_management_page_service import get_revaluation_management_page
from app.modules.college_admin.supplementary_examination_management_page_service import (
    create_supplementary_examination_session_page,
    get_supplementary_examination_management_page,
)
from app.modules.college_admin.student_exam_eligibility_page_service import (
    get_student_exam_eligibility_page,
    rerun_student_exam_eligibility_page,
)
from app.modules.college_admin.examination_admin_service import (
    create_examination_season,
    create_examination_session,
    examination_report,
    generate_hall_ticket,
    list_eligibility,
    list_pending_marks,
    publish_hall_ticket,
    publish_results,
    review_marks_batch,
    set_eligibility,
    upsert_examination_centre,
    upsert_examination_config,
    upsert_registration_window,
    upsert_review_window,
)

router = APIRouter()


@router.put("/configurations", response_model=ApiResponse[ExaminationConfigRead])
async def exam_config_route(
    payload: ExaminationConfigUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ExaminationConfigRead]:
    return success_response(await upsert_examination_config(scope, payload), request_id=get_request_id())


@router.post("/seasons", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def exam_season_route(
    payload: ExaminationSeasonCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_examination_season(scope, payload), request_id=get_request_id())


@router.post("/sessions", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def exam_session_route(
    payload: ExaminationSessionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_examination_session(scope, payload), request_id=get_request_id())


@router.put("/registration-windows", response_model=ApiResponse[dict])
async def registration_window_route(
    payload: RegistrationWindowUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_registration_window(scope, payload), request_id=get_request_id())


@router.put("/eligibility", response_model=ApiResponse[dict])
async def eligibility_route(
    payload: EligibilityUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await set_eligibility(scope, payload), request_id=get_request_id())


@router.get("/eligibility/{season_id}", response_model=ApiResponse[Page[dict]])
async def list_eligibility_route(
    season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await list_eligibility(scope, season_id, pagination), request_id=get_request_id())


@router.post("/hall-tickets", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def hall_ticket_route(
    payload: HallTicketGenerate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await generate_hall_ticket(scope, payload), request_id=get_request_id())


@router.post("/hall-tickets/{ticket_id}/publish", response_model=ApiResponse[dict])
async def publish_hall_ticket_route(
    ticket_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await publish_hall_ticket(scope, ticket_id), request_id=get_request_id())


@router.get("/marks/pending", response_model=ApiResponse[Page[dict]])
async def pending_marks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await list_pending_marks(scope, pagination), request_id=get_request_id())


@router.post("/marks/review", response_model=ApiResponse[dict])
async def marks_review_route(
    payload: MarksBatchDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await review_marks_batch(scope, payload), request_id=get_request_id())


@router.post("/results/publish", response_model=ApiResponse[dict])
async def publish_results_route(
    payload: ResultPublishRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await publish_results(scope, payload), request_id=get_request_id())


@router.put("/review-windows", response_model=ApiResponse[dict])
async def review_window_route(
    payload: ReviewWindowUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_review_window(scope, payload), request_id=get_request_id())


@router.get("/reports/{season_id}", response_model=ApiResponse[dict])
async def exam_report_route(
    season_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await examination_report(scope, season_id), request_id=get_request_id())


@router.post("/centres", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def centre_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    centre_code: Annotated[str, Query()],
    name: Annotated[str, Query()],
) -> ApiResponse[dict]:
    return success_response(await upsert_examination_centre(scope, centre_code, name), request_id=get_request_id())


@router.get("/dashboard/page", response_model=ApiResponse[ExaminationDashboardPageRead])
async def examination_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[ExaminationDashboardPageRead]:
    return success_response(
        await get_examination_dashboard_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/registrations/page", response_model=ApiResponse[ExamRegistrationManagementPageRead])
async def exam_registration_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
    status: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> ApiResponse[ExamRegistrationManagementPageRead]:
    return success_response(
        await get_exam_registration_management_page(
            scope,
            page=page,
            session_id=session_id,
            status=status,
            programme_code=programme_code,
            search=search,
        ),
        request_id=get_request_id(),
    )


@router.post("/registrations/confirm-selected", response_model=ApiResponse[ExamRegistrationManagementPageRead])
async def exam_registration_confirm_selected_route(
    payload: ExamRegistrationBulkConfirmPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    actor: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ExamRegistrationManagementPageRead]:
    return success_response(
        await bulk_confirm_exam_registrations(scope, actor, payload),
        request_id=get_request_id(),
    )


@router.get("/sessions/page", response_model=ApiResponse[ExaminationSessionManagementPageRead])
async def examination_session_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
) -> ApiResponse[ExaminationSessionManagementPageRead]:
    return success_response(
        await get_examination_session_management_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/sessions/setup/page", response_model=ApiResponse[ExaminationConfigurationPageRead])
async def examination_configuration_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    session_id: Annotated[str | None, Query()] = None,
    mode: Annotated[str | None, Query()] = None,
) -> ApiResponse[ExaminationConfigurationPageRead]:
    return success_response(
        await get_examination_configuration_page(scope, session_id=session_id, mode=mode),
        request_id=get_request_id(),
    )


@router.post("/sessions/setup/save", response_model=ApiResponse[ExaminationConfigurationPageRead])
async def examination_configuration_save_route(
    payload: ExaminationConfigurationSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ExaminationConfigurationPageRead]:
    return success_response(
        await save_examination_configuration_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/timetable/page", response_model=ApiResponse[ExamTimetableManagementPageRead])
async def exam_timetable_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[ExamTimetableManagementPageRead]:
    return success_response(
        await get_exam_timetable_management_page(
            scope,
            page=page,
            session_id=session_id,
            programme_code=programme_code,
        ),
        request_id=get_request_id(),
    )


@router.post("/timetable/regenerate", response_model=ApiResponse[ExamTimetableManagementPageRead])
async def exam_timetable_regenerate_route(
    payload: ExamTimetableManagementActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ExamTimetableManagementPageRead]:
    return success_response(
        await regenerate_exam_timetable_page(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/timetable/publish", response_model=ApiResponse[ExamTimetableManagementPageRead])
async def exam_timetable_publish_route(
    payload: ExamTimetableManagementActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ExamTimetableManagementPageRead]:
    return success_response(
        await publish_exam_timetable_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/eligibility/students/page", response_model=ApiResponse[StudentExamEligibilityPageRead])
async def student_exam_eligibility_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[StudentExamEligibilityPageRead]:
    return success_response(
        await get_student_exam_eligibility_page(scope, page=page, session_id=session_id),
        request_id=get_request_id(),
    )


@router.post("/eligibility/students/rerun", response_model=ApiResponse[StudentExamEligibilityPageRead])
async def student_exam_eligibility_rerun_route(
    payload: StudentExamEligibilityRerunPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentExamEligibilityPageRead]:
    return success_response(
        await rerun_student_exam_eligibility_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/hall-tickets/page", response_model=ApiResponse[HallTicketAdministrationPageRead])
async def hall_ticket_administration_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[HallTicketAdministrationPageRead]:
    return success_response(
        await get_hall_ticket_administration_page(scope, page=page, session_id=session_id),
        request_id=get_request_id(),
    )


@router.post("/hall-tickets/generate-all", response_model=ApiResponse[HallTicketAdministrationPageRead])
async def hall_ticket_generate_all_route(
    payload: HallTicketAdministrationActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HallTicketAdministrationPageRead]:
    return success_response(
        await generate_all_hall_tickets_page(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/hall-tickets/release", response_model=ApiResponse[HallTicketAdministrationPageRead])
async def hall_ticket_release_route(
    payload: HallTicketAdministrationActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HallTicketAdministrationPageRead]:
    return success_response(
        await release_hall_tickets_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/halls-seating/page", response_model=ApiResponse[ExaminationHallSeatingManagementPageRead])
async def examination_hall_seating_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[ExaminationHallSeatingManagementPageRead]:
    return success_response(
        await get_examination_hall_seating_management_page(scope, page=page, session_id=session_id),
        request_id=get_request_id(),
    )


@router.post("/halls-seating/auto-allocate", response_model=ApiResponse[ExaminationHallSeatingManagementPageRead])
async def examination_hall_seating_auto_allocate_route(
    payload: ExaminationHallSeatingActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ExaminationHallSeatingManagementPageRead]:
    return success_response(
        await auto_allocate_hall_seating_page(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/halls-seating/confirm", response_model=ApiResponse[ExaminationHallSeatingManagementPageRead])
async def examination_hall_seating_confirm_route(
    payload: ExaminationHallSeatingActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ExaminationHallSeatingManagementPageRead]:
    return success_response(
        await confirm_hall_seating_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/invigilation/page", response_model=ApiResponse[InvigilatorAllocationPageRead])
async def invigilator_allocation_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[InvigilatorAllocationPageRead]:
    return success_response(
        await get_invigilator_allocation_page(scope, page=page, session_id=session_id),
        request_id=get_request_id(),
    )


@router.post("/invigilation/auto-assign", response_model=ApiResponse[InvigilatorAllocationPageRead])
async def invigilator_auto_assign_route(
    payload: InvigilatorAllocationActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InvigilatorAllocationPageRead]:
    return success_response(
        await auto_assign_invigilators_page(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/invigilation/publish-roster", response_model=ApiResponse[InvigilatorAllocationPageRead])
async def invigilator_publish_roster_route(
    payload: InvigilatorAllocationActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InvigilatorAllocationPageRead]:
    return success_response(
        await publish_invigilator_roster_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/marks-entry/page", response_model=ApiResponse[MarksEntryManagementPageRead])
async def marks_entry_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[MarksEntryManagementPageRead]:
    return success_response(
        await get_marks_entry_management_page(scope, page=page, session_id=session_id),
        request_id=get_request_id(),
    )


@router.post("/marks-entry/send-reminders", response_model=ApiResponse[MarksEntryManagementPageRead])
async def marks_entry_send_reminders_route(
    payload: MarksEntryManagementActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[MarksEntryManagementPageRead]:
    return success_response(
        await send_marks_entry_reminders_page(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/marks-entry/lock", response_model=ApiResponse[MarksEntryManagementPageRead])
async def marks_entry_lock_route(
    payload: MarksEntryManagementActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[MarksEntryManagementPageRead]:
    return success_response(
        await lock_marks_entry_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/assessment-pattern/page", response_model=ApiResponse[InternalExternalAssessmentPageRead])
async def internal_external_assessment_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[InternalExternalAssessmentPageRead]:
    return success_response(
        await get_internal_external_assessment_page(scope, session_id=session_id),
        request_id=get_request_id(),
    )


@router.post("/assessment-pattern/save", response_model=ApiResponse[InternalExternalAssessmentPageRead])
async def internal_external_assessment_save_route(
    payload: InternalExternalAssessmentSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InternalExternalAssessmentPageRead]:
    return success_response(
        await save_internal_external_assessment_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/results/processing/page", response_model=ApiResponse[ResultProcessingPageRead])
async def result_processing_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[ResultProcessingPageRead]:
    return success_response(
        await get_result_processing_page(scope, session_id=session_id),
        request_id=get_request_id(),
    )


@router.post("/results/processing/process", response_model=ApiResponse[ResultProcessingPageRead])
async def result_processing_process_route(
    payload: ResultProcessingActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ResultProcessingPageRead]:
    return success_response(
        await process_results_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/results/approval/page", response_model=ApiResponse[ResultApprovalPageRead])
async def result_approval_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[ResultApprovalPageRead]:
    return success_response(
        await get_result_approval_page(scope, page=page, session_id=session_id),
        request_id=get_request_id(),
    )


@router.post("/results/approval/approve", response_model=ApiResponse[ResultApprovalPageRead])
async def result_approval_approve_route(
    payload: ResultApprovalActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ResultApprovalPageRead]:
    return success_response(
        await approve_result_approval_page(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/results/approval/return", response_model=ApiResponse[ResultApprovalPageRead])
async def result_approval_return_route(
    payload: ResultApprovalActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ResultApprovalPageRead]:
    return success_response(
        await return_result_approval_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/results/publication/page", response_model=ApiResponse[ResultPublicationPageRead])
async def result_publication_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[ResultPublicationPageRead]:
    return success_response(
        await get_result_publication_page(scope, page=page, session_id=session_id),
        request_id=get_request_id(),
    )


@router.post("/results/publication/publish-now", response_model=ApiResponse[ResultPublicationPageRead])
async def result_publication_publish_now_route(
    payload: ResultPublicationActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ResultPublicationPageRead]:
    return success_response(
        await publish_results_now_page(scope, payload),
        request_id=get_request_id(),
    )


@router.post("/results/publication/schedule", response_model=ApiResponse[ResultPublicationPageRead])
async def result_publication_schedule_route(
    payload: ResultPublicationActionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ResultPublicationPageRead]:
    return success_response(
        await schedule_result_publication_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/revaluation/page", response_model=ApiResponse[RevaluationManagementPageRead])
async def revaluation_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[RevaluationManagementPageRead]:
    return success_response(
        await get_revaluation_management_page(scope, page=page, session_id=session_id),
        request_id=get_request_id(),
    )


@router.get("/supplementary/page", response_model=ApiResponse[SupplementaryExaminationManagementPageRead])
async def supplementary_examination_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[SupplementaryExaminationManagementPageRead]:
    return success_response(
        await get_supplementary_examination_management_page(scope, page=page, session_id=session_id),
        request_id=get_request_id(),
    )


@router.post("/supplementary/create-session", response_model=ApiResponse[SupplementaryExaminationManagementPageRead])
async def supplementary_examination_create_session_route(
    payload: SupplementaryExaminationCreateSessionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[SupplementaryExaminationManagementPageRead]:
    return success_response(
        await create_supplementary_examination_session_page(scope, payload),
        request_id=get_request_id(),
    )
