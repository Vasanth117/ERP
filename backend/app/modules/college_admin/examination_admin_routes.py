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
