"""Department Admin phase 3 — class structure and student administration."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.department_admin.class_management_service import (
    class_strength,
    class_structure,
    create_batch,
    create_section,
    get_batch,
    get_section,
    list_batches,
    list_sections,
    update_batch,
    update_section,
)
from app.modules.department_admin.section_transfer_service import (
    create_section_transfer,
    get_section_transfer,
    list_section_transfers,
    review_section_transfer,
)
from app.modules.department_admin.deps import department_admin_user
from app.modules.department_admin.phase3_schemas import (
    BatchCreate,
    BatchRead,
    BatchUpdate,
    ClassStrengthSummary,
    ClassStructureNode,
    EnrollmentSummaryRead,
    SectionCreate,
    SectionRead,
    SectionTransferCreate,
    SectionTransferRead,
    SectionTransferReview,
    SectionUpdate,
    StudentAcademicProfileRead,
    StudentCorrectionCreate,
    StudentCorrectionRead,
    StudentCorrectionReview,
    StudentDirectoryFilters,
    StudentDirectoryItem,
    StudentFollowUpCreate,
    StudentFollowUpRead,
    StudentFollowUpUpdate,
)
from app.modules.department_admin.student_administration_service import (
    create_correction_request,
    create_follow_up,
    enrollment_summary,
    get_correction_request,
    get_student,
    get_student_academic_profile,
    list_correction_requests,
    list_follow_ups,
    list_students,
    list_unallocated_students,
    review_correction_request,
    update_follow_up,
)

phase3_router = APIRouter()


def _student_filters(
    programme_code: Annotated[str | None, Query()] = None,
    batch_label: Annotated[str | None, Query()] = None,
    section_code: Annotated[str | None, Query()] = None,
    semester_label: Annotated[str | None, Query()] = None,
    enrollment_status: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> StudentDirectoryFilters:
    return StudentDirectoryFilters(
        programme_code=programme_code,
        batch_label=batch_label,
        section_code=section_code,
        semester_label=semester_label,
        enrollment_status=enrollment_status,
        search=search,
    )


@phase3_router.get("/batches", response_model=ApiResponse[Page[BatchRead]])
async def batches_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[BatchRead]]:
    data = await list_batches(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase3_router.post("/batches", response_model=ApiResponse[BatchRead])
async def batches_create_route(
    payload: BatchCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[BatchRead]:
    data = await create_batch(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/batches/{batch_id}", response_model=ApiResponse[BatchRead])
async def batches_get_route(
    batch_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[BatchRead]:
    data = await get_batch(scope, user, batch_id)
    return success_response(data, request_id=get_request_id())


@phase3_router.patch("/batches/{batch_id}", response_model=ApiResponse[BatchRead])
async def batches_update_route(
    batch_id: str,
    payload: BatchUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[BatchRead]:
    data = await update_batch(scope, user, batch_id, payload)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/batches/{batch_id}/sections", response_model=ApiResponse[list[SectionRead]])
async def batch_sections_route(
    batch_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[SectionRead]]:
    data = await list_sections(scope, user, batch_id)
    return success_response(data, request_id=get_request_id())


@phase3_router.post("/batches/{batch_id}/sections", response_model=ApiResponse[SectionRead])
async def batch_sections_create_route(
    batch_id: str,
    payload: SectionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[SectionRead]:
    data = await create_section(scope, user, batch_id, payload)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/sections/{section_id}", response_model=ApiResponse[SectionRead])
async def sections_get_route(
    section_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[SectionRead]:
    data = await get_section(scope, user, section_id)
    return success_response(data, request_id=get_request_id())


@phase3_router.patch("/sections/{section_id}", response_model=ApiResponse[SectionRead])
async def sections_update_route(
    section_id: str,
    payload: SectionUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[SectionRead]:
    data = await update_section(scope, user, section_id, payload)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/classes/structure", response_model=ApiResponse[list[ClassStructureNode]])
async def classes_structure_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[ClassStructureNode]]:
    data = await class_structure(scope, user)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/classes/strength", response_model=ApiResponse[list[ClassStrengthSummary]])
async def classes_strength_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[ClassStrengthSummary]]:
    data = await class_strength(scope, user)
    return success_response(data, request_id=get_request_id())


@phase3_router.post("/section-transfer-requests", response_model=ApiResponse[SectionTransferRead])
async def section_transfer_create_route(
    payload: SectionTransferCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[SectionTransferRead]:
    data = await create_section_transfer(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/section-transfer-requests", response_model=ApiResponse[Page[SectionTransferRead]])
async def section_transfer_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[SectionTransferRead]]:
    data = await list_section_transfers(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/section-transfer-requests/{request_id}", response_model=ApiResponse[SectionTransferRead])
async def section_transfer_get_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[SectionTransferRead]:
    data = await get_section_transfer(scope, user, request_id)
    return success_response(data, request_id=get_request_id())


@phase3_router.post("/section-transfer-requests/{request_id}/review", response_model=ApiResponse[SectionTransferRead])
async def section_transfer_review_route(
    request_id: str,
    payload: SectionTransferReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[SectionTransferRead]:
    data = await review_section_transfer(scope, user, request_id, payload)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/students", response_model=ApiResponse[Page[StudentDirectoryItem]])
async def students_directory_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    filters: Annotated[StudentDirectoryFilters, Depends(_student_filters)],
) -> ApiResponse[Page[StudentDirectoryItem]]:
    data = await list_students(scope, user, pagination=pagination, filters=filters)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/students/enrollment-summary", response_model=ApiResponse[EnrollmentSummaryRead])
async def students_enrollment_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[EnrollmentSummaryRead]:
    data = await enrollment_summary(scope, user)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/students/unallocated", response_model=ApiResponse[Page[StudentDirectoryItem]])
async def students_unallocated_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[StudentDirectoryItem]]:
    data = await list_unallocated_students(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/students/{student_id}", response_model=ApiResponse[StudentDirectoryItem])
async def students_get_route(
    student_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[StudentDirectoryItem]:
    data = await get_student(scope, user, student_id)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/students/{student_id}/academic-profile", response_model=ApiResponse[StudentAcademicProfileRead])
async def students_academic_profile_route(
    student_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[StudentAcademicProfileRead]:
    data = await get_student_academic_profile(scope, user, student_id)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/student-correction-requests", response_model=ApiResponse[Page[StudentCorrectionRead]])
async def student_corrections_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[StudentCorrectionRead]]:
    data = await list_correction_requests(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase3_router.post("/student-correction-requests", response_model=ApiResponse[StudentCorrectionRead])
async def student_corrections_create_route(
    payload: StudentCorrectionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[StudentCorrectionRead]:
    data = await create_correction_request(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/student-correction-requests/{request_id}", response_model=ApiResponse[StudentCorrectionRead])
async def student_corrections_get_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[StudentCorrectionRead]:
    data = await get_correction_request(scope, user, request_id)
    return success_response(data, request_id=get_request_id())


@phase3_router.post("/student-correction-requests/{request_id}/review", response_model=ApiResponse[StudentCorrectionRead])
async def student_corrections_review_route(
    request_id: str,
    payload: StudentCorrectionReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[StudentCorrectionRead]:
    data = await review_correction_request(scope, user, request_id, payload)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/student-follow-ups", response_model=ApiResponse[Page[StudentFollowUpRead]])
async def student_follow_ups_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[StudentFollowUpRead]]:
    data = await list_follow_ups(scope, user, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@phase3_router.post("/student-follow-ups", response_model=ApiResponse[StudentFollowUpRead])
async def student_follow_ups_create_route(
    payload: StudentFollowUpCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[StudentFollowUpRead]:
    data = await create_follow_up(scope, user, payload)
    return success_response(data, request_id=get_request_id())


@phase3_router.patch("/student-follow-ups/{follow_up_id}", response_model=ApiResponse[StudentFollowUpRead])
async def student_follow_ups_update_route(
    follow_up_id: str,
    payload: StudentFollowUpUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[StudentFollowUpRead]:
    data = await update_follow_up(scope, user, follow_up_id, payload)
    return success_response(data, request_id=get_request_id())