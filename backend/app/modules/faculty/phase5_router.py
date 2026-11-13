"""Faculty Phase 5 — communication and self-service routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.faculty.communication_schemas import (
    AnnouncementCreate,
    AnnouncementRead,
    AnnouncementUpdate,
    MessageRead,
    NotificationItemRead,
    NotificationPreferencesRead,
    NotificationPreferencesUpdate,
    NotificationReadUpdate,
    RecipientRead,
)
from app.modules.faculty.communication_schemas import AssignmentUpdateShare
from app.modules.faculty.communication_service import (
    communication_history,
    create_announcement,
    get_notification_preferences,
    list_academic_notifications,
    list_announcements,
    list_recipients,
    mark_notification_read,
    publish_announcement,
    send_academic_reminder,
    share_assignment_update,
    update_announcement,
    update_notification_preferences,
    withdraw_announcement,
)
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.faculty.deps import announcement_rate_limit, faculty_user
from app.modules.faculty.self_service_schemas import (
    EmploymentInfoRead,
    LeaveRequestCreate,
    LeaveRequestRead,
    PayslipListRead,
    PersonalActivityHistoryItem,
    PersonalDocumentRead,
    ReportExportRead,
    WorkloadReportRead,
)
from app.modules.faculty.self_service_service import (
    attendance_submission_history,
    download_payslip,
    download_personal_document,
    download_report_export,
    generate_personal_activity_report,
    get_employment_info,
    get_leave_status,
    get_report_export,
    list_leave_requests,
    list_payslips,
    list_personal_documents,
    marks_submission_history,
    personal_activity_history,
    personal_workload_report,
    submit_leave,
)
phase5_router = APIRouter()


@phase5_router.post(
    "/me/communication/announcements",
    response_model=ApiResponse[AnnouncementRead],
    status_code=status.HTTP_201_CREATED,
)
async def create_announcement_route(
    payload: AnnouncementCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    _: Annotated[None, Depends(announcement_rate_limit)],
) -> ApiResponse[AnnouncementRead]:
    return success_response(await create_announcement(scope, user, payload), request_id=get_request_id())


@phase5_router.get("/me/communication/announcements", response_model=ApiResponse[list[AnnouncementRead]])
async def list_announcements_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[AnnouncementRead]]:
    return success_response(await list_announcements(scope, user), request_id=get_request_id())


@phase5_router.patch("/me/communication/announcements/{announcement_id}", response_model=ApiResponse[AnnouncementRead])
async def update_announcement_route(
    announcement_id: str,
    payload: AnnouncementUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[AnnouncementRead]:
    return success_response(
        await update_announcement(scope, user, to_object_id(announcement_id, "announcement id"), payload),
        request_id=get_request_id(),
    )


@phase5_router.post("/me/communication/announcements/{announcement_id}/publish", response_model=ApiResponse[AnnouncementRead])
async def publish_announcement_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[AnnouncementRead]:
    return success_response(
        await publish_announcement(scope, user, to_object_id(announcement_id, "announcement id")),
        request_id=get_request_id(),
    )


@phase5_router.post("/me/communication/announcements/{announcement_id}/withdraw", response_model=ApiResponse[AnnouncementRead])
async def withdraw_announcement_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[AnnouncementRead]:
    return success_response(
        await withdraw_announcement(scope, user, to_object_id(announcement_id, "announcement id")),
        request_id=get_request_id(),
    )


@phase5_router.get(
    "/me/communication/announcements/{announcement_id}/recipients",
    response_model=ApiResponse[list[RecipientRead]],
)
async def announcement_recipients_route(
    announcement_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[RecipientRead]]:
    return success_response(
        await list_recipients(scope, user, to_object_id(announcement_id, "announcement id")),
        request_id=get_request_id(),
    )


@phase5_router.post(
    "/me/communication/reminders",
    response_model=ApiResponse[MessageRead],
    status_code=status.HTTP_201_CREATED,
)
async def academic_reminder_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    course_code: Annotated[str, Query()],
    subject: Annotated[str, Query(max_length=200)],
    body: Annotated[str, Query(max_length=4000)],
    section: Annotated[str | None, Query()] = None,
) -> ApiResponse[MessageRead]:
    return success_response(
        await send_academic_reminder(scope, user, course_code=course_code, section=section, subject=subject, body=body),
        request_id=get_request_id(),
    )


@phase5_router.get("/me/communication/messages", response_model=ApiResponse[list[MessageRead]])
async def communication_messages_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[MessageRead]]:
    return success_response(await communication_history(scope, user), request_id=get_request_id())


@phase5_router.get("/me/communication/history", response_model=ApiResponse[list[MessageRead]])
async def communication_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[MessageRead]]:
    return success_response(await communication_history(scope, user), request_id=get_request_id())


@phase5_router.post(
    "/me/communication/assignment-updates",
    response_model=ApiResponse[MessageRead],
    status_code=status.HTTP_201_CREATED,
)
async def assignment_update_share_route(
    payload: AssignmentUpdateShare,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    _: Annotated[None, Depends(announcement_rate_limit)],
) -> ApiResponse[MessageRead]:
    return success_response(await share_assignment_update(scope, user, payload), request_id=get_request_id())


@phase5_router.get("/me/communication/notifications", response_model=ApiResponse[list[NotificationItemRead]])
async def notifications_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[NotificationItemRead]]:
    return success_response(await list_academic_notifications(scope, user), request_id=get_request_id())


@phase5_router.patch("/me/communication/notifications/{notification_id}", response_model=ApiResponse[NotificationItemRead])
async def notification_read_route(
    notification_id: str,
    payload: NotificationReadUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    source: Annotated[str, Query()] = "academic",
) -> ApiResponse[NotificationItemRead]:
    if payload.read:
        data = await mark_notification_read(scope, user, notification_id, source=source)
        return success_response(data, request_id=get_request_id())
    return success_response(
        await mark_notification_read(scope, user, notification_id, source=source),
        request_id=get_request_id(),
    )


@phase5_router.get("/me/communication/notification-preferences", response_model=ApiResponse[NotificationPreferencesRead])
async def notification_prefs_get_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[NotificationPreferencesRead]:
    return success_response(await get_notification_preferences(scope, user), request_id=get_request_id())


@phase5_router.patch("/me/communication/notification-preferences", response_model=ApiResponse[NotificationPreferencesRead])
async def notification_prefs_patch_route(
    payload: NotificationPreferencesUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[NotificationPreferencesRead]:
    return success_response(await update_notification_preferences(scope, user, payload), request_id=get_request_id())


@phase5_router.get("/me/self-service/employment", response_model=ApiResponse[EmploymentInfoRead])
async def employment_info_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[EmploymentInfoRead]:
    return success_response(await get_employment_info(scope, user), request_id=get_request_id())


@phase5_router.post(
    "/me/self-service/leave",
    response_model=ApiResponse[LeaveRequestRead],
    status_code=status.HTTP_201_CREATED,
)
async def leave_submit_route(
    payload: LeaveRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[LeaveRequestRead]:
    return success_response(await submit_leave(scope, user, payload), request_id=get_request_id())


@phase5_router.get("/me/self-service/leave", response_model=ApiResponse[list[LeaveRequestRead]])
async def leave_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    status: Annotated[LeaveRequestStatus | None, Query(description="Filter e.g. approved")] = None,
) -> ApiResponse[list[LeaveRequestRead]]:
    return success_response(await list_leave_requests(scope, user, status=status), request_id=get_request_id())


@phase5_router.get("/me/self-service/leave/{leave_id}", response_model=ApiResponse[LeaveRequestRead])
async def leave_status_route(
    leave_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[LeaveRequestRead]:
    return success_response(
        await get_leave_status(scope, user, to_object_id(leave_id, "leave id")),
        request_id=get_request_id(),
    )


@phase5_router.get("/me/self-service/payslips", response_model=ApiResponse[PayslipListRead])
async def payslips_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[PayslipListRead]:
    return success_response(await list_payslips(scope, user), request_id=get_request_id())


@phase5_router.get("/me/self-service/payslips/{payslip_id}/download")
async def payslip_download_route(
    payslip_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> Response:
    data, name = await download_payslip(scope, user, to_object_id(payslip_id, "payslip id"))
    return Response(content=data, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


@phase5_router.get("/me/self-service/documents", response_model=ApiResponse[list[PersonalDocumentRead]])
async def personal_documents_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[PersonalDocumentRead]]:
    return success_response(await list_personal_documents(scope, user), request_id=get_request_id())


@phase5_router.get("/me/self-service/documents/{document_id}/download")
async def personal_document_download_route(
    document_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> Response:
    data, name, mime = await download_personal_document(scope, user, to_object_id(document_id, "document id"))
    return Response(content=data, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{name}"'})


@phase5_router.get("/me/self-service/activity", response_model=ApiResponse[Page[PersonalActivityHistoryItem]])
async def personal_activity_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[PersonalActivityHistoryItem]]:
    return success_response(await personal_activity_history(scope, user, pagination), request_id=get_request_id())


@phase5_router.get("/me/self-service/history/attendance")
async def attendance_history_self_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list]:
    return success_response(await attendance_submission_history(scope, user), request_id=get_request_id())


@phase5_router.get("/me/self-service/history/marks")
async def marks_history_self_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[dict]:
    return success_response(await marks_submission_history(scope, user), request_id=get_request_id())


@phase5_router.get("/me/self-service/reports/workload", response_model=ApiResponse[WorkloadReportRead])
async def workload_self_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[WorkloadReportRead]:
    return success_response(await personal_workload_report(scope, user), request_id=get_request_id())


@phase5_router.post(
    "/me/self-service/reports/personal-activity",
    response_model=ApiResponse[ReportExportRead],
    status_code=status.HTTP_201_CREATED,
)
async def personal_report_generate_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[ReportExportRead]:
    return success_response(await generate_personal_activity_report(scope, user), request_id=get_request_id())


@phase5_router.get("/me/self-service/reports/{export_id}", response_model=ApiResponse[ReportExportRead])
async def report_export_status_route(
    export_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[ReportExportRead]:
    return success_response(
        await get_report_export(scope, user, to_object_id(export_id, "export id")),
        request_id=get_request_id(),
    )


@phase5_router.get("/me/self-service/reports/{export_id}/download")
async def report_export_download_route(
    export_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    token: Annotated[str, Query()],
    sig: Annotated[str, Query()],
) -> Response:
    data = await download_report_export(
        scope,
        user,
        to_object_id(export_id, "export id"),
        token,
        sig,
    )
    return Response(content=data, media_type="application/json")
