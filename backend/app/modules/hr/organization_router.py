"""HR organization routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.identity_schemas import DepartmentHeadAssign, InstitutionDepartmentCreate, InstitutionDepartmentRead, InstitutionDepartmentUpdate
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.organization_schemas import (
    AssignmentHistoryItem,
    DepartmentEmployeesRead,
    EmployeeAssignmentRead,
    EmployeeAssignmentUpdate,
    EmployeeTransferCreate,
    EmployeeTransferRead,
    HrDesignationCreate,
    HrDesignationRead,
    HrDesignationUpdate,
    HrEmploymentClassificationRead,
    HrEmploymentClassificationUpsert,
    HrWorkLocationCreate,
    HrWorkLocationRead,
    OrganizationOverview,
    ReportingHierarchyRead,
    ReportingManagerUpdate,
    TransferApproval,
)
from app.modules.hr.organization_service import (
    assignment_history,
    create_transfer_request,
    create_work_location,
    department_employees,
    get_employee_assignment,
    get_organization_overview,
    get_reporting_hierarchy,
    hr_assign_department_head,
    hr_create_department,
    hr_department_history,
    hr_get_department,
    hr_list_departments,
    hr_update_department,
    list_designations,
    list_employment_classifications,
    list_work_locations,
    process_due_transfers,
    review_transfer,
    update_designation,
    update_employee_assignment,
    update_reporting_manager,
    upsert_designation,
    upsert_employment_classification,
)

router = APIRouter(prefix="/organization", tags=["hr-organization"])


@router.get("/overview", response_model=ApiResponse[OrganizationOverview])
async def organization_overview_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await get_organization_overview(scope), request_id=get_request_id())


@router.post("/departments", response_model=ApiResponse[InstitutionDepartmentRead])
async def create_department_route(
    payload: InstitutionDepartmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await hr_create_department(scope, payload), request_id=get_request_id())


@router.get("/departments", response_model=ApiResponse[Page[InstitutionDepartmentRead]])
async def list_departments_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await hr_list_departments(scope, pagination), request_id=get_request_id())


@router.get("/departments/{department_id}", response_model=ApiResponse[InstitutionDepartmentRead])
async def get_department_route(department_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await hr_get_department(scope, department_id), request_id=get_request_id())


@router.patch("/departments/{department_id}", response_model=ApiResponse[InstitutionDepartmentRead])
async def update_department_route(
    department_id: str,
    payload: InstitutionDepartmentUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await hr_update_department(scope, department_id, payload), request_id=get_request_id())


@router.post("/departments/{department_id}/head", response_model=ApiResponse[InstitutionDepartmentRead])
async def department_head_route(
    department_id: str,
    payload: DepartmentHeadAssign,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await hr_assign_department_head(scope, department_id, payload), request_id=get_request_id())


@router.get("/departments/{department_id}/employees", response_model=ApiResponse[DepartmentEmployeesRead])
async def department_employees_route(
    department_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await department_employees(scope, department_id, pagination), request_id=get_request_id())


@router.get("/departments/{department_id}/history", response_model=ApiResponse[list])
async def department_history_route(department_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await hr_department_history(scope, department_id), request_id=get_request_id())


@router.post("/designations", response_model=ApiResponse[HrDesignationRead])
async def upsert_designation_route(payload: HrDesignationCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await upsert_designation(scope, payload), request_id=get_request_id())


@router.get("/designations", response_model=ApiResponse[Page[HrDesignationRead]])
async def list_designations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await list_designations(scope, pagination), request_id=get_request_id())


@router.patch("/designations/{designation_id}", response_model=ApiResponse[HrDesignationRead])
async def update_designation_route(
    designation_id: str,
    payload: HrDesignationUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await update_designation(scope, designation_id, payload), request_id=get_request_id())


@router.get("/classifications", response_model=ApiResponse[list[HrEmploymentClassificationRead]])
async def list_classifications_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await list_employment_classifications(scope), request_id=get_request_id())


@router.put("/classifications", response_model=ApiResponse[HrEmploymentClassificationRead])
async def upsert_classification_route(
    payload: HrEmploymentClassificationUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await upsert_employment_classification(scope, payload), request_id=get_request_id())


@router.post("/work-locations", response_model=ApiResponse[HrWorkLocationRead])
async def create_work_location_route(
    payload: HrWorkLocationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await create_work_location(scope, payload), request_id=get_request_id())


@router.get("/work-locations", response_model=ApiResponse[Page[HrWorkLocationRead]])
async def list_work_locations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await list_work_locations(scope, pagination), request_id=get_request_id())


@router.get("/employees/{employee_user_id}/assignment", response_model=ApiResponse[EmployeeAssignmentRead])
async def get_assignment_route(employee_user_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await get_employee_assignment(scope, employee_user_id), request_id=get_request_id())


@router.patch("/employees/{employee_user_id}/assignment", response_model=ApiResponse[EmployeeAssignmentRead])
async def update_assignment_route(
    employee_user_id: str,
    payload: EmployeeAssignmentUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await update_employee_assignment(scope, employee_user_id, payload), request_id=get_request_id())


@router.put("/employees/{employee_user_id}/reporting-manager", response_model=ApiResponse[EmployeeAssignmentRead])
async def reporting_manager_route(
    employee_user_id: str,
    payload: ReportingManagerUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await update_reporting_manager(scope, employee_user_id, payload), request_id=get_request_id())


@router.get("/employees/{employee_user_id}/reporting-hierarchy", response_model=ApiResponse[ReportingHierarchyRead])
async def reporting_hierarchy_route(employee_user_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await get_reporting_hierarchy(scope, employee_user_id), request_id=get_request_id())


@router.get("/employees/{employee_user_id}/assignment-history", response_model=ApiResponse[Page[AssignmentHistoryItem]])
async def assignment_history_route(
    employee_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await assignment_history(scope, employee_user_id, pagination), request_id=get_request_id())


@router.post("/employees/{employee_user_id}/transfers", response_model=ApiResponse[EmployeeTransferRead])
async def create_transfer_route(
    employee_user_id: str,
    payload: EmployeeTransferCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await create_transfer_request(scope, employee_user_id, payload), request_id=get_request_id())


@router.post("/transfers/{transfer_id}/review", response_model=ApiResponse[EmployeeTransferRead])
async def review_transfer_route(
    transfer_id: str,
    payload: TransferApproval,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await review_transfer(scope, transfer_id, payload), request_id=get_request_id())


@router.post("/transfers/process-due", response_model=ApiResponse[dict])
async def process_due_transfers_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(hr_staff_user)]):
    return success_response(await process_due_transfers(scope), request_id=get_request_id())