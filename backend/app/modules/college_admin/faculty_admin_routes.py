"""College admin faculty & employee routes (dashboard and page APIs under /faculty-administration)."""

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
from app.modules.college_admin.schemas import (
    AddNewFacultyEmployeeCreatePayload,
    AddNewFacultyEmployeeCreateResult,
    AddNewFacultyEmployeeDraftUpdate,
    AddNewFacultyEmployeePageRead,
    EmployeeDirectoryPageRead,
    DepartmentDesignationAssignmentPageRead,
    DepartmentDesignationAssignmentSavePayload,
    EmployeeDocumentVerificationDecisionPayload,
    EmployeeDocumentVerificationPageRead,
    EmployeeDocumentVerificationVerifyAllPayload,
    EmployeeProfileManagementPageRead,
    EmployeeStatusApprovePayload,
    EmployeeStatusChangeSubmitPayload,
    EmployeeStatusManagementPageRead,
    FacultyEmployeeHistoryPageRead,
    EmployeeProfileManagementSavePayload,
    FacultyDirectoryPageRead,
    FacultySubjectAllocationConfirmPayload,
    FacultySubjectAllocationFilterPayload,
    FacultySubjectAllocationPageRead,
    FacultyTimetablePageRead,
    FacultyWorkloadManagementPageRead,
    FacultyWorkloadRebalancePayload,
    FacultyProfilePageRead,
)
from app.modules.college_admin.add_new_faculty_employee_page_service import (
    create_add_new_faculty_employee,
    get_add_new_faculty_employee_page,
    save_add_new_faculty_employee_draft,
)
from app.modules.college_admin.employee_directory_page_service import get_employee_directory_page
from app.modules.college_admin.employee_document_verification_page_service import (
    get_employee_document_verification_page,
    save_employee_document_decision,
    verify_all_employee_documents,
)
from app.modules.college_admin.employee_status_management_page_service import (
    approve_employee_status_change,
    get_employee_status_management_page,
    submit_employee_status_change,
)
from app.modules.college_admin.faculty_employee_history_page_service import get_faculty_employee_history_page
from app.modules.college_admin.department_designation_assignment_page_service import (
    get_department_designation_assignment_page,
    save_department_designation_assignment,
)
from app.modules.college_admin.employee_profile_management_page_service import (
    get_employee_profile_management_page,
    save_employee_profile_management,
)
from app.modules.college_admin.faculty_subject_allocation_page_service import (
    auto_suggest_faculty_subject_allocation,
    confirm_faculty_subject_allocation,
    get_faculty_subject_allocation_page,
)
from app.modules.college_admin.faculty_timetable_page_service import get_faculty_timetable_page
from app.modules.college_admin.faculty_workload_management_page_service import (
    get_faculty_workload_management_page,
    rebalance_faculty_workload_page,
)
from app.modules.college_admin.faculty_directory_page_service import get_faculty_directory_page
from app.modules.college_admin.faculty_profile_page_service import get_faculty_profile_page
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




@router.get("/faculty/profile/page", response_model=ApiResponse[FacultyProfilePageRead])
async def faculty_profile_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    record_id: str,
) -> ApiResponse[FacultyProfilePageRead]:
    return success_response(
        await get_faculty_profile_page(scope, record_id),
        request_id=get_request_id(),
    )


@router.get("/faculty/directory/page", response_model=ApiResponse[FacultyDirectoryPageRead])
async def faculty_directory_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    search: str | None = None,
    department_id: str | None = None,
    designation: str | None = None,
    status_filter: str | None = None,
    academic_year_code: str | None = None,
) -> ApiResponse[FacultyDirectoryPageRead]:
    return success_response(
        await get_faculty_directory_page(
            scope,
            page=page,
            search=search,
            department_id=department_id or None,
            designation=designation or None,
            status_filter=status_filter or None,
            academic_year_code=academic_year_code or None,
        ),
        request_id=get_request_id(),
    )


