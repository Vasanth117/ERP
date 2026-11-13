"""Student laboratory, practical and model examination routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.deps import student_user
from app.modules.students.examination_portal_schemas import (
    LaboratoryAttendanceRead,
    LaboratorySubjectRead,
    MarksCorrectionStudentRead,
    ModelExamMarkRead,
    ModelExamScheduleRead,
    PracticalComponentRead,
    PracticalExamHistoryItemRead,
    PracticalFeedbackRead,
    PracticalMarkRead,
    PracticalScheduleRead,
    UnpublishedPracticalMarkRead,
)
from app.modules.students.practical_examination_service import (
    get_laboratory_attendance,
    get_laboratory_subjects,
    get_model_examination_schedules,
    get_practical_assessment_details,
    get_practical_correction_status,
    get_practical_examination_history,
    get_practical_feedback,
    get_practical_schedules,
    get_published_model_marks,
    get_published_practical_marks,
    get_unpublished_practical_marks,
)

practical_examination_router = APIRouter()


@practical_examination_router.get("/me/laboratory/subjects", response_model=ApiResponse[list[LaboratorySubjectRead]])
async def student_laboratory_subjects_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[LaboratorySubjectRead]]:
    data = await get_laboratory_subjects(scope, user)
    return success_response(data, request_id=get_request_id())


@practical_examination_router.get("/me/practical/schedules", response_model=ApiResponse[list[PracticalScheduleRead]])
async def student_practical_schedules_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[PracticalScheduleRead]]:
    data = await get_practical_schedules(scope, user)
    return success_response(data, request_id=get_request_id())


@practical_examination_router.get("/me/practical/components", response_model=ApiResponse[list[PracticalComponentRead]])
async def student_practical_components_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[PracticalComponentRead]]:
    data = await get_practical_assessment_details(scope, user)
    return success_response(data, request_id=get_request_id())


@practical_examination_router.get("/me/practical/marks", response_model=ApiResponse[list[PracticalMarkRead]])
async def student_practical_marks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[PracticalMarkRead]]:
    data = await get_published_practical_marks(scope, user)
    return success_response(data, request_id=get_request_id())


@practical_examination_router.get("/me/practical/marks/unpublished", response_model=ApiResponse[list[UnpublishedPracticalMarkRead]])
async def student_unpublished_practical_marks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[UnpublishedPracticalMarkRead]]:
    data = await get_unpublished_practical_marks(scope, user)
    return success_response(data, request_id=get_request_id())


@practical_examination_router.get("/me/model-examinations/schedules", response_model=ApiResponse[list[ModelExamScheduleRead]])
async def student_model_exam_schedules_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ModelExamScheduleRead]]:
    data = await get_model_examination_schedules(scope, user)
    return success_response(data, request_id=get_request_id())


@practical_examination_router.get("/me/model-examinations/marks", response_model=ApiResponse[list[ModelExamMarkRead]])
async def student_model_exam_marks_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[ModelExamMarkRead]]:
    data = await get_published_model_marks(scope, user)
    return success_response(data, request_id=get_request_id())


@practical_examination_router.get(
    "/me/practical/feedback/{assessment_id}/{component_id}",
    response_model=ApiResponse[PracticalFeedbackRead],
)
async def student_practical_feedback_route(
    assessment_id: str,
    component_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[PracticalFeedbackRead]:
    data = await get_practical_feedback(scope, user, assessment_id, component_id)
    return success_response(data, request_id=get_request_id())


@practical_examination_router.get("/me/laboratory/attendance", response_model=ApiResponse[list[LaboratoryAttendanceRead]])
async def student_laboratory_attendance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[list[LaboratoryAttendanceRead]]:
    data = await get_laboratory_attendance(scope, user)
    return success_response(data, request_id=get_request_id())


@practical_examination_router.get("/me/practical/history", response_model=ApiResponse[Page[PracticalExamHistoryItemRead]])
async def student_practical_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[PracticalExamHistoryItemRead]]:
    data = await get_practical_examination_history(scope, user, pagination)
    return success_response(data, request_id=get_request_id())


@practical_examination_router.get("/me/practical/corrections", response_model=ApiResponse[Page[MarksCorrectionStudentRead]])
async def student_practical_corrections_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[MarksCorrectionStudentRead]]:
    data = await get_practical_correction_status(scope, user, pagination)
    return success_response(data, request_id=get_request_id())
