"""Examination cell — marks entry routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_deps import examination_cell_user
from app.modules.examinations.exam_cell_marks_schemas import (
    ExamMarksAccessGrant,
    ExamMarksBulkUpsert,
    ExamMarksCorrectionRead,
    ExamMarksCorrectionRequest,
    ExamMarksEntryRead,
    ExamMarksEntryUpsert,
    ExamMarksHistoryRead,
    ExamMarksImportRequest,
    ExamMarksImportResult,
    ExamMarksSubjectSummary,
    ExamMarksSubmissionRead,
    ExamMarksSubmitRequest,
)
from app.modules.examinations.exam_cell_marks_service import (
    apply_marks_correction,
    approve_marks,
    bulk_save_marks,
    get_submission,
    grant_marks_access,
    import_marks,
    marks_history,
    marks_subject_summary,
    moderate_marks,
    request_marks_correction,
    save_marks_draft,
    submit_marks,
)

router = APIRouter(tags=["examination-cell-marks"])


@router.post("/marks/access", response_model=ApiResponse[ExamMarksSubmissionRead])
async def grant_access_route(
    payload: ExamMarksAccessGrant,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksSubmissionRead]:
    return success_response(await grant_marks_access(scope, user, payload), request_id=get_request_id())


@router.get("/marks/submissions/{submission_id}", response_model=ApiResponse[ExamMarksSubmissionRead])
async def get_submission_route(
    submission_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksSubmissionRead]:
    _ = user
    return success_response(await get_submission(scope, submission_id), request_id=get_request_id())


@router.post("/marks/submissions/{submission_id}/entries", response_model=ApiResponse[ExamMarksEntryRead])
async def save_entry_route(
    submission_id: str,
    payload: ExamMarksEntryUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksEntryRead]:
    return success_response(await save_marks_draft(scope, user, submission_id, payload), request_id=get_request_id())


@router.post("/marks/submissions/{submission_id}/entries/bulk", response_model=ApiResponse[list[ExamMarksEntryRead]])
async def bulk_entries_route(
    submission_id: str,
    payload: ExamMarksBulkUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamMarksEntryRead]]:
    return success_response(await bulk_save_marks(scope, user, submission_id, payload), request_id=get_request_id())


@router.post("/marks/submissions/{submission_id}/submit", response_model=ApiResponse[ExamMarksSubmissionRead])
async def submit_marks_route(
    submission_id: str,
    payload: ExamMarksSubmitRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksSubmissionRead]:
    return success_response(await submit_marks(scope, user, submission_id, payload), request_id=get_request_id())


@router.post("/marks/submissions/{submission_id}/moderate", response_model=ApiResponse[ExamMarksSubmissionRead])
async def moderate_route(
    submission_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksSubmissionRead]:
    return success_response(await moderate_marks(scope, user, submission_id), request_id=get_request_id())


@router.post("/marks/submissions/{submission_id}/approve", response_model=ApiResponse[ExamMarksSubmissionRead])
async def approve_route(
    submission_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksSubmissionRead]:
    return success_response(await approve_marks(scope, user, submission_id), request_id=get_request_id())


@router.post("/marks/submissions/{submission_id}/corrections", response_model=ApiResponse[ExamMarksCorrectionRead])
async def correction_request_route(
    submission_id: str,
    payload: ExamMarksCorrectionRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksCorrectionRead]:
    return success_response(await request_marks_correction(scope, user, submission_id, payload), request_id=get_request_id())


@router.post("/marks/corrections/{correction_id}/approve", response_model=ApiResponse[ExamMarksCorrectionRead])
async def correction_approve_route(
    correction_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksCorrectionRead]:
    return success_response(await apply_marks_correction(scope, user, correction_id, approve=True), request_id=get_request_id())


@router.post("/marks/corrections/{correction_id}/reject", response_model=ApiResponse[ExamMarksCorrectionRead])
async def correction_reject_route(
    correction_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksCorrectionRead]:
    return success_response(await apply_marks_correction(scope, user, correction_id, approve=False), request_id=get_request_id())


@router.post("/marks/submissions/{submission_id}/import", response_model=ApiResponse[ExamMarksImportResult])
async def import_route(
    submission_id: str,
    payload: ExamMarksImportRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksImportResult]:
    return success_response(await import_marks(scope, user, submission_id, payload), request_id=get_request_id())


@router.get("/marks/submissions/{submission_id}/summary", response_model=ApiResponse[ExamMarksSubjectSummary])
async def summary_route(
    submission_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[ExamMarksSubjectSummary]:
    _ = user
    return success_response(await marks_subject_summary(scope, submission_id), request_id=get_request_id())


@router.get("/marks/submissions/{submission_id}/history", response_model=ApiResponse[list[ExamMarksHistoryRead]])
async def history_route(
    submission_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(examination_cell_user)],
) -> ApiResponse[list[ExamMarksHistoryRead]]:
    _ = user
    return success_response(await marks_history(scope, submission_id), request_id=get_request_id())