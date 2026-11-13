"""College admin student administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.student_admin_schemas import (
    AdmissionCreate,
    AdmissionRead,
    BulkStudentImport,
    EnrollmentAssign,
    GuardianCreate,
    ProfileCorrectionDecision,
    PromotionCreate,
    StudentAcademicHistoryRead,
    StudentRecordCreate,
    StudentRecordRead,
    StudentRecordUpdate,
    StudentStatusChange,
    TransferCreate,
)
from app.modules.college_admin.student_admin_service import (
    add_guardian,
    bulk_import_students,
    change_student_status,
    confirm_admission,
    create_admission,
    create_student_record,
    decide_profile_correction,
    enroll_student,
    get_student_record,
    list_admissions,
    list_student_records,
    process_promotion,
    process_transfer,
    student_academic_history,
    update_student_record,
)

router = APIRouter()


@router.post("/admissions", response_model=ApiResponse[AdmissionRead], status_code=status.HTTP_201_CREATED)
async def create_admission_route(
    payload: AdmissionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AdmissionRead]:
    return success_response(await create_admission(scope, payload), request_id=get_request_id())


@router.get("/admissions", response_model=ApiResponse[Page[AdmissionRead]])
async def list_admissions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AdmissionRead]]:
    return success_response(await list_admissions(scope, pagination), request_id=get_request_id())


@router.post("/admissions/{admission_id}/confirm", response_model=ApiResponse[AdmissionRead])
async def confirm_admission_route(
    admission_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AdmissionRead]:
    return success_response(await confirm_admission(scope, to_object_id(admission_id, "admission id")), request_id=get_request_id())


@router.post("/students", response_model=ApiResponse[StudentRecordRead], status_code=status.HTTP_201_CREATED)
async def create_student_route(
    payload: StudentRecordCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentRecordRead]:
    return success_response(await create_student_record(scope, payload), request_id=get_request_id())


@router.get("/students", response_model=ApiResponse[Page[StudentRecordRead]])
async def list_students_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[StudentRecordRead]]:
    return success_response(await list_student_records(scope, pagination), request_id=get_request_id())


@router.get("/students/{record_id}", response_model=ApiResponse[StudentRecordRead])
async def get_student_route(
    record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentRecordRead]:
    return success_response(await get_student_record(scope, to_object_id(record_id, "record id")), request_id=get_request_id())


@router.patch("/students/{record_id}", response_model=ApiResponse[StudentRecordRead])
async def update_student_route(
    record_id: str,
    payload: StudentRecordUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentRecordRead]:
    return success_response(await update_student_record(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.post("/students/{record_id}/status", response_model=ApiResponse[StudentRecordRead])
async def status_change_route(
    record_id: str,
    payload: StudentStatusChange,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentRecordRead]:
    return success_response(await change_student_status(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.post("/students/{record_id}/enrollments", response_model=ApiResponse[dict])
async def enroll_route(
    record_id: str,
    payload: EnrollmentAssign,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await enroll_student(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.post("/students/{record_id}/transfer", response_model=ApiResponse[dict])
async def transfer_route(
    record_id: str,
    payload: TransferCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await process_transfer(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.post("/students/{record_id}/promotion", response_model=ApiResponse[dict])
async def promotion_route(
    record_id: str,
    payload: PromotionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await process_promotion(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.post("/students/{record_id}/guardians", response_model=ApiResponse[dict])
async def guardian_route(
    record_id: str,
    payload: GuardianCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await add_guardian(scope, to_object_id(record_id, "record id"), payload), request_id=get_request_id())


@router.get("/students/{record_id}/academic-history", response_model=ApiResponse[StudentAcademicHistoryRead])
async def academic_history_route(
    record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[StudentAcademicHistoryRead]:
    return success_response(await student_academic_history(scope, to_object_id(record_id, "record id")), request_id=get_request_id())


@router.post("/students/bulk", response_model=ApiResponse[list[StudentRecordRead]])
async def bulk_import_route(
    payload: BulkStudentImport,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[StudentRecordRead]]:
    return success_response(await bulk_import_students(scope, payload), request_id=get_request_id())


@router.post("/profile-corrections/decide", response_model=ApiResponse[dict])
async def profile_correction_route(
    payload: ProfileCorrectionDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await decide_profile_correction(scope, payload), request_id=get_request_id())
