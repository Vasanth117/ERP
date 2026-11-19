"""Parent / guardian portal routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.parents.dashboard_service import get_parent_dashboard
from app.modules.parents.deps import parent_linking_rate_limit, parent_profile_update_rate_limit, parent_user
from app.modules.parents.enums import ParentDashboardDateRange, ParentNotificationCategory
from app.modules.parents.linking_service import list_link_requests, resolve_student_reference, submit_link_request
from app.modules.parents.profile_service import (
    confirm_contact_verification,
    get_parent_profile,
    list_linked_relationships,
    recent_security_activity,
    request_deactivation,
    start_contact_verification,
    submit_profile_correction,
    update_communication_preferences,
    update_parent_profile,
)
from app.modules.parents.schemas import (
    ParentCommunicationPreferencesUpdate,
    ParentContactVerificationConfirm,
    ParentContactVerificationStart,
    ParentDashboardFilters,
    ParentDashboardRead,
    ParentDeactivationRequestInput,
    ParentLinkRequestCreate,
    ParentLinkRequestRead,
    ParentProfileCorrectionRequest,
    ParentProfileRead,
    ParentProfileUpdate,
    ParentRelationshipRead,
    StudentReferencePreview,
    StudentReferenceResolve,
)

from app.modules.parents.communication_router import router as communication_router
from app.modules.parents.meeting_router import router as meeting_router
from app.modules.parents.security_router import router as security_router
from app.modules.parents.enums import ParentReportCategory, ParentServiceRequestCategory
from app.modules.parents.phase5_schemas import ParentReportExportRead, ParentReportsDashboardRead
from app.modules.parents.reports_portal_service import build_report, reports_dashboard
from app.modules.parents.phase4_schemas import ParentServiceRequestTypesRead
from app.modules.parents.service_request_service import list_request_types
from app.modules.parents.student_router import router as student_router

router = APIRouter()
router.include_router(communication_router, prefix="/me/communications")
router.include_router(meeting_router, prefix="/me/meetings")
router.include_router(security_router, prefix="/me/security")
router.include_router(student_router, prefix="/me/students")


@router.get("/me/reports/dashboard", response_model=ApiResponse[ParentReportsDashboardRead])
async def parent_reports_dashboard_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentReportsDashboardRead]:
    return success_response(await reports_dashboard(scope, user), request_id=get_request_id())


@router.get("/me/reports/export", response_model=ApiResponse[ParentReportExportRead])
async def parent_report_export_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    category: ParentReportCategory,
    student_user_id: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    export_format: str = "json",
) -> ApiResponse[ParentReportExportRead]:
    return success_response(
        await build_report(
            scope,
            parent=user,
            student_user_id=student_user_id,
            category=category,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
            export_format=export_format,
        ),
        request_id=get_request_id(),
    )


@router.get("/me/service-request-types", response_model=ApiResponse[ParentServiceRequestTypesRead])
async def parent_service_request_types_route(
    category: ParentServiceRequestCategory,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentServiceRequestTypesRead]:
    return success_response(await list_request_types(scope, category), request_id=get_request_id())


@router.get("/me/dashboard", response_model=ApiResponse[ParentDashboardRead])
async def parent_dashboard_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    student_user_id: str | None = None,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    date_range: ParentDashboardDateRange = ParentDashboardDateRange.WEEK,
    notification_category: ParentNotificationCategory | None = None,
    request_status: str | None = None,
) -> ApiResponse[ParentDashboardRead]:
    filters = ParentDashboardFilters(
        student_user_id=student_user_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        date_range=date_range,
        notification_category=notification_category,
        request_status=request_status,
    )
    return success_response(
        await get_parent_dashboard(scope, user, filters),
        request_id=get_request_id(),
    )


@router.get("/me/profile", response_model=ApiResponse[ParentProfileRead])
async def parent_profile_get_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentProfileRead]:
    return success_response(await get_parent_profile(scope, user), request_id=get_request_id())


@router.patch("/me/profile", response_model=ApiResponse[ParentProfileRead])
async def parent_profile_patch_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentProfileUpdate,
    _: Annotated[None, Depends(parent_profile_update_rate_limit)],
) -> ApiResponse[ParentProfileRead]:
    return success_response(await update_parent_profile(scope, user, payload), request_id=get_request_id())


@router.patch("/me/profile/communication-preferences", response_model=ApiResponse[ParentProfileRead])
async def parent_comm_prefs_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentCommunicationPreferencesUpdate,
) -> ApiResponse[ParentProfileRead]:
    return success_response(await update_communication_preferences(scope, user, payload), request_id=get_request_id())


@router.post("/me/profile/contact-verification/start", response_model=ApiResponse[dict])
async def parent_verification_start_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentContactVerificationStart,
) -> ApiResponse[dict]:
    return success_response(await start_contact_verification(scope, user, payload), request_id=get_request_id())


@router.post("/me/profile/contact-verification/confirm", response_model=ApiResponse[ParentProfileRead])
async def parent_verification_confirm_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentContactVerificationConfirm,
) -> ApiResponse[ParentProfileRead]:
    return success_response(await confirm_contact_verification(scope, user, payload), request_id=get_request_id())


@router.post("/me/profile/correction-requests", response_model=ApiResponse[dict])
async def parent_correction_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentProfileCorrectionRequest,
) -> ApiResponse[dict]:
    return success_response(await submit_profile_correction(scope, user, payload), request_id=get_request_id())


@router.post("/me/profile/deactivation-requests", response_model=ApiResponse[dict])
async def parent_deactivation_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentDeactivationRequestInput,
) -> ApiResponse[dict]:
    return success_response(await request_deactivation(scope, user, payload), request_id=get_request_id())


@router.get("/me/profile/security-activity", response_model=ApiResponse[Page[dict]])
async def parent_security_activity_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await recent_security_activity(scope, user, pagination), request_id=get_request_id())


@router.get("/me/relationships", response_model=ApiResponse[list[ParentRelationshipRead]])
async def parent_relationships_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentRelationshipRead]]:
    return success_response(await list_linked_relationships(scope, user), request_id=get_request_id())


@router.post("/me/linking/resolve-reference", response_model=ApiResponse[StudentReferencePreview])
async def parent_resolve_reference_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: StudentReferenceResolve,
    _: Annotated[None, Depends(parent_linking_rate_limit)],
) -> ApiResponse[StudentReferencePreview]:
    return success_response(await resolve_student_reference(scope, user, payload), request_id=get_request_id())


@router.post("/me/linking/requests", response_model=ApiResponse[ParentLinkRequestRead])
async def parent_link_request_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    payload: ParentLinkRequestCreate,
    _: Annotated[None, Depends(parent_linking_rate_limit)],
) -> ApiResponse[ParentLinkRequestRead]:
    return success_response(await submit_link_request(scope, user, payload), request_id=get_request_id())


@router.get("/me/linking/requests", response_model=ApiResponse[list[ParentLinkRequestRead]])
async def parent_list_link_requests_route(
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentLinkRequestRead]]:
    return success_response(await list_link_requests(scope, user), request_id=get_request_id())