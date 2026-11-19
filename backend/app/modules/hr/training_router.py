"""Training management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.modules.auth.models import User
from app.modules.hr.deps import employee_self_user, hr_staff_user
from app.modules.hr.training_schemas import (
    TrainingAssessmentSubmit,
    TrainingAttendanceUpsert,
    TrainingEnrollmentCreate,
    TrainingEnrollmentRead,
    TrainingEnrollmentReview,
    TrainingProgramRead,
    TrainingProgramUpsert,
)
from app.modules.hr.training_service import (
    complete_training_enrollment,
    create_training_enrollment,
    list_training_programs,
    record_training_attendance,
    review_training_enrollment,
    submit_training_assessment,
    upsert_training_program,
)

router = APIRouter(prefix="/training", tags=["hr-training"])


@router.post("/programs", response_model=ApiResponse[TrainingProgramRead])
async def upsert_program_route(payload: TrainingProgramUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_training_program(scope, payload), request_id=get_request_id())


@router.get("/programs", response_model=ApiResponse[list[TrainingProgramRead]])
async def list_programs_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_training_programs(scope), request_id=get_request_id())


@router.post("/enrollments", response_model=ApiResponse[TrainingEnrollmentRead])
async def hr_enroll_route(payload: TrainingEnrollmentCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await create_training_enrollment(scope, payload, self_service=False), request_id=get_request_id())


@router.post("/enrollments/{enrollment_id}/review", response_model=ApiResponse[TrainingEnrollmentRead])
async def review_enrollment_route(enrollment_id: str, payload: TrainingEnrollmentReview, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await review_training_enrollment(scope, enrollment_id, payload), request_id=get_request_id())


@router.post("/enrollments/{enrollment_id}/attendance", response_model=ApiResponse)
async def attendance_route(enrollment_id: str, payload: TrainingAttendanceUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await record_training_attendance(scope, enrollment_id, payload, self_service=False), request_id=get_request_id())


@router.post("/enrollments/{enrollment_id}/assessment", response_model=ApiResponse)
async def assessment_route(enrollment_id: str, payload: TrainingAssessmentSubmit, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await submit_training_assessment(scope, enrollment_id, payload), request_id=get_request_id())


@router.post("/enrollments/{enrollment_id}/complete", response_model=ApiResponse)
async def complete_route(enrollment_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await complete_training_enrollment(scope, enrollment_id), request_id=get_request_id())


@router.post("/self/enrollments", response_model=ApiResponse[TrainingEnrollmentRead])
async def self_enroll_route(payload: TrainingEnrollmentCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(employee_self_user)]):
    payload.employee_user_id = str(user.id)
    return success_response(await create_training_enrollment(scope, payload, self_service=True), request_id=get_request_id())


@router.post("/self/enrollments/{enrollment_id}/attendance", response_model=ApiResponse)
async def self_attendance_route(enrollment_id: str, payload: TrainingAttendanceUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(employee_self_user)]):
    return success_response(await record_training_attendance(scope, enrollment_id, payload, self_service=True), request_id=get_request_id())