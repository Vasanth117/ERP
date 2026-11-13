"""College Admin dashboard and institution routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.dashboard_service import (
    get_dashboard_overview,
    get_institutional_statistics,
    get_operational_summaries,
    get_pending_approvals,
    get_recent_activities,
)
from app.modules.college_admin.deps import college_admin_user, institution_settings_rate_limit
from app.modules.college_admin.enums import DashboardDateRange
from app.modules.college_admin.institution_service import (
    create_campus,
    get_campus,
    get_configuration_history,
    get_institution_profile,
    get_institution_settings,
    list_campuses,
    update_campus,
    update_institution_profile,
    update_institution_settings,
)
from app.modules.college_admin.schemas import (
    ActivitySummary,
    CampusCreate,
    CampusRead,
    CampusUpdate,
    CollegeDashboardOverview,
    CollegeDashboardStatsRead,
    InstitutionConfigurationHistoryItem,
    InstitutionProfileRead,
    InstitutionProfileUpdate,
    InstitutionSettingsRead,
    OperationalSummariesRead,
    PendingApprovalItem,
)
from app.modules.college_admin.settings_registry import InstitutionBrandingUpdate, InstitutionSettingsUpdate
from app.modules.college_admin.academic_routes import router as academic_config_router
from app.modules.college_admin.student_admin_routes import router as student_admin_router
from app.modules.college_admin.faculty_admin_routes import router as faculty_admin_router
from app.modules.college_admin.attendance_admin_routes import router as attendance_admin_router
from app.modules.college_admin.examination_admin_routes import router as examination_admin_router
from app.modules.college_admin.finance_admin_routes import router as finance_admin_router
from app.modules.college_admin.hr_admin_routes import router as hr_admin_router
from app.modules.college_admin.library_admin_routes import router as library_admin_router

router = APIRouter()

router.include_router(academic_config_router, prefix="/academic-config", tags=["college-admin-academic-config"])
router.include_router(student_admin_router, prefix="/student-administration", tags=["college-admin-student-admin"])
router.include_router(faculty_admin_router, prefix="/faculty-administration", tags=["college-admin-faculty-admin"])
router.include_router(attendance_admin_router, prefix="/attendance-administration", tags=["college-admin-attendance-admin"])
router.include_router(examination_admin_router, prefix="/examination-administration", tags=["college-admin-examination-admin"])
router.include_router(finance_admin_router, prefix="/finance-administration", tags=["college-admin-finance-admin"])
router.include_router(hr_admin_router, prefix="/hr-administration", tags=["college-admin-hr-admin"])
router.include_router(library_admin_router, prefix="/library-administration", tags=["college-admin-library-admin"])


@router.get("/dashboard", response_model=ApiResponse[CollegeDashboardOverview])
async def dashboard_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(college_admin_user)],
    anchor_date: Annotated[date | None, Query(description="Dashboard anchor date (UTC calendar day)")] = None,
    date_range: Annotated[DashboardDateRange, Query(alias="range")] = DashboardDateRange.WEEK,
    department_id: Annotated[str | None, Query()] = None,
    campus_id: Annotated[str | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[CollegeDashboardOverview]:
    data = await get_dashboard_overview(
        scope,
        user,
        anchor_date=anchor_date,
        date_range=date_range,
        department_id=department_id,
        campus_id=campus_id,
        academic_year_label=academic_year_label,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/statistics", response_model=ApiResponse[CollegeDashboardStatsRead])
async def dashboard_statistics_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    department_id: Annotated[str | None, Query()] = None,
    academic_year_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[CollegeDashboardStatsRead]:
    data = await get_institutional_statistics(
        scope,
        department_id=department_id,
        academic_year_label=academic_year_label,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/operations", response_model=ApiResponse[OperationalSummariesRead])
async def dashboard_operations_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    academic_year_label: Annotated[str | None, Query()] = None,
) -> ApiResponse[OperationalSummariesRead]:
    data = await get_operational_summaries(scope, academic_year_label=academic_year_label)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/pending-approvals", response_model=ApiResponse[Page[PendingApprovalItem]])
async def dashboard_pending_approvals_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    department_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[Page[PendingApprovalItem]]:
    data = await get_pending_approvals(scope, department_id=department_id, pagination=pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/dashboard/activities", response_model=ApiResponse[Page[ActivitySummary]])
async def dashboard_activities_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    anchor_date: Annotated[date | None, Query()] = None,
    date_range: Annotated[DashboardDateRange, Query(alias="range")] = DashboardDateRange.WEEK,
) -> ApiResponse[Page[ActivitySummary]]:
    data = await get_recent_activities(
        scope,
        anchor_date=anchor_date,
        date_range=date_range,
        pagination=pagination,
    )
    return success_response(data, request_id=get_request_id())


@router.get("/institution/profile", response_model=ApiResponse[InstitutionProfileRead])
async def institution_profile_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionProfileRead]:
    data = await get_institution_profile(scope)
    return success_response(data, request_id=get_request_id())


@router.patch("/institution/profile", response_model=ApiResponse[InstitutionProfileRead])
async def institution_profile_update_route(
    payload: InstitutionProfileUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[InstitutionProfileRead]:
    data = await update_institution_profile(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/institution/campuses", response_model=ApiResponse[list[CampusRead]])
async def institution_campuses_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    active_only: Annotated[bool, Query()] = False,
) -> ApiResponse[list[CampusRead]]:
    data = await list_campuses(scope, active_only=active_only)
    return success_response(data, request_id=get_request_id())


@router.post("/institution/campuses", response_model=ApiResponse[CampusRead], status_code=status.HTTP_201_CREATED)
async def institution_campus_create_route(
    payload: CampusCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CampusRead]:
    data = await create_campus(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/institution/campuses/{campus_id}", response_model=ApiResponse[CampusRead])
async def institution_campus_detail_route(
    campus_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CampusRead]:
    data = await get_campus(scope, to_object_id(campus_id, "campus id"))
    return success_response(data, request_id=get_request_id())


@router.patch("/institution/campuses/{campus_id}", response_model=ApiResponse[CampusRead])
async def institution_campus_update_route(
    campus_id: str,
    payload: CampusUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CampusRead]:
    data = await update_campus(scope, to_object_id(campus_id, "campus id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/institution/settings", response_model=ApiResponse[InstitutionSettingsRead])
async def institution_settings_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionSettingsRead]:
    data = await get_institution_settings(scope)
    return success_response(data, request_id=get_request_id())


class InstitutionSettingsPatchBody(InstitutionSettingsUpdate):
    branding: InstitutionBrandingUpdate | None = None


@router.patch("/institution/settings", response_model=ApiResponse[InstitutionSettingsRead])
async def institution_settings_update_route(
    payload: InstitutionSettingsPatchBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    __: Annotated[None, Depends(institution_settings_rate_limit)],
) -> ApiResponse[InstitutionSettingsRead]:
    branding = payload.branding
    settings_payload = InstitutionSettingsUpdate(**payload.model_dump(exclude={"branding"}, exclude_none=True))
    data = await update_institution_settings(scope, settings_payload, branding=branding)
    return success_response(data, request_id=get_request_id())


@router.get("/institution/configuration-history", response_model=ApiResponse[list[InstitutionConfigurationHistoryItem]])
async def institution_configuration_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[InstitutionConfigurationHistoryItem]]:
    data = await get_configuration_history(scope)
    return success_response(data, request_id=get_request_id())


from app.modules.college_admin.identity_schemas import (
    AccessHistoryRead,
    AccountStatusChange,
    BulkUserCreate,
    DepartmentHeadAssign,
    DepartmentHistoryRead,
    DepartmentTransfer,
    InstitutionDepartmentCreate,
    InstitutionDepartmentRead,
    InstitutionDepartmentUpdate,
    InstitutionRoleCreate,
    InstitutionRoleRead,
    InstitutionRoleUpdate,
    InstitutionUserCreate,
    InstitutionUserInvite,
    InstitutionUserRead,
    InstitutionUserUpdate,
    InvitationAccept,
    InvitationCreateResponse,
    OrganizationUnitCreate,
    OrganizationUnitRead,
    PermissionRead,
    UserRoleAssign,
    UserRoleRevoke,
)
from app.modules.college_admin.organization_service import (
    assign_department_head,
    associate_department_staff,
    create_institution_department,
    create_organization_unit,
    get_department_history,
    get_institution_department,
    list_institution_departments,
    list_organization_units,
    transfer_department,
    update_institution_department,
)
from app.modules.college_admin.role_management_service import (
    create_institution_role,
    list_institution_roles,
    list_permissions,
    update_institution_role,
)
from app.modules.college_admin.user_management_service import (
    accept_institution_invitation,
    accept_password_reset,
    activate_user,
    assign_user_roles,
    bulk_create_users,
    create_institution_user,
    deactivate_user,
    get_institution_user,
    get_user_access_history,
    invite_institution_user,
    list_institution_users,
    reset_user_access,
    revoke_user_role,
    revoke_user_sessions,
    suspend_user,
    update_institution_user,
)


@router.post("/users", response_model=ApiResponse[InstitutionUserRead], status_code=status.HTTP_201_CREATED)
async def create_user_route(
    payload: InstitutionUserCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await create_institution_user(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/invite", response_model=ApiResponse[InvitationCreateResponse], status_code=status.HTTP_201_CREATED)
async def invite_user_route(
    payload: InstitutionUserInvite,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InvitationCreateResponse]:
    data = await invite_institution_user(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/invitations/accept", response_model=ApiResponse[InstitutionUserRead])
async def accept_invitation_route(payload: InvitationAccept) -> ApiResponse[InstitutionUserRead]:
    data = await accept_institution_invitation(payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/password-reset/accept", response_model=ApiResponse[dict])
async def accept_password_reset_route(payload: InvitationAccept) -> ApiResponse[dict]:
    data = await accept_password_reset(payload)
    return success_response(data, request_id=get_request_id())


@router.get("/users", response_model=ApiResponse[Page[InstitutionUserRead]])
async def list_users_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[InstitutionUserRead]]:
    data = await list_institution_users(scope, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/users/{user_id}", response_model=ApiResponse[InstitutionUserRead])
async def get_user_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await get_institution_user(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.patch("/users/{user_id}", response_model=ApiResponse[InstitutionUserRead])
async def update_user_route(
    user_id: str,
    payload: InstitutionUserUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await update_institution_user(scope, to_object_id(user_id, "user id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/activate", response_model=ApiResponse[InstitutionUserRead])
async def activate_user_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await activate_user(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/suspend", response_model=ApiResponse[InstitutionUserRead])
async def suspend_user_route(
    user_id: str,
    payload: AccountStatusChange,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await suspend_user(scope, to_object_id(user_id, "user id"), reason=payload.reason)
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/deactivate", response_model=ApiResponse[InstitutionUserRead])
async def deactivate_user_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await deactivate_user(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/roles", response_model=ApiResponse[InstitutionUserRead])
async def assign_roles_route(
    user_id: str,
    payload: UserRoleAssign,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await assign_user_roles(scope, to_object_id(user_id, "user id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/roles/revoke", response_model=ApiResponse[InstitutionUserRead])
async def revoke_role_route(
    user_id: str,
    payload: UserRoleRevoke,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionUserRead]:
    data = await revoke_user_role(scope, to_object_id(user_id, "user id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/sessions/revoke", response_model=ApiResponse[dict])
async def revoke_sessions_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    data = await revoke_user_sessions(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.post("/users/{user_id}/reset-access", response_model=ApiResponse[dict])
async def reset_access_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    data = await reset_user_access(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.post("/users/bulk", response_model=ApiResponse[list[InstitutionUserRead]])
async def bulk_users_route(
    payload: BulkUserCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[InstitutionUserRead]]:
    data = await bulk_create_users(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/users/{user_id}/access-history", response_model=ApiResponse[list[AccessHistoryRead]])
async def user_access_history_route(
    user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[AccessHistoryRead]]:
    data = await get_user_access_history(scope, to_object_id(user_id, "user id"))
    return success_response(data, request_id=get_request_id())


@router.get("/roles", response_model=ApiResponse[list[InstitutionRoleRead]])
async def list_roles_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[InstitutionRoleRead]]:
    data = await list_institution_roles(scope)
    return success_response(data, request_id=get_request_id())


@router.post("/roles", response_model=ApiResponse[InstitutionRoleRead], status_code=status.HTTP_201_CREATED)
async def create_role_route(
    payload: InstitutionRoleCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionRoleRead]:
    data = await create_institution_role(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.patch("/roles/{role_id}", response_model=ApiResponse[InstitutionRoleRead])
async def update_role_route(
    role_id: str,
    payload: InstitutionRoleUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionRoleRead]:
    data = await update_institution_role(scope, to_object_id(role_id, "role id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/permissions", response_model=ApiResponse[list[PermissionRead]])
async def list_permissions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[PermissionRead]]:
    data = await list_permissions(scope)
    return success_response(data, request_id=get_request_id())


@router.post("/organization/units", response_model=ApiResponse[OrganizationUnitRead], status_code=status.HTTP_201_CREATED)
async def create_org_unit_route(
    payload: OrganizationUnitCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[OrganizationUnitRead]:
    data = await create_organization_unit(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/organization/units", response_model=ApiResponse[list[OrganizationUnitRead]])
async def list_org_units_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[OrganizationUnitRead]]:
    data = await list_organization_units(scope)
    return success_response(data, request_id=get_request_id())


@router.post("/departments", response_model=ApiResponse[InstitutionDepartmentRead], status_code=status.HTTP_201_CREATED)
async def create_department_route(
    payload: InstitutionDepartmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionDepartmentRead]:
    data = await create_institution_department(scope, payload)
    return success_response(data, request_id=get_request_id())


@router.get("/departments", response_model=ApiResponse[Page[InstitutionDepartmentRead]])
async def list_departments_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[InstitutionDepartmentRead]]:
    data = await list_institution_departments(scope, pagination)
    return success_response(data, request_id=get_request_id())


@router.get("/departments/{department_id}", response_model=ApiResponse[InstitutionDepartmentRead])
async def get_department_route(
    department_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionDepartmentRead]:
    data = await get_institution_department(scope, to_object_id(department_id, "department id"))
    return success_response(data, request_id=get_request_id())


@router.patch("/departments/{department_id}", response_model=ApiResponse[InstitutionDepartmentRead])
async def update_department_route(
    department_id: str,
    payload: InstitutionDepartmentUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionDepartmentRead]:
    data = await update_institution_department(scope, to_object_id(department_id, "department id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/departments/{department_id}/head", response_model=ApiResponse[InstitutionDepartmentRead])
async def assign_head_route(
    department_id: str,
    payload: DepartmentHeadAssign,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionDepartmentRead]:
    data = await assign_department_head(scope, to_object_id(department_id, "department id"), payload)
    return success_response(data, request_id=get_request_id())


@router.post("/departments/{department_id}/transfer", response_model=ApiResponse[InstitutionDepartmentRead])
async def transfer_department_route(
    department_id: str,
    payload: DepartmentTransfer,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[InstitutionDepartmentRead]:
    data = await transfer_department(scope, to_object_id(department_id, "department id"), payload)
    return success_response(data, request_id=get_request_id())


@router.get("/departments/{department_id}/history", response_model=ApiResponse[list[DepartmentHistoryRead]])
async def department_history_route(
    department_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[DepartmentHistoryRead]]:
    data = await get_department_history(scope, to_object_id(department_id, "department id"))
    return success_response(data, request_id=get_request_id())


@router.post("/departments/{department_id}/staff/{staff_user_id}", response_model=ApiResponse[dict])
async def associate_staff_route(
    department_id: str,
    staff_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    data = await associate_department_staff(
        scope,
        to_object_id(department_id, "department id"),
        to_object_id(staff_user_id, "user id"),
    )
    return success_response(data, request_id=get_request_id())
