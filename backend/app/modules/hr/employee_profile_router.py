"""HR employee profile routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hr.deps import hr_staff_user
from app.modules.hr.employee_profile_schemas import (
    EmployeeListItem,
    EmployeeProfileRead,
    EmployeeProfileUpdate,
    EmployeeRegister,
    EmployeeSearchQuery,
    EmploymentStatusChange,
    ProfileChangeHistoryItem,
    ProfileCorrectionRead,
    ProfileCorrectionReview,
    ProfileCorrectionSubmit,
    ProfileVerificationDecision,
)
from app.modules.hr.employee_profile_service import (
    change_employment_status,
    decide_profile_verification,
    get_employee_profile,
    list_pending_corrections,
    profile_change_history,
    register_employee,
    review_profile_correction,
    search_employees,
    submit_profile_correction,
    update_employee_profile,
)

router = APIRouter(prefix="/employees", tags=["hr-employees"])


@router.post("", response_model=ApiResponse[EmployeeProfileRead], status_code=status.HTTP_201_CREATED)
async def register_employee_route(
    payload: EmployeeRegister,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await register_employee(scope, payload), request_id=get_request_id())


@router.get("/search", response_model=ApiResponse[Page[EmployeeListItem]])
async def search_employees_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    employee_code: str | None = None,
    name: str | None = None,
    official_email: str | None = None,
    mobile_number: str | None = None,
    department_id: str | None = None,
    designation: str | None = None,
    campus_id: str | None = None,
    employment_type: str | None = None,
    employment_status: str | None = None,
    probation_only: bool = False,
):
    from app.modules.college_admin.faculty_admin_models import FacultyEmploymentStatus

    query = EmployeeSearchQuery(
        employee_code=employee_code,
        name=name,
        official_email=official_email,
        mobile_number=mobile_number,
        department_id=department_id,
        designation=designation,
        campus_id=campus_id,
        employment_type=employment_type,
        employment_status=FacultyEmploymentStatus(employment_status) if employment_status else None,
        probation_only=probation_only,
    )
    return success_response(await search_employees(scope, query, pagination), request_id=get_request_id())


@router.get("/corrections/pending", response_model=ApiResponse[Page[ProfileCorrectionRead]])
async def pending_corrections_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await list_pending_corrections(scope, pagination), request_id=get_request_id())


@router.post("/me/corrections", response_model=ApiResponse[ProfileCorrectionRead], status_code=status.HTTP_201_CREATED)
async def submit_correction_route(
    payload: ProfileCorrectionSubmit,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await submit_profile_correction(scope, user, payload), request_id=get_request_id())


@router.get("/{profile_id}", response_model=ApiResponse[EmployeeProfileRead])
async def get_employee_profile_route(
    profile_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await get_employee_profile(scope, profile_id), request_id=get_request_id())


@router.patch("/{profile_id}", response_model=ApiResponse[EmployeeProfileRead])
async def update_employee_profile_route(
    profile_id: str,
    payload: EmployeeProfileUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await update_employee_profile(scope, profile_id, payload), request_id=get_request_id())


@router.post("/{profile_id}/verification", response_model=ApiResponse[EmployeeProfileRead])
async def verify_profile_route(
    profile_id: str,
    payload: ProfileVerificationDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await decide_profile_verification(scope, profile_id, payload), request_id=get_request_id())


@router.post("/{profile_id}/employment-status", response_model=ApiResponse[EmployeeProfileRead])
async def employment_status_route(
    profile_id: str,
    payload: EmploymentStatusChange,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await change_employment_status(scope, profile_id, payload), request_id=get_request_id())


@router.get("/{profile_id}/history", response_model=ApiResponse[Page[ProfileChangeHistoryItem]])
async def profile_history_route(
    profile_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
):
    return success_response(await profile_change_history(scope, profile_id, pagination), request_id=get_request_id())


@router.post("/corrections/{correction_id}/review", response_model=ApiResponse[ProfileCorrectionRead])
async def review_correction_route(
    correction_id: str,
    payload: ProfileCorrectionReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hr_staff_user)],
):
    return success_response(await review_profile_correction(scope, correction_id, payload), request_id=get_request_id())