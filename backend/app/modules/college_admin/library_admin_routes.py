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
from app.modules.college_admin.schemas import (
    LibraryBookAcquisitionPageRead,
    LibraryBookCataloguePageRead,
    LibraryBookInventoryPageRead,
    LibraryBranchManagementPageRead,
    LibraryCirculationIssueReturnPageRead,
    LibraryDashboardPageRead,
    LibraryDigitalLibraryPageRead,
    LibraryFineManagementPageRead,
    LibraryLostDamagedPageRead,
    LibraryMemberManagementPageRead,
    LibraryReportsPageRead,
    LibraryReservationManagementPageRead,
    LibrarySectionSubNavRead,
    LibrarySettingsPageRead,
    LibrarySettingsSave,
)
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
from app.modules.college_admin.library_book_acquisition_page_service import get_library_book_acquisition_page
from app.modules.college_admin.library_book_catalogue_page_service import get_library_book_catalogue_page
from app.modules.college_admin.library_book_inventory_page_service import get_library_book_inventory_page
from app.modules.college_admin.library_branch_management_page_service import get_library_branch_management_page
from app.modules.college_admin.library_circulation_issue_return_page_service import (
    get_library_circulation_issue_return_page,
)
from app.modules.college_admin.library_dashboard_page_service import get_library_dashboard_page
from app.modules.college_admin.library_digital_library_page_service import get_library_digital_library_page
from app.modules.college_admin.library_fine_management_page_service import get_library_fine_management_page
from app.modules.college_admin.library_lost_damaged_page_service import get_library_lost_damaged_page
from app.modules.college_admin.library_member_management_page_service import get_library_member_management_page
from app.modules.college_admin.library_reports_page_service import get_library_reports_page
from app.modules.college_admin.library_reservation_management_page_service import (
    get_library_reservation_management_page,
)
from app.modules.college_admin.library_settings_page_service import (
    get_library_settings_page,
    save_library_settings_page,
)
from app.modules.college_admin.library_section_sub_nav_service import get_library_section_sub_nav
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


@router.get("/reports/management/page", response_model=ApiResponse[LibraryReportsPageRead])
async def library_reports_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[LibraryReportsPageRead]:
    return success_response(
        await get_library_reports_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/settings/management/page", response_model=ApiResponse[LibrarySettingsPageRead])
async def library_settings_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LibrarySettingsPageRead]:
    return success_response(await get_library_settings_page(scope), request_id=get_request_id())


@router.put("/settings/management/page", response_model=ApiResponse[LibrarySettingsPageRead])
async def library_settings_page_save_route(
    payload: LibrarySettingsSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LibrarySettingsPageRead]:
    return success_response(await save_library_settings_page(scope, payload), request_id=get_request_id())


@router.get("/digital/management/page", response_model=ApiResponse[LibraryDigitalLibraryPageRead])
async def library_digital_library_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[LibraryDigitalLibraryPageRead]:
    return success_response(
        await get_library_digital_library_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/navigation/section-sub-nav", response_model=ApiResponse[LibrarySectionSubNavRead])
async def library_section_sub_nav_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    path: Annotated[str, Query(min_length=1)],
) -> ApiResponse[LibrarySectionSubNavRead]:
    return success_response(await get_library_section_sub_nav(scope, path=path), request_id=get_request_id())


@router.get("/dashboard/page", response_model=ApiResponse[LibraryDashboardPageRead])
async def library_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[LibraryDashboardPageRead]:
    return success_response(
        await get_library_dashboard_page(scope, user, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/branches/management/page", response_model=ApiResponse[LibraryBranchManagementPageRead])
async def library_branch_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[LibraryBranchManagementPageRead]:
    return success_response(
        await get_library_branch_management_page(scope),
        request_id=get_request_id(),
    )


@router.get("/catalogue/management/page", response_model=ApiResponse[LibraryBookCataloguePageRead])
async def library_book_catalogue_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
    search: Annotated[str | None, Query()] = None,
    category: Annotated[str | None, Query()] = None,
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[LibraryBookCataloguePageRead]:
    return success_response(
        await get_library_book_catalogue_page(
            scope,
            user,
            page=page,
            page_size=page_size,
            search=search,
            category=category,
            branch_code=branch_code,
        ),
        request_id=get_request_id(),
    )


@router.get("/inventory/management/page", response_model=ApiResponse[LibraryBookInventoryPageRead])
async def library_book_inventory_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[LibraryBookInventoryPageRead]:
    return success_response(
        await get_library_book_inventory_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/members/management/page", response_model=ApiResponse[LibraryMemberManagementPageRead])
async def library_member_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[LibraryMemberManagementPageRead]:
    return success_response(
        await get_library_member_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/fines/management/page", response_model=ApiResponse[LibraryFineManagementPageRead])
async def library_fine_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[LibraryFineManagementPageRead]:
    return success_response(
        await get_library_fine_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/lost-damaged/management/page", response_model=ApiResponse[LibraryLostDamagedPageRead])
async def library_lost_damaged_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[LibraryLostDamagedPageRead]:
    return success_response(
        await get_library_lost_damaged_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/circulation/management/page", response_model=ApiResponse[LibraryCirculationIssueReturnPageRead])
async def library_circulation_issue_return_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[LibraryCirculationIssueReturnPageRead]:
    return success_response(
        await get_library_circulation_issue_return_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/reservations/management/page", response_model=ApiResponse[LibraryReservationManagementPageRead])
async def library_reservation_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[LibraryReservationManagementPageRead]:
    return success_response(
        await get_library_reservation_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/acquisitions/management/page", response_model=ApiResponse[LibraryBookAcquisitionPageRead])
async def library_book_acquisition_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
) -> ApiResponse[LibraryBookAcquisitionPageRead]:
    return success_response(
        await get_library_book_acquisition_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


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
