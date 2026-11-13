"""College admin faculty & employee routes."""

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
from app.modules.college_admin.faculty_admin_schemas import (
    BulkFacultyImport,
    DepartmentAssignmentCreate,
    FacultyDocumentCreate,
    FacultyHistoryRead,
    FacultyRecordCreate,
    FacultyRecordRead,
    FacultyRecordUpdate,
    FacultyTransferCreate,
    TeachingAssignmentCreate,
    WorkloadAllocate,
)
from app.modules.college_admin.faculty_admin_service import (
    add_faculty_document,
    assign_department,
    assign_teaching,
    allocate_workload,
    bulk_import_faculty,
    create_faculty_record,
    faculty_history,
    get_faculty_record,
    get_workload,
    list_faculty_records,
    process_faculty_transfer,
    update_faculty_record,
)

router = APIRouter()


@router.post("/faculty", response_model=ApiResponse[FacultyRecordRead], status_code=status.HTTP_201_CREATED)
async def create_faculty_route(
    payload: FacultyRecordCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FacultyRecordRead]:
    return success_response(await create_faculty_record(scope, payload), request_id=get_request_id())


@router.get("/faculty", response_model=ApiResponse[Page[FacultyRecordRead]])
async def list_faculty_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[FacultyRecordRead]]:
    return success_response(await list_faculty_records(scope, pagination), request_id=get_request_id())


@router.get("/faculty/{record_id}", response_model=ApiResponse[FacultyRecordRead])
async def get_faculty_route(
    record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FacultyRecordRead]:
    return success_response(await get_faculty_record(scope, to_object_id(record_id, "record_id")), request_id=get_request_id())


@router.patch("/faculty/{record_id}", response_model=ApiResponse[FacultyRecordRead])
async def update_faculty_route(
    record_id: str,
    payload: FacultyRecordUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FacultyRecordRead]:
    return success_response(await update_faculty_record(scope, to_object_id(record_id, "record_id"), payload), request_id=get_request_id())


@router.post("/faculty/{record_id}/departments", response_model=ApiResponse[dict])
async def assign_department_route(
    record_id: str,
    payload: DepartmentAssignmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await assign_department(scope, to_object_id(record_id, "record_id"), payload), request_id=get_request_id())


@router.post("/faculty/{record_id}/teaching", response_model=ApiResponse[dict])
async def assign_teaching_route(
    record_id: str,
    payload: TeachingAssignmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await assign_teaching(scope, to_object_id(record_id, "record_id"), payload), request_id=get_request_id())


@router.post("/faculty/{record_id}/workload", response_model=ApiResponse[dict])
async def allocate_workload_route(
    record_id: str,
    payload: WorkloadAllocate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await allocate_workload(scope, to_object_id(record_id, "record_id"), payload), request_id=get_request_id())


@router.get("/faculty/{record_id}/workload", response_model=ApiResponse[dict])
async def get_workload_route(
    record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_label: Annotated[str, Query()],
    semester_label: Annotated[str, Query()],
) -> ApiResponse[dict]:
    return success_response(
        await get_workload(scope, to_object_id(record_id, "record_id"), academic_year_label=academic_year_label, semester_label=semester_label),
        request_id=get_request_id(),
    )


@router.post("/faculty/{record_id}/transfer", response_model=ApiResponse[dict])
async def transfer_faculty_route(
    record_id: str,
    payload: FacultyTransferCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await process_faculty_transfer(scope, to_object_id(record_id, "record_id"), payload), request_id=get_request_id())


@router.post("/faculty/{record_id}/documents", response_model=ApiResponse[dict])
async def faculty_document_route(
    record_id: str,
    payload: FacultyDocumentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await add_faculty_document(scope, to_object_id(record_id, "record_id"), payload), request_id=get_request_id())


@router.get("/faculty/{record_id}/history", response_model=ApiResponse[FacultyHistoryRead])
async def faculty_history_route(
    record_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FacultyHistoryRead]:
    return success_response(await faculty_history(scope, to_object_id(record_id, "record_id")), request_id=get_request_id())


@router.post("/faculty/bulk", response_model=ApiResponse[list[FacultyRecordRead]])
async def bulk_faculty_route(
    payload: BulkFacultyImport,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[FacultyRecordRead]]:
    return success_response(await bulk_import_faculty(scope, payload), request_id=get_request_id())
