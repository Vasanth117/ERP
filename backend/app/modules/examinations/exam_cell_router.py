"""Examination cell — dashboard and session management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_dashboard_schemas import ExamDashboardOverview
from app.modules.examinations.exam_cell_dashboard_service import get_examination_dashboard
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_schemas import (
    ExamSessionCreate,
    ExamSessionRead,
    ExamSessionStatusHistoryRead,
    ExamSessionTransitionRequest,
    ExamSessionUpdate,
)
from app.modules.examinations.exam_cell_session_service import (
    create_exam_session,
    get_exam_session,
    list_exam_session_history,
    list_exam_sessions,
    transition_exam_session,
    update_exam_session,
)
from app.modules.examinations.exam_cell_schemas import ExamSessionListFilters
from app.modules.examinations.exam_cell_assessment_router import router as assessment_router
from app.modules.examinations.exam_cell_hall_ticket_router import router as hall_ticket_router
from app.modules.examinations.exam_cell_registration_router import router as registration_router
from app.modules.examinations.exam_cell_timetable_router import router as timetable_router
from app.modules.examinations.exam_cell_seating_router import router as seating_router
from app.modules.examinations.exam_cell_marks_router import router as marks_router
from app.modules.examinations.exam_cell_grading_router import router as grading_router
from app.modules.examinations.exam_cell_result_router import router as result_router
from app.modules.examinations.exam_cell_publication_router import router as publication_router
from app.modules.examinations.exam_cell_revaluation_router import router as revaluation_router
from app.modules.examinations.exam_cell_incident_router import router as incident_router
from app.modules.examinations.exam_cell_notification_router import router as notification_router
from app.modules.examinations.exam_cell_report_router import router as report_router
from app.modules.examinations.exam_cell_security_router import router as security_router

router = APIRouter()
router.include_router(assessment_router)
router.include_router(timetable_router)
router.include_router(registration_router)
router.include_router(hall_ticket_router)
router.include_router(seating_router)
router.include_router(marks_router)
router.include_router(grading_router)
router.include_router(result_router)
router.include_router(publication_router)
router.include_router(revaluation_router)
router.include_router(incident_router)
router.include_router(notification_router)
router.include_router(report_router)
router.include_router(security_router)


@router.get("/dashboard", response_model=ApiResponse[ExamDashboardOverview])
async def examination_dashboard_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    exam_session_id: Annotated[str | None, Query()] = None,
    session_code: Annotated[str | None, Query()] = None,
    department_code: Annotated[str | None, Query()] = None,
    course_code: Annotated[str | None, Query()] = None,
    examination_status: Annotated[ExamSessionStatus | None, Query(alias="status")] = None,
    examination_type: Annotated[ExamSessionType | None, Query()] = None,
) -> ApiResponse[ExamDashboardOverview]:
    data = await get_examination_dashboard(
        scope,
        user,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        exam_session_id=exam_session_id,
        session_code=session_code,
        department_code=department_code,
        course_code=course_code,
        examination_status=examination_status,
        examination_type=examination_type,
    )
    return success_response(data, request_id=get_request_id())


@router.post("/sessions", response_model=ApiResponse[ExamSessionRead], status_code=status.HTTP_201_CREATED)
async def create_exam_session_route(
    payload: ExamSessionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSessionRead]:
    return success_response(await create_exam_session(scope, user, payload), request_id=get_request_id())


@router.get("/sessions", response_model=ApiResponse[Page[ExamSessionRead]])
async def list_exam_sessions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    academic_year_label: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    examination_type: Annotated[ExamSessionType | None, Query()] = None,
    status_filter: Annotated[ExamSessionStatus | None, Query(alias="status")] = None,
    department_code: Annotated[str | None, Query()] = None,
    session_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[ExamSessionRead]]:
    _ = user
    filters = ExamSessionListFilters(
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        examination_type=examination_type,
        status=status_filter,
        department_code=department_code,
        session_code=session_code,
    )
    return success_response(await list_exam_sessions(scope, filters, pagination), request_id=get_request_id())


@router.get("/sessions/{session_id}", response_model=ApiResponse[ExamSessionRead])
async def get_exam_session_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSessionRead]:
    _ = user
    oid = to_object_id(session_id, "exam session id")
    return success_response(await get_exam_session(scope, oid), request_id=get_request_id())


@router.patch("/sessions/{session_id}", response_model=ApiResponse[ExamSessionRead])
async def update_exam_session_route(
    session_id: str,
    payload: ExamSessionUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSessionRead]:
    oid = to_object_id(session_id, "exam session id")
    return success_response(await update_exam_session(scope, user, oid, payload), request_id=get_request_id())


@router.post("/sessions/{session_id}/transitions", response_model=ApiResponse[ExamSessionRead])
async def transition_exam_session_route(
    session_id: str,
    payload: ExamSessionTransitionRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamSessionRead]:
    oid = to_object_id(session_id, "exam session id")
    return success_response(await transition_exam_session(scope, user, oid, payload), request_id=get_request_id())


@router.get("/sessions/{session_id}/history", response_model=ApiResponse[list[ExamSessionStatusHistoryRead]])
async def exam_session_history_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamSessionStatusHistoryRead]]:
    _ = user
    oid = to_object_id(session_id, "exam session id")
    return success_response(await list_exam_session_history(scope, oid), request_id=get_request_id())