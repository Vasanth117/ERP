"""Student LMS routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile
from pydantic import BaseModel, Field
from fastapi.responses import Response

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.lms.download_tokens import resolve_material_download_token
from app.modules.students.assessment_schemas import (
    AssessmentProgressRead,
    AssignmentDetailRead,
    AssignmentListRead,
    FeedbackRead,
    QuizScheduleRead,
    SubmissionStatusRead,
)
from app.modules.students.deps import lms_assignment_submit_rate_limit, student_user
from app.modules.students.student_lms_schemas import (
    CourseAnnouncementRead,
    LearningMaterialRead,
    LearningProgressRead,
    MaterialDownloadRead,
    QuizParticipationRead,
)
from app.modules.students.student_lms_service import (
    course_announcements,
    fetch_material_bytes,
    issue_material_download,
    learning_progress,
    list_course_materials,
    list_recorded_lectures,
    lms_assessment_progress,
    lms_assignment_detail,
    lms_assignment_feedback,
    lms_list_assignments,
    lms_notifications,
    lms_quiz_schedules,
    lms_submission_status,
    get_lms_preferences,
    update_lms_preferences,
    participate_quiz,
    submit_assignment_file,
)


class LmsPreferencesUpdate(BaseModel):
    group_by_unit: bool | None = None
    show_recorded_lectures: bool | None = None

    model_config = {"extra": "forbid"}

student_lms_router = APIRouter()


@student_lms_router.get("/me/lms/materials", response_model=ApiResponse[list[LearningMaterialRead]])
async def student_lms_materials_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    course_code: Annotated[str | None, Query()] = None,
    subject_id: Annotated[str | None, Query()] = None,
    unit_no: Annotated[int | None, Query(ge=1)] = None,
) -> ApiResponse[list[LearningMaterialRead]]:
    data = await list_course_materials(scope, user, course_code=course_code, subject_id=subject_id, unit_no=unit_no)
    return success_response(data, request_id=get_request_id())


@student_lms_router.get("/me/lms/recorded-lectures", response_model=ApiResponse[list[LearningMaterialRead]])
async def student_recorded_lectures_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    course_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[LearningMaterialRead]]:
    data = await list_recorded_lectures(scope, user, course_code=course_code)
    return success_response(data, request_id=get_request_id())


@student_lms_router.post(
    "/me/lms/materials/{material_id}/download-token",
    response_model=ApiResponse[MaterialDownloadRead],
)
async def student_material_download_token_route(
    material_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[MaterialDownloadRead]:
    data = await issue_material_download(scope, user, material_id)
    return success_response(data, request_id=get_request_id())


@student_lms_router.get("/me/lms/materials/{material_id}/download")
async def student_material_download_route(
    material_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    token: Annotated[str, Query(min_length=8)],
) -> Response:
    tenant_id = str(user.tenant_id)
    resolved_id = await resolve_material_download_token(tenant_id=tenant_id, token=token, user_id=str(user.id))
    if resolved_id != material_id:
        from app.core.exceptions import AppError

        raise AppError(code="FORBIDDEN", message="Token does not match material", status_code=403)
    data, name, mime = await fetch_material_bytes(scope, user, material_id)
    return Response(content=data, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{name}"'})


@student_lms_router.get("/me/lms/announcements", response_model=ApiResponse[Page[CourseAnnouncementRead]])
async def student_lms_announcements_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    course_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[CourseAnnouncementRead]]:
    data = await course_announcements(scope, user, course_code=course_code, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@student_lms_router.get("/me/lms/assignments", response_model=ApiResponse[list[AssignmentListRead]])
async def student_lms_assignments_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[AssignmentListRead]]:
    data = await lms_list_assignments(scope, user)
    return success_response(data, request_id=get_request_id())


@student_lms_router.get("/me/lms/assignments/{assignment_id}", response_model=ApiResponse[AssignmentDetailRead])
async def student_lms_assignment_detail_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[AssignmentDetailRead]:
    data = await lms_assignment_detail(scope, user, assignment_id)
    return success_response(data, request_id=get_request_id())


@student_lms_router.post("/me/lms/assignments/{assignment_id}/submit", response_model=ApiResponse[SubmissionStatusRead])
async def student_lms_assignment_submit_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(lms_assignment_submit_rate_limit)],
    file: UploadFile = File(...),
) -> ApiResponse[SubmissionStatusRead]:
    payload = await file.read()
    await submit_assignment_file(
        scope,
        user,
        assignment_id,
        file.filename or "submission.pdf",
        file.content_type or "application/octet-stream",
        payload,
    )
    detail = await lms_submission_status(scope, user, assignment_id)
    return success_response(detail, request_id=get_request_id())


@student_lms_router.get(
    "/me/lms/assignments/{assignment_id}/submission",
    response_model=ApiResponse[SubmissionStatusRead],
)
async def student_lms_submission_status_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[SubmissionStatusRead]:
    data = await lms_submission_status(scope, user, assignment_id)
    return success_response(data, request_id=get_request_id())


@student_lms_router.get(
    "/me/lms/assignments/{assignment_id}/feedback",
    response_model=ApiResponse[FeedbackRead],
)
async def student_lms_feedback_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[FeedbackRead]:
    data = await lms_assignment_feedback(scope, user, assignment_id)
    return success_response(data, request_id=get_request_id())


@student_lms_router.get("/me/lms/quizzes", response_model=ApiResponse[list[QuizScheduleRead]])
async def student_lms_quizzes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[QuizScheduleRead]]:
    data = await lms_quiz_schedules(scope, user)
    return success_response(data, request_id=get_request_id())


@student_lms_router.post("/me/lms/quizzes/{quiz_id}/participate", response_model=ApiResponse[QuizParticipationRead])
async def student_lms_quiz_participate_route(
    quiz_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[QuizParticipationRead]:
    data = await participate_quiz(scope, user, quiz_id)
    return success_response(data, request_id=get_request_id())


@student_lms_router.get("/me/lms/progress", response_model=ApiResponse[list[LearningProgressRead]])
async def student_lms_progress_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[LearningProgressRead]]:
    data = await learning_progress(scope, user)
    return success_response(data, request_id=get_request_id())


@student_lms_router.get("/me/lms/assessment-progress", response_model=ApiResponse[list[AssessmentProgressRead]])
async def student_lms_assessment_progress_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[AssessmentProgressRead]]:
    data = await lms_assessment_progress(scope, user)
    return success_response(data, request_id=get_request_id())


@student_lms_router.get("/me/lms/notifications", response_model=ApiResponse[Page[dict]])
async def student_lms_notifications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    data = await lms_notifications(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@student_lms_router.get("/me/lms/preferences", response_model=ApiResponse[dict])
async def student_lms_preferences_get_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[dict]:
    return success_response(await get_lms_preferences(scope, user), request_id=get_request_id())


@student_lms_router.patch("/me/lms/preferences", response_model=ApiResponse[dict])
async def student_lms_preferences_patch_route(
    payload: LmsPreferencesUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[dict]:
    return success_response(
        await update_lms_preferences(
            scope,
            user,
            group_by_unit=payload.group_by_unit,
            show_recorded=payload.show_recorded_lectures,
        ),
        request_id=get_request_id(),
    )
