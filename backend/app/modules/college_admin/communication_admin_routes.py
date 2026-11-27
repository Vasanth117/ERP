"""College admin communication administration routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.communication_admin_schemas import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementSchedule,
    AudienceGroupUpsert,
    ProviderSettingsUpsert,
    RetryDelivery,
    TemplateUpsert,
)
from app.modules.college_admin.communication_announcements_management_page_service import (
    get_communication_announcements_management_page,
)
from app.modules.college_admin.communication_create_announcement_page_service import (
    get_communication_create_announcement_page,
    save_communication_create_announcement_page,
)
from app.modules.college_admin.communication_channels_page_service import (
    get_communication_email_channel_page,
    get_communication_sms_channel_page,
    get_communication_whatsapp_channel_page,
)
from app.modules.college_admin.communication_audience_notifications_page_service import (
    get_communication_faculty_notifications_page,
    get_communication_parent_communication_page,
    get_communication_student_notifications_page,
)
from app.modules.college_admin.communication_dashboard_page_service import get_communication_dashboard_page
from app.modules.college_admin.communication_templates_scheduling_page_service import (
    get_communication_scheduled_messages_management_page,
    get_communication_templates_management_page,
)
from app.modules.college_admin.communication_section_sub_nav_service import get_communication_section_sub_nav
from app.modules.college_admin.communication_delivery_history_page_service import (
    export_communication_history_csv,
    get_communication_delivery_status_page,
    get_communication_history_page,
)
from app.modules.college_admin.communication_admin_service import (
    communication_report,
    create_announcement,
    list_failed_deliveries,
    publish_announcement,
    retry_all_failed_deliveries,
    retry_delivery,
    schedule_announcement,
    upsert_audience_group,
    upsert_provider_settings,
    upsert_template,
)
from app.modules.college_admin.deps import college_admin_user
from app.modules.college_admin.schemas import (
    CommunicationAnnouncementsManagementPageRead,
    CommunicationCreateAnnouncementPageRead,
    CommunicationCreateAnnouncementSave,
    CommunicationDashboardPageRead,
    CommunicationDeliveryStatusPageRead,
    CommunicationEmailChannelPageRead,
    CommunicationHistoryPageRead,
    CommunicationFacultyNotificationsPageRead,
    CommunicationParentCommunicationPageRead,
    CommunicationScheduledMessagesPageRead,
    CommunicationSmsChannelPageRead,
    CommunicationStudentNotificationsPageRead,
    CommunicationTemplatesManagementPageRead,
    CommunicationWhatsappChannelPageRead,
    CommunicationSectionSubNavRead,
)

router = APIRouter()


@router.get("/navigation/section-sub-nav", response_model=ApiResponse[CommunicationSectionSubNavRead])
async def communication_section_sub_nav_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    path: Annotated[str, Query()],
):
    return success_response(await get_communication_section_sub_nav(scope, path=path), request_id=get_request_id())


@router.get("/dashboard/page", response_model=ApiResponse[CommunicationDashboardPageRead])
async def communication_dashboard_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_communication_dashboard_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/announcements/management/page", response_model=ApiResponse[CommunicationAnnouncementsManagementPageRead])
async def communication_announcements_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
    search: Annotated[str | None, Query()] = None,
    audience: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
):
    return success_response(
        await get_communication_announcements_management_page(
            scope,
            page=page,
            page_size=page_size,
            search=search,
            audience=audience,
            status=status_filter,
        ),
        request_id=get_request_id(),
    )


@router.get("/announcements/create/page", response_model=ApiResponse[CommunicationCreateAnnouncementPageRead])
async def communication_create_announcement_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    announcement_id: Annotated[str | None, Query()] = None,
    audience: Annotated[str | None, Query()] = None,
    preset_channels: Annotated[str | None, Query()] = None,
    publish_timing: Annotated[str | None, Query()] = None,
) -> ApiResponse[CommunicationCreateAnnouncementPageRead]:
    return success_response(
        await get_communication_create_announcement_page(
            scope,
            announcement_id=announcement_id,
            audience=audience,
            preset_channels=preset_channels,
            preset_publish_timing=publish_timing,
        ),
        request_id=get_request_id(),
    )


@router.get("/deliveries/monitoring/page", response_model=ApiResponse[CommunicationDeliveryStatusPageRead])
async def communication_delivery_status_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_communication_delivery_status_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/history/management/page", response_model=ApiResponse[CommunicationHistoryPageRead])
async def communication_history_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
    search: Annotated[str | None, Query()] = None,
    month: Annotated[str | None, Query()] = None,
    channel: Annotated[str | None, Query()] = None,
    sender: Annotated[str | None, Query()] = None,
):
    return success_response(
        await get_communication_history_page(
            scope,
            page=page,
            page_size=page_size,
            search=search,
            month=month,
            channel=channel,
            sender=sender,
        ),
        request_id=get_request_id(),
    )


@router.get("/history/export")
async def communication_history_export_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    search: Annotated[str | None, Query()] = None,
    month: Annotated[str | None, Query()] = None,
    channel: Annotated[str | None, Query()] = None,
    sender: Annotated[str | None, Query()] = None,
):
    from fastapi.responses import PlainTextResponse

    csv_text = await export_communication_history_csv(
        scope,
        search=search,
        month=month,
        channel=channel,
        sender=sender,
    )
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="communication-history.csv"'},
    )


@router.post("/deliveries/retry-failed", response_model=ApiResponse[dict])
async def retry_failed_deliveries_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
):
    return success_response(await retry_all_failed_deliveries(scope), request_id=get_request_id())


@router.get("/templates/management/page", response_model=ApiResponse[CommunicationTemplatesManagementPageRead])
async def communication_templates_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 4,
):
    return success_response(
        await get_communication_templates_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/scheduled/management/page", response_model=ApiResponse[CommunicationScheduledMessagesPageRead])
async def communication_scheduled_messages_management_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_communication_scheduled_messages_management_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/channels/email/management/page", response_model=ApiResponse[CommunicationEmailChannelPageRead])
async def communication_email_channel_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_communication_email_channel_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/channels/sms/management/page", response_model=ApiResponse[CommunicationSmsChannelPageRead])
async def communication_sms_channel_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_communication_sms_channel_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/channels/whatsapp/management/page", response_model=ApiResponse[CommunicationWhatsappChannelPageRead])
async def communication_whatsapp_channel_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_communication_whatsapp_channel_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/audience/students/management/page", response_model=ApiResponse[CommunicationStudentNotificationsPageRead])
async def communication_student_notifications_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_communication_student_notifications_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/audience/faculty/management/page", response_model=ApiResponse[CommunicationFacultyNotificationsPageRead])
async def communication_faculty_notifications_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_communication_faculty_notifications_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.get("/audience/parents/management/page", response_model=ApiResponse[CommunicationParentCommunicationPageRead])
async def communication_parent_communication_page_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 3,
):
    return success_response(
        await get_communication_parent_communication_page(scope, page=page, page_size=page_size),
        request_id=get_request_id(),
    )


@router.put("/announcements/create/page", response_model=ApiResponse[CommunicationCreateAnnouncementPageRead])
async def communication_create_announcement_save_route(
    payload: CommunicationCreateAnnouncementSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[CommunicationCreateAnnouncementPageRead]:
    return success_response(await save_communication_create_announcement_page(scope, payload), request_id=get_request_id())


@router.post("/announcements", response_model=ApiResponse[AnnouncementRead], status_code=status.HTTP_201_CREATED)
async def announcement_create_route(payload: AnnouncementCreate, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await create_announcement(scope, payload), request_id=get_request_id())


@router.post("/announcements/{announcement_id}/publish", response_model=ApiResponse[AnnouncementRead])
async def announcement_publish_route(announcement_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await publish_announcement(scope, announcement_id), request_id=get_request_id())


@router.post("/announcements/schedule", response_model=ApiResponse[dict])
async def schedule_route(payload: AnnouncementSchedule, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await schedule_announcement(scope, payload), request_id=get_request_id())


@router.put("/templates", response_model=ApiResponse[dict])
async def template_route(payload: TemplateUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await upsert_template(scope, payload), request_id=get_request_id())


@router.put("/audience-groups", response_model=ApiResponse[dict])
async def audience_route(payload: AudienceGroupUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await upsert_audience_group(scope, payload), request_id=get_request_id())


@router.put("/providers", response_model=ApiResponse[dict])
async def provider_route(payload: ProviderSettingsUpsert, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await upsert_provider_settings(scope, payload), request_id=get_request_id())


@router.get("/deliveries/failed", response_model=ApiResponse[Page[dict]])
async def failed_deliveries_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)], pagination: Annotated[Pagination, Depends(pagination_params)]):
    return success_response(await list_failed_deliveries(scope, pagination), request_id=get_request_id())


@router.post("/deliveries/retry", response_model=ApiResponse[dict])
async def retry_route(payload: RetryDelivery, scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await retry_delivery(scope, payload), request_id=get_request_id())


@router.get("/reports/summary", response_model=ApiResponse[dict])
async def comm_report_route(scope: Annotated[AccessScope, Depends(get_access_scope)], _: Annotated[User, Depends(college_admin_user)]):
    return success_response(await communication_report(scope), request_id=get_request_id())