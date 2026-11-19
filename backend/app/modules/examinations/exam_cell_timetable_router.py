"""Examination cell — exam timetable routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_timetable_schemas import (
    ExamScheduleApprovalRead,
    ExamTimetableApprovalRequest,
    ExamTimetableCreate,
    ExamTimetableEntryCreate,
    ExamTimetableEntryRead,
    ExamTimetableEntryReschedule,
    ExamTimetableRead,
    ExamTimetableRevisionRead,
    ExamTimetableValidationResult,
)
from app.modules.examinations.exam_cell_timetable_service import (
    add_timetable_entry,
    approve_exam_timetable,
    cancel_timetable_entry,
    create_exam_timetable,
    get_exam_timetable,
    list_exam_timetables,
    list_schedule_approvals,
    list_timetable_entries,
    list_timetable_revisions,
    publish_exam_timetable,
    reject_exam_timetable,
    reschedule_timetable_entry,
    revise_exam_timetable,
    submit_exam_timetable,
    validate_exam_timetable,
)

router = APIRouter(prefix="/timetables", tags=["examination-cell-timetables"])


@router.post("", response_model=ApiResponse[ExamTimetableRead], status_code=status.HTTP_201_CREATED)
async def create_timetable_route(
    payload: ExamTimetableCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableRead]:
    return success_response(await create_exam_timetable(scope, user, payload), request_id=get_request_id())


@router.get("", response_model=ApiResponse[Page[ExamTimetableRead]])
async def list_timetables_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    exam_session_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[ExamTimetableRead]]:
    _ = user
    return success_response(await list_exam_timetables(scope, exam_session_id=exam_session_id, pagination=pagination), request_id=get_request_id())


@router.get("/{timetable_id}", response_model=ApiResponse[ExamTimetableRead])
async def get_timetable_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableRead]:
    _ = user
    return success_response(await get_exam_timetable(scope, to_object_id(timetable_id, "timetable id")), request_id=get_request_id())


@router.post("/{timetable_id}/entries", response_model=ApiResponse[ExamTimetableEntryRead], status_code=status.HTTP_201_CREATED)
async def add_timetable_entry_route(
    timetable_id: str,
    payload: ExamTimetableEntryCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableEntryRead]:
    return success_response(
        await add_timetable_entry(scope, user, to_object_id(timetable_id, "timetable id"), payload),
        request_id=get_request_id(),
    )


@router.get("/{timetable_id}/entries", response_model=ApiResponse[list[ExamTimetableEntryRead]])
async def list_timetable_entries_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamTimetableEntryRead]]:
    _ = user
    return success_response(
        await list_timetable_entries(scope, to_object_id(timetable_id, "timetable id")),
        request_id=get_request_id(),
    )


@router.get("/{timetable_id}/validate", response_model=ApiResponse[ExamTimetableValidationResult])
async def validate_timetable_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableValidationResult]:
    _ = user
    return success_response(await validate_exam_timetable(scope, to_object_id(timetable_id, "timetable id")), request_id=get_request_id())


@router.post("/{timetable_id}/submit", response_model=ApiResponse[ExamTimetableRead])
async def submit_timetable_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableRead]:
    return success_response(await submit_exam_timetable(scope, user, to_object_id(timetable_id, "timetable id")), request_id=get_request_id())


@router.post("/{timetable_id}/approve", response_model=ApiResponse[ExamTimetableRead])
async def approve_timetable_route(
    timetable_id: str,
    body: ExamTimetableApprovalRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableRead]:
    return success_response(await approve_exam_timetable(scope, user, to_object_id(timetable_id, "timetable id"), body), request_id=get_request_id())


@router.post("/{timetable_id}/reject", response_model=ApiResponse[ExamTimetableRead])
async def reject_timetable_route(
    timetable_id: str,
    body: ExamTimetableApprovalRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableRead]:
    return success_response(await reject_exam_timetable(scope, user, to_object_id(timetable_id, "timetable id"), body), request_id=get_request_id())


@router.post("/{timetable_id}/publish", response_model=ApiResponse[ExamTimetableRead])
async def publish_timetable_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableRead]:
    return success_response(await publish_exam_timetable(scope, user, to_object_id(timetable_id, "timetable id")), request_id=get_request_id())


@router.post("/{timetable_id}/revise", response_model=ApiResponse[ExamTimetableRead])
async def revise_timetable_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableRead]:
    return success_response(await revise_exam_timetable(scope, user, to_object_id(timetable_id, "timetable id")), request_id=get_request_id())


@router.post("/{timetable_id}/entries/{entry_code}/cancel", response_model=ApiResponse[ExamTimetableEntryRead])
async def cancel_entry_route(
    timetable_id: str,
    entry_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableEntryRead]:
    return success_response(
        await cancel_timetable_entry(scope, user, to_object_id(timetable_id, "timetable id"), entry_code),
        request_id=get_request_id(),
    )


@router.post("/{timetable_id}/entries/{entry_code}/reschedule", response_model=ApiResponse[ExamTimetableEntryRead])
async def reschedule_entry_route(
    timetable_id: str,
    entry_code: str,
    payload: ExamTimetableEntryReschedule,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamTimetableEntryRead]:
    return success_response(
        await reschedule_timetable_entry(scope, user, to_object_id(timetable_id, "timetable id"), entry_code, payload),
        request_id=get_request_id(),
    )


@router.get("/{timetable_id}/revisions", response_model=ApiResponse[list[ExamTimetableRevisionRead]])
async def timetable_revisions_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamTimetableRevisionRead]]:
    _ = user
    return success_response(await list_timetable_revisions(scope, to_object_id(timetable_id, "timetable id")), request_id=get_request_id())


@router.get("/{timetable_id}/approvals", response_model=ApiResponse[list[ExamScheduleApprovalRead]])
async def timetable_approvals_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamScheduleApprovalRead]]:
    _ = user
    return success_response(await list_schedule_approvals(scope, to_object_id(timetable_id, "timetable id")), request_id=get_request_id())