@router.get("/employees/new/page", response_model=ApiResponse[AddNewFacultyEmployeePageRead])
async def add_new_faculty_employee_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AddNewFacultyEmployeePageRead]:
    return success_response(
        await get_add_new_faculty_employee_page(scope),
        request_id=get_request_id(),
    )


@router.put("/employees/new/draft", response_model=ApiResponse[AddNewFacultyEmployeePageRead])
async def add_new_faculty_employee_draft_route(
    payload: AddNewFacultyEmployeeDraftUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AddNewFacultyEmployeePageRead]:
    return success_response(
        await save_add_new_faculty_employee_draft(scope, payload),
        request_id=get_request_id(),
    )


@router.post(
    "/employees/new/create",
    response_model=ApiResponse[AddNewFacultyEmployeeCreateResult],
    status_code=status.HTTP_201_CREATED,
)
async def add_new_faculty_employee_create_route(
    payload: AddNewFacultyEmployeeCreatePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AddNewFacultyEmployeeCreateResult]:
    return success_response(
        await create_add_new_faculty_employee(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/employees/profile-management/page", response_model=ApiResponse[EmployeeProfileManagementPageRead])
async def employee_profile_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    record_id: str | None = None,
) -> ApiResponse[EmployeeProfileManagementPageRead]:
    return success_response(
        await get_employee_profile_management_page(scope, record_id),
        request_id=get_request_id(),
    )


@router.post("/employees/profile-management/save", response_model=ApiResponse[EmployeeProfileManagementPageRead])
async def employee_profile_management_save_route(
    payload: EmployeeProfileManagementSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[EmployeeProfileManagementPageRead]:
    return success_response(
        await save_employee_profile_management(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/assignments/department-designation/page", response_model=ApiResponse[DepartmentDesignationAssignmentPageRead])
async def department_designation_assignment_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    record_id: str | None = None,
) -> ApiResponse[DepartmentDesignationAssignmentPageRead]:
    return success_response(
        await get_department_designation_assignment_page(scope, record_id),
        request_id=get_request_id(),
    )


@router.post(
    "/assignments/department-designation/save",
    response_model=ApiResponse[DepartmentDesignationAssignmentPageRead],
)
async def department_designation_assignment_save_route(
    payload: DepartmentDesignationAssignmentSavePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[DepartmentDesignationAssignmentPageRead]:
    return success_response(
        await save_department_designation_assignment(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/assignments/subject-allocation/page", response_model=ApiResponse[FacultySubjectAllocationPageRead])
async def faculty_subject_allocation_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    department_id: str | None = None,
) -> ApiResponse[FacultySubjectAllocationPageRead]:
    return success_response(
        await get_faculty_subject_allocation_page(
            scope,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
            department_id=department_id,
        ),
        request_id=get_request_id(),
    )


@router.post("/assignments/subject-allocation/auto-suggest", response_model=ApiResponse[FacultySubjectAllocationPageRead])
async def faculty_subject_allocation_auto_suggest_route(
    payload: FacultySubjectAllocationFilterPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FacultySubjectAllocationPageRead]:
    return success_response(
        await auto_suggest_faculty_subject_allocation(scope, payload),
        request_id=get_request_id(),
    )


@router.post(
    "/assignments/subject-allocation/confirm",
    response_model=ApiResponse[FacultySubjectAllocationPageRead],
)
async def faculty_subject_allocation_confirm_route(
    payload: FacultySubjectAllocationConfirmPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FacultySubjectAllocationPageRead]:
    return success_response(
        await confirm_faculty_subject_allocation(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/workload/management/page", response_model=ApiResponse[FacultyWorkloadManagementPageRead])
async def faculty_workload_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ApiResponse[FacultyWorkloadManagementPageRead]:
    return success_response(
        await get_faculty_workload_management_page(
            scope,
            page=page,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
        ),
        request_id=get_request_id(),
    )


@router.post("/workload/management/rebalance", response_model=ApiResponse[FacultyWorkloadManagementPageRead])
async def faculty_workload_rebalance_route(
    payload: FacultyWorkloadRebalancePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[FacultyWorkloadManagementPageRead]:
    return success_response(
        await rebalance_faculty_workload_page(scope, payload),
        request_id=get_request_id(),
    )


@router.get("/employees/status/page", response_model=ApiResponse[EmployeeStatusManagementPageRead])
async def employee_status_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    selected_request_id: str | None = None,
) -> ApiResponse[EmployeeStatusManagementPageRead]:
    return success_response(
        await get_employee_status_management_page(scope, page=page, selected_request_id=selected_request_id),
        request_id=get_request_id(),
    )


@router.post("/employees/status/submit", response_model=ApiResponse[EmployeeStatusManagementPageRead])
async def employee_status_submit_route(
    payload: EmployeeStatusChangeSubmitPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[EmployeeStatusManagementPageRead]:
    return success_response(await submit_employee_status_change(scope, payload), request_id=get_request_id())


@router.post("/employees/status/approve", response_model=ApiResponse[EmployeeStatusManagementPageRead])
async def employee_status_approve_route(
    payload: EmployeeStatusApprovePayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[EmployeeStatusManagementPageRead]:
    return success_response(
        await approve_employee_status_change(scope, request_id=payload.request_id, page=payload.page),
        request_id=get_request_id(),
    )


@router.get("/employees/history/page", response_model=ApiResponse[FacultyEmployeeHistoryPageRead])
async def faculty_employee_history_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
) -> ApiResponse[FacultyEmployeeHistoryPageRead]:
    return success_response(
        await get_faculty_employee_history_page(scope, page=page),
        request_id=get_request_id(),
    )


@router.get("/employees/documents/verification/page", response_model=ApiResponse[EmployeeDocumentVerificationPageRead])
async def employee_document_verification_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    document_id: str | None = None,
) -> ApiResponse[EmployeeDocumentVerificationPageRead]:
    return success_response(
        await get_employee_document_verification_page(scope, document_id=document_id),
        request_id=get_request_id(),
    )


@router.post(
    "/employees/documents/verification/decide",
    response_model=ApiResponse[EmployeeDocumentVerificationPageRead],
)
async def employee_document_verification_decide_route(
    payload: EmployeeDocumentVerificationDecisionPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[EmployeeDocumentVerificationPageRead]:
    return success_response(
        await save_employee_document_decision(scope, payload),
        request_id=get_request_id(),
    )


@router.post(
    "/employees/documents/verification/verify-all",
    response_model=ApiResponse[EmployeeDocumentVerificationPageRead],
)
async def employee_document_verification_verify_all_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    payload: EmployeeDocumentVerificationVerifyAllPayload | None = None,
) -> ApiResponse[EmployeeDocumentVerificationPageRead]:
    return success_response(
        await verify_all_employee_documents(scope, payload or EmployeeDocumentVerificationVerifyAllPayload()),
        request_id=get_request_id(),
    )


@router.get("/timetable/page", response_model=ApiResponse[FacultyTimetablePageRead])
async def faculty_timetable_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    record_id: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ApiResponse[FacultyTimetablePageRead]:
    return success_response(
        await get_faculty_timetable_page(
            scope,
            record_id,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
        ),
        request_id=get_request_id(),
    )


@router.get("/employees/directory/page", response_model=ApiResponse[EmployeeDirectoryPageRead])
async def employee_directory_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: int = 1,
    search: str | None = None,
    unit_id: str | None = None,
    role: str | None = None,
    type_filter: str | None = None,
    status_filter: str | None = None,
) -> ApiResponse[EmployeeDirectoryPageRead]:
    return success_response(
        await get_employee_directory_page(
            scope,
            page=page,
            search=search,
            unit_id=unit_id or None,
            role=role or None,
            type_filter=type_filter or None,
            status_filter=status_filter or None,
        ),
        request_id=get_request_id(),
    )


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
