"""College admin hostel administration routes."""

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
    HostelAdmissionApplicationsPageRead,
    HostelBedAllocationPageRead,
    HostelBuildingManagementPageRead,
    HostelCheckInCheckoutPageRead,
    HostelFeeManagementPageRead,
    HostelMessManagementPageRead,
    HostelLeaveOutpassApprovalPageRead,
    HostelResidentManagementPageRead,
    HostelReportsPageRead,
    HostelSettingsPageRead,
    HostelSettingsSave,
    HostelVisitorManagementPageRead,
    HostelDashboardPageRead,
    HostelManagementPageRead,
    HostelRoomManagementPageRead,
    HostelSectionSubNavRead,
)
from app.modules.college_admin.hostel_admin_schemas import (
    AllocationApprove,
    CheckInOut,
    HostelApplicationReview,
    HostelBedCreate,
    HostelBlockCreate,
    HostelBuildingCreate,
    HostelRoomCreate,
    HostelRuleUpsert,
    IncidentCreate,
    MaintenanceCreate,
    MessPlanUpsert,
    OutpassDecision,
    VisitorLogCreate,
)
from app.modules.college_admin.hostel_admission_applications_page_service import (
    get_hostel_admission_applications_page,
)
from app.modules.college_admin.hostel_bed_allocation_page_service import get_hostel_bed_allocation_page
from app.modules.college_admin.hostel_check_in_checkout_page_service import get_hostel_check_in_checkout_page
from app.modules.college_admin.hostel_fee_management_page_service import get_hostel_fee_management_page
from app.modules.college_admin.hostel_leave_outpass_approval_page_service import get_hostel_leave_outpass_approval_page
from app.modules.college_admin.hostel_mess_management_page_service import get_hostel_mess_management_page
from app.modules.college_admin.hostel_visitor_management_page_service import get_hostel_visitor_management_page
from app.modules.college_admin.hostel_reports_page_service import get_hostel_reports_page
from app.modules.college_admin.hostel_resident_management_page_service import get_hostel_resident_management_page
from app.modules.college_admin.hostel_settings_page_service import (
    get_hostel_settings_page,
    save_hostel_settings_page,
)
from app.modules.college_admin.hostel_building_management_page_service import get_hostel_building_management_page
from app.modules.college_admin.hostel_dashboard_page_service import get_hostel_dashboard_page
from app.modules.college_admin.hostel_room_management_page_service import get_hostel_room_management_page
from app.modules.college_admin.hostel_management_page_service import get_hostel_management_page
from app.modules.college_admin.hostel_section_sub_nav_service import get_hostel_section_sub_nav
from app.modules.college_admin.hostel_admin_service import (
    approve_allocation,
    check_in,
    check_out,
    create_bed,
    create_block,
    create_building,
    create_incident,
    create_maintenance,
    create_room,
    decide_outpass,
    list_waiting,
    log_visitor,
    occupancy_report,
    review_application,
    upsert_mess_plan,
    upsert_rule,
)

router = APIRouter()


@router.get("/navigation/section-sub-nav", response_model=ApiResponse[HostelSectionSubNavRead])
async def hostel_section_sub_nav_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    path: Annotated[str, Query()],
):
    return success_response(await get_hostel_section_sub_nav(scope, path=path), request_id=get_request_id())


@router.get("/dashboard/page", response_model=ApiResponse[HostelDashboardPageRead])
async def hostel_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
):
    return success_response(
        await get_hostel_dashboard_page(scope, user, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/buildings/management/page", response_model=ApiResponse[HostelBuildingManagementPageRead])
async def hostel_building_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
):
    return success_response(
        await get_hostel_building_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/rooms/management/page", response_model=ApiResponse[HostelRoomManagementPageRead])
async def hostel_room_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
    search: Annotated[str | None, Query()] = None,
    block_code: Annotated[str | None, Query()] = None,
    floor_id: Annotated[str | None, Query()] = None,
    room_type: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_hostel_room_management_page(
            scope,
            page=page,
            page_size=page_size,
            search=search,
            block_code=block_code,
            floor_id=floor_id,
            room_type=room_type,
        ),
        request_id=get_request_id(),
    )


@router.get("/visitors/management/page", response_model=ApiResponse[HostelVisitorManagementPageRead])
async def hostel_visitor_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_hostel_visitor_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/outpass/management/page", response_model=ApiResponse[HostelLeaveOutpassApprovalPageRead])
async def hostel_leave_outpass_approval_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
):
    return success_response(
        await get_hostel_leave_outpass_approval_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/fees/management/page", response_model=ApiResponse[HostelFeeManagementPageRead])
async def hostel_fee_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_hostel_fee_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/mess/management/page", response_model=ApiResponse[HostelMessManagementPageRead])
async def hostel_mess_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    return success_response(await get_hostel_mess_management_page(scope), request_id=get_request_id())


@router.get("/residents/management/page", response_model=ApiResponse[HostelResidentManagementPageRead])
async def hostel_resident_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
    search: Annotated[str | None, Query()] = None,
    block_code: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_hostel_resident_management_page(
            scope,
            page=page,
            page_size=page_size,
            search=search,
            block_code=block_code,
            status_filter=status_filter,
        ),
        request_id=get_request_id(),
    )


