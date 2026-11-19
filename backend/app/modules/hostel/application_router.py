"""Hostel application and waiting list routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.hostel.application_schemas import (
    AllocationOfferCreate,
    HostelApplicationRead,
    HostelApplicationReviewInput,
    HostelApplicationStaffSubmit,
    WaitingListAdd,
    WaitingListPriorityUpdate,
)
from app.modules.hostel.application_service import get_application, list_applications, review_application, staff_submit_application
from app.modules.hostel.deps import hostel_admin_user
from app.modules.hostel.hostel_enums import HostelApplicationStatus
from app.modules.hostel.waiting_list_service import add_to_waiting_list, issue_allocation_offer, list_waiting_entries, update_waiting_priority

router = APIRouter(prefix="/me", tags=["hostel-applications"])


@router.get("/applications", response_model=ApiResponse[Page[HostelApplicationRead]])
async def list_applications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    status: Annotated[HostelApplicationStatus | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
    preferred_hostel_code: Annotated[str | None, Query()] = None,
    student_user_id: Annotated[str | None, Query()] = None,
):
    data = await list_applications(
        scope,
        pagination,
        status=status,
        academic_year_label=academic_year_label,
        preferred_hostel_code=preferred_hostel_code,
        student_user_id=student_user_id,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/applications/{application_id}", response_model=ApiResponse[HostelApplicationRead])
async def get_application_route(
    application_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await get_application(scope, application_id), request_id=get_request_id())


@router.post("/applications/staff", response_model=ApiResponse[HostelApplicationRead], status_code=status.HTTP_201_CREATED)
async def staff_submit_application_route(
    payload: HostelApplicationStaffSubmit,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await staff_submit_application(scope, payload), request_id=get_request_id())


@router.post("/applications/review", response_model=ApiResponse[HostelApplicationRead])
async def review_application_route(
    payload: HostelApplicationReviewInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await review_application(scope, payload), request_id=get_request_id())


@router.post("/waiting-list", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def waiting_list_add_route(
    payload: WaitingListAdd,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await add_to_waiting_list(scope, payload), request_id=get_request_id())


@router.get("/waiting-list", response_model=ApiResponse[Page[dict]])
async def waiting_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    list_id: Annotated[str | None, Query()] = None,
):
    return success_response(await list_waiting_entries(scope, pagination, list_id=list_id), request_id=get_request_id())


@router.post("/waiting-list/priority", response_model=ApiResponse[dict])
async def waiting_priority_route(
    payload: WaitingListPriorityUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await update_waiting_priority(scope, payload), request_id=get_request_id())


@router.post("/offers", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def issue_offer_route(
    payload: AllocationOfferCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(hostel_admin_user)],
):
    return success_response(await issue_allocation_offer(scope, payload), request_id=get_request_id())