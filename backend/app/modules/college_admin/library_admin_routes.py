"""College admin library administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.library_admin_schemas import (
    AcquisitionCreate,
    BookCopyCreate,
    BorrowingPolicyUpsert,
    CatalogueCreate,
    CirculationIssue,
    CirculationReturn,
    FineDecision,
    LibraryBranchCreate,
    ReservationFulfill,
)
from app.modules.college_admin.library_admin_service import (
    add_book_copy,
    add_digital_resource,
    create_acquisition,
    create_branch,
    decide_fine,
    fulfill_reservation,
    issue_book,
    library_report,
    list_circulation,
    return_book,
    set_membership,
    upsert_borrowing_policy,
    upsert_catalogue,
)

router = APIRouter()


@router.post("/branches", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def branch_route(
    payload: LibraryBranchCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_branch(scope, payload), request_id=get_request_id())


@router.post("/catalogue", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def catalogue_route(
    payload: CatalogueCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_catalogue(scope, payload), request_id=get_request_id())


@router.post("/copies", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def copy_route(
    payload: BookCopyCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await add_book_copy(scope, payload), request_id=get_request_id())


@router.put("/borrowing-policies", response_model=ApiResponse[dict])
async def borrowing_policy_route(
    payload: BorrowingPolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await upsert_borrowing_policy(scope, payload), request_id=get_request_id())


@router.post("/membership", response_model=ApiResponse[dict])
async def membership_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    member_user_id: Annotated[str, Query()],
    eligible: Annotated[bool, Query()] = True,
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await set_membership(scope, member_user_id, branch_code=branch_code, eligible=eligible), request_id=get_request_id())


@router.post("/circulation/issue", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def issue_route(
    payload: CirculationIssue,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await issue_book(scope, payload), request_id=get_request_id())


@router.post("/circulation/return", response_model=ApiResponse[dict])
async def return_route(
    payload: CirculationReturn,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await return_book(scope, payload), request_id=get_request_id())


@router.get("/circulation", response_model=ApiResponse[Page[dict]])
async def circulation_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[dict]]:
    return success_response(await list_circulation(scope, pagination, branch_code=branch_code), request_id=get_request_id())


@router.post("/reservations/fulfill", response_model=ApiResponse[dict])
async def reservation_route(
    payload: ReservationFulfill,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await fulfill_reservation(scope, payload), request_id=get_request_id())


@router.post("/fines/decide", response_model=ApiResponse[dict])
async def fine_route(
    payload: FineDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await decide_fine(scope, payload), request_id=get_request_id())


@router.post("/acquisitions", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def acquisition_route(
    payload: AcquisitionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await create_acquisition(scope, payload), request_id=get_request_id())


@router.post("/digital-resources", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def digital_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    resource_id: Annotated[str, Query()],
    title: Annotated[str, Query()],
    url: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await add_digital_resource(scope, resource_id=resource_id, title=title, url=url), request_id=get_request_id())


@router.get("/reports/summary", response_model=ApiResponse[dict])
async def library_report_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[dict]:
    return success_response(await library_report(scope, branch_code=branch_code), request_id=get_request_id())