@router.get("/check-ins/management/page", response_model=ApiResponse[HostelCheckInCheckoutPageRead])
async def hostel_check_in_checkout_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_hostel_check_in_checkout_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/applications/management/page", response_model=ApiResponse[HostelAdmissionApplicationsPageRead])
async def hostel_admission_applications_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
    academic_year_label: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_hostel_admission_applications_page(
            scope,
            page=page,
            page_size=page_size,
            academic_year_label=academic_year_label,
        ),
        request_id=get_request_id(),
    )


@router.get("/allocations/management/page", response_model=ApiResponse[HostelBedAllocationPageRead])
async def hostel_bed_allocation_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
    academic_year_label: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_hostel_bed_allocation_page(
            scope,
            page=page,
            page_size=page_size,
            academic_year_label=academic_year_label,
        ),
        request_id=get_request_id(),
    )


@router.get("/reports/management/page", response_model=ApiResponse[HostelReportsPageRead])
async def hostel_reports_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_hostel_reports_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/settings/management/page", response_model=ApiResponse[HostelSettingsPageRead])
async def hostel_settings_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HostelSettingsPageRead]:
    return success_response(await get_hostel_settings_page(scope), request_id=get_request_id())


@router.put("/settings/management/page", response_model=ApiResponse[HostelSettingsPageRead])
async def hostel_settings_page_save_route(
    payload: HostelSettingsSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[HostelSettingsPageRead]:
    return success_response(await save_hostel_settings_page(scope, payload), request_id=get_request_id())


@router.get("/screens/{screen_slug}/management/page", response_model=ApiResponse[HostelManagementPageRead])
async def hostel_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    screen_slug: str,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 8,
):
    return success_response(
        await get_hostel_management_page(scope, screen_slug, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.post("/buildings", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def building_route(payload: HostelBuildingCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_building(scope, payload), request_id=get_request_id())


@router.post("/blocks", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def block_route(payload: HostelBlockCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_block(scope, payload), request_id=get_request_id())


@router.post("/rooms", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def room_route(payload: HostelRoomCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_room(scope, payload), request_id=get_request_id())


@router.post("/beds", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def bed_route(payload: HostelBedCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_bed(scope, payload), request_id=get_request_id())


@router.post("/applications/review", response_model=ApiResponse[dict])
async def application_review_route(payload: HostelApplicationReview, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await review_application(scope, payload), request_id=get_request_id())


@router.get("/waiting-list", response_model=ApiResponse[Page[dict]])
async def waiting_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)], pagination: Annotated[Pagination, Depends(pagination_params)]):
    return success_response(await list_waiting(scope, pagination), request_id=get_request_id())


@router.post("/allocations/approve", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def allocate_route(payload: AllocationApprove, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await approve_allocation(scope, payload), request_id=get_request_id())


@router.post("/check-in", response_model=ApiResponse[dict])
async def check_in_route(payload: CheckInOut, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await check_in(scope, payload), request_id=get_request_id())


@router.post("/check-out", response_model=ApiResponse[dict])
async def check_out_route(payload: CheckInOut, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await check_out(scope, payload), request_id=get_request_id())


@router.post("/visitors", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def visitor_route(payload: VisitorLogCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await log_visitor(scope, payload), request_id=get_request_id())


@router.post("/outpass/decide", response_model=ApiResponse[dict])
async def outpass_route(payload: OutpassDecision, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await decide_outpass(scope, payload), request_id=get_request_id())


@router.post("/maintenance", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def maintenance_route(payload: MaintenanceCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_maintenance(scope, payload), request_id=get_request_id())


@router.post("/incidents", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def incident_route(payload: IncidentCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_incident(scope, payload), request_id=get_request_id())


@router.put("/rules", response_model=ApiResponse[dict])
async def rule_route(payload: HostelRuleUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await upsert_rule(scope, payload), request_id=get_request_id())


@router.put("/mess-plans", response_model=ApiResponse[dict])
async def mess_route(payload: MessPlanUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await upsert_mess_plan(scope, payload), request_id=get_request_id())


@router.get("/reports/occupancy", response_model=ApiResponse[dict])
async def occupancy_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)], building_code: Annotated[str | None, Query()] = None):
    return success_response(await occupancy_report(scope, building_code=building_code), request_id=get_request_id())