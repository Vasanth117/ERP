"""Library & branch management routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.library.deps import librarian_user
from app.modules.library.facility_enums import LibraryConfigEntityType
from app.modules.library.facility_schemas import (
    BranchOperationalStats,
    InstitutionLibraryCreate,
    InstitutionLibraryRead,
    InstitutionLibraryUpdate,
    LibraryBranchCreate,
    LibraryBranchRead,
    LibraryBranchUpdate,
    LibraryConfigurationHistoryRead,
    LibraryHolidayCreate,
    LibraryHolidayRead,
    LibraryHolidayUpdate,
    LibrarySectionCreate,
    LibrarySectionRead,
    LibrarySectionUpdate,
    LibraryShelfLocationCreate,
    LibraryShelfLocationRead,
    LibraryShelfLocationUpdate,
    LibraryStaffAssignmentCreate,
    LibraryStaffAssignmentRead,
    LibraryStaffAssignmentUpdate,
    OperatingHoursRead,
    OperatingHoursUpsert,
)
from app.modules.library.facility_service import (
    branch_operational_stats,
    create_branch_facility,
    create_holiday,
    create_library,
    create_section,
    create_shelf_location,
    create_staff_assignment,
    get_branch,
    get_holiday,
    get_library,
    get_operating_hours,
    list_branches,
    list_configuration_history,
    list_holidays,
    list_libraries,
    list_sections,
    list_shelf_locations,
    list_staff_assignments,
    update_branch,
    update_holiday,
    update_library,
    update_section,
    update_shelf_location,
    update_staff_assignment,
    upsert_operating_hours,
)

router = APIRouter(prefix="/facility", tags=["library-facility"])


@router.post("/libraries", response_model=ApiResponse[InstitutionLibraryRead], status_code=status.HTTP_201_CREATED)
async def create_library_route(
    payload: InstitutionLibraryCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[InstitutionLibraryRead]:
    return success_response(await create_library(scope, payload), request_id=get_request_id())


@router.get("/libraries", response_model=ApiResponse[Page[InstitutionLibraryRead]])
async def list_libraries_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[InstitutionLibraryRead]]:
    return success_response(await list_libraries(scope, pagination), request_id=get_request_id())


@router.get("/libraries/{library_code}", response_model=ApiResponse[InstitutionLibraryRead])
async def get_library_route(
    library_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[InstitutionLibraryRead]:
    return success_response(await get_library(scope, library_code), request_id=get_request_id())


@router.patch("/libraries/{library_code}", response_model=ApiResponse[InstitutionLibraryRead])
async def update_library_route(
    library_code: str,
    payload: InstitutionLibraryUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[InstitutionLibraryRead]:
    return success_response(await update_library(scope, library_code, payload), request_id=get_request_id())


@router.post("/branches", response_model=ApiResponse[LibraryBranchRead], status_code=status.HTTP_201_CREATED)
async def create_branch_route(
    payload: LibraryBranchCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryBranchRead]:
    return success_response(await create_branch_facility(scope, payload), request_id=get_request_id())


@router.get("/branches", response_model=ApiResponse[Page[LibraryBranchRead]])
async def list_branches_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    library_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[LibraryBranchRead]]:
    return success_response(await list_branches(scope, pagination, library_code=library_code), request_id=get_request_id())


@router.get("/branches/{branch_code}", response_model=ApiResponse[LibraryBranchRead])
async def get_branch_route(
    branch_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryBranchRead]:
    return success_response(await get_branch(scope, branch_code), request_id=get_request_id())


@router.patch("/branches/{branch_code}", response_model=ApiResponse[LibraryBranchRead])
async def update_branch_route(
    branch_code: str,
    payload: LibraryBranchUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryBranchRead]:
    return success_response(await update_branch(scope, branch_code, payload), request_id=get_request_id())


@router.get("/branches/{branch_code}/statistics", response_model=ApiResponse[BranchOperationalStats])
async def branch_statistics_route(
    branch_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[BranchOperationalStats]:
    return success_response(await branch_operational_stats(scope, branch_code), request_id=get_request_id())


@router.put("/operating-hours", response_model=ApiResponse[OperatingHoursRead])
async def operating_hours_upsert_route(
    payload: OperatingHoursUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[OperatingHoursRead]:
    return success_response(await upsert_operating_hours(scope, payload), request_id=get_request_id())


@router.get("/operating-hours", response_model=ApiResponse[OperatingHoursRead])
async def operating_hours_get_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    library_code: Annotated[str, Query()],
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[OperatingHoursRead]:
    return success_response(await get_operating_hours(scope, library_code=library_code, branch_code=branch_code), request_id=get_request_id())


@router.post("/holidays", response_model=ApiResponse[LibraryHolidayRead], status_code=status.HTTP_201_CREATED)
async def create_holiday_route(
    payload: LibraryHolidayCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryHolidayRead]:
    return success_response(await create_holiday(scope, payload), request_id=get_request_id())


@router.get("/holidays", response_model=ApiResponse[Page[LibraryHolidayRead]])
async def list_holidays_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    library_code: Annotated[str | None, Query()] = None,
    branch_code: Annotated[str | None, Query()] = None,
    active_only: Annotated[bool, Query()] = True,
) -> ApiResponse[Page[LibraryHolidayRead]]:
    return success_response(
        await list_holidays(scope, pagination, library_code=library_code, branch_code=branch_code, active_only=active_only),
        request_id=get_request_id(),
    )


@router.get("/holidays/{holiday_id}", response_model=ApiResponse[LibraryHolidayRead])
async def get_holiday_route(
    holiday_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryHolidayRead]:
    return success_response(await get_holiday(scope, holiday_id), request_id=get_request_id())


@router.patch("/holidays/{holiday_id}", response_model=ApiResponse[LibraryHolidayRead])
async def update_holiday_route(
    holiday_id: str,
    payload: LibraryHolidayUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryHolidayRead]:
    return success_response(await update_holiday(scope, holiday_id, payload), request_id=get_request_id())


@router.post("/staff-assignments", response_model=ApiResponse[LibraryStaffAssignmentRead], status_code=status.HTTP_201_CREATED)
async def staff_assignment_create_route(
    payload: LibraryStaffAssignmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryStaffAssignmentRead]:
    return success_response(await create_staff_assignment(scope, payload), request_id=get_request_id())


@router.patch("/staff-assignments/{assignment_id}", response_model=ApiResponse[LibraryStaffAssignmentRead])
async def staff_assignment_update_route(
    assignment_id: str,
    payload: LibraryStaffAssignmentUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryStaffAssignmentRead]:
    return success_response(await update_staff_assignment(scope, assignment_id, payload), request_id=get_request_id())


@router.get("/staff-assignments", response_model=ApiResponse[Page[LibraryStaffAssignmentRead]])
async def staff_assignments_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    library_code: Annotated[str | None, Query()] = None,
    branch_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[LibraryStaffAssignmentRead]]:
    return success_response(
        await list_staff_assignments(scope, pagination, library_code=library_code, branch_code=branch_code),
        request_id=get_request_id(),
    )


@router.post("/sections", response_model=ApiResponse[LibrarySectionRead], status_code=status.HTTP_201_CREATED)
async def section_create_route(
    payload: LibrarySectionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibrarySectionRead]:
    return success_response(await create_section(scope, payload), request_id=get_request_id())


@router.patch("/sections/{branch_code}/{section_code}", response_model=ApiResponse[LibrarySectionRead])
async def section_update_route(
    branch_code: str,
    section_code: str,
    payload: LibrarySectionUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibrarySectionRead]:
    return success_response(await update_section(scope, branch_code, section_code, payload), request_id=get_request_id())


@router.get("/sections", response_model=ApiResponse[Page[LibrarySectionRead]])
async def sections_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str, Query()],
) -> ApiResponse[Page[LibrarySectionRead]]:
    return success_response(await list_sections(scope, pagination, branch_code=branch_code), request_id=get_request_id())


@router.post("/shelf-locations", response_model=ApiResponse[LibraryShelfLocationRead], status_code=status.HTTP_201_CREATED)
async def shelf_location_create_route(
    payload: LibraryShelfLocationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryShelfLocationRead]:
    return success_response(await create_shelf_location(scope, payload), request_id=get_request_id())


@router.patch("/shelf-locations/{branch_code}/{location_code}", response_model=ApiResponse[LibraryShelfLocationRead])
async def shelf_location_update_route(
    branch_code: str,
    location_code: str,
    payload: LibraryShelfLocationUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
) -> ApiResponse[LibraryShelfLocationRead]:
    return success_response(await update_shelf_location(scope, branch_code, location_code, payload), request_id=get_request_id())


@router.get("/shelf-locations", response_model=ApiResponse[Page[LibraryShelfLocationRead]])
async def shelf_locations_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    branch_code: Annotated[str, Query()],
) -> ApiResponse[Page[LibraryShelfLocationRead]]:
    return success_response(await list_shelf_locations(scope, pagination, branch_code=branch_code), request_id=get_request_id())


@router.get("/configuration-history", response_model=ApiResponse[Page[LibraryConfigurationHistoryRead]])
async def configuration_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(librarian_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    entity_type: Annotated[LibraryConfigEntityType | None, Query()] = None,
    entity_key: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[LibraryConfigurationHistoryRead]]:
    return success_response(
        await list_configuration_history(scope, pagination, entity_type=entity_type, entity_key=entity_key),
        request_id=get_request_id(),
    )