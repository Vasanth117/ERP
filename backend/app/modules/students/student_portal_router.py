"""Student portal phase 10 — library, residence, services, communication, reports."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.students.academic_document_service import download_academic_document
from app.modules.students.deps import student_portal_request_rate_limit, student_user
from app.modules.students.student_communication_service import (
    announcements,
    authorized_documents,
    correction_history,
    document_request_history,
    get_preferences,
    mark_notification_read,
    notifications_feed,
    submit_document_request,
    submit_profile_correction,
    update_preferences,
)
from app.modules.students.student_library_service import (
    book_availability,
    borrowing_history,
    digital_resources,
    due_dates,
    fines,
    issued_books,
    overdue_books,
    reservations,
    search_catalogue,
)
from app.modules.students.student_portal_schemas import (
    AnnouncementFeedRead,
    CommunicationPreferencesRead,
    CommunicationPreferencesUpdate,
    DocumentRequestInput,
    HostelRequestInput,
    NotificationFeedRead,
    ProfileCorrectionInput,
    ReportExportRead,
    ReportGenerateInput,
    ServiceRequestInput,
    ServiceRequestRead,
    TransportRequestInput,
)
from app.modules.students.student_reports_service import download_report, generate_report, report_history, report_status
from app.modules.students.academic_service import submit_enrollment_request
from app.modules.students.schemas import EnrollmentRequestCreate
from app.modules.students.student_residence_service import (
    hostel_application_status,
    hostel_fee_details,
    hostel_notices,
    hostel_request_status,
    hostel_room_allocation,
    submit_hostel_request,
    submit_transport_request,
    transport_allocation,
    transport_fee_details,
    transport_notifications_feed,
    transport_route_stops,
    transport_routes,
    transport_schedules,
)
from app.modules.students.student_services_hub_service import (
    academic_service_requests,
    list_services,
    service_history,
    service_request_status,
    submit_service_request,
)

student_portal_router = APIRouter()


# Library
@student_portal_router.get("/me/library/catalogue", response_model=ApiResponse[list])
async def library_catalogue_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    q: Annotated[str | None, Query()] = None,
) -> ApiResponse[list]:
    return success_response(await search_catalogue(scope, user, q=q), request_id=get_request_id())


@student_portal_router.get("/me/library/books/{book_id}/availability", response_model=ApiResponse[dict])
async def library_availability_route(book_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[dict]:
    return success_response(await book_availability(scope, user, book_id), request_id=get_request_id())


@student_portal_router.get("/me/library/issued", response_model=ApiResponse[list])
async def library_issued_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    return success_response(await issued_books(scope, user), request_id=get_request_id())


@student_portal_router.get("/me/library/due-dates", response_model=ApiResponse[list])
async def library_due_dates_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    return success_response(await due_dates(scope, user), request_id=get_request_id())


@student_portal_router.get("/me/library/overdue", response_model=ApiResponse[list])
async def library_overdue_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    return success_response(await overdue_books(scope, user), request_id=get_request_id())


@student_portal_router.get("/me/library/reservations", response_model=ApiResponse[list])
async def library_reservations_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    return success_response(await reservations(scope, user), request_id=get_request_id())


@student_portal_router.get("/me/library/fines", response_model=ApiResponse[list])
async def library_fines_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    return success_response(await fines(scope, user), request_id=get_request_id())


@student_portal_router.get("/me/library/digital", response_model=ApiResponse[list])
async def library_digital_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    return success_response(await digital_resources(scope, user), request_id=get_request_id())


@student_portal_router.get("/me/library/history", response_model=ApiResponse[list])
async def library_history_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    return success_response(await borrowing_history(scope, user), request_id=get_request_id())


# Hostel
@student_portal_router.get("/me/hostel/application", response_model=ApiResponse[dict | None])
async def hostel_application_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[dict | None]:
    data = await hostel_application_status(scope, user)
    return success_response(data.model_dump() if data else None, request_id=get_request_id())


@student_portal_router.get("/me/hostel/allocation", response_model=ApiResponse[dict | None])
async def hostel_allocation_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[dict | None]:
    data = await hostel_room_allocation(scope, user)
    return success_response(data.model_dump() if data else None, request_id=get_request_id())


@student_portal_router.get("/me/hostel/fees", response_model=ApiResponse[dict])
async def hostel_fees_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[dict]:
    return success_response(await hostel_fee_details(scope, user), request_id=get_request_id())


@student_portal_router.get("/me/hostel/notices", response_model=ApiResponse[list])
async def hostel_notices_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    return success_response(await hostel_notices(scope, user), request_id=get_request_id())


@student_portal_router.post("/me/hostel/requests", response_model=ApiResponse[dict])
async def hostel_request_submit_route(
    payload: HostelRequestInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(student_portal_request_rate_limit)],
) -> ApiResponse[dict]:
    return success_response(await submit_hostel_request(scope, user, payload), request_id=get_request_id())


@student_portal_router.get("/me/hostel/requests/{request_id}", response_model=ApiResponse[dict])
async def hostel_request_status_route(request_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[dict]:
    return success_response(await hostel_request_status(scope, user, request_id), request_id=get_request_id())


# Transport
@student_portal_router.get("/me/transport/routes", response_model=ApiResponse[list])
async def transport_routes_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    data = await transport_routes(scope, user)
    return success_response([r.model_dump() for r in data], request_id=get_request_id())


@student_portal_router.get("/me/transport/allocation", response_model=ApiResponse[dict | None])
async def transport_allocation_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[dict | None]:
    data = await transport_allocation(scope, user)
    return success_response(data.model_dump() if data else None, request_id=get_request_id())


@student_portal_router.get("/me/transport/routes/{route_id}/stops", response_model=ApiResponse[list])
async def transport_stops_route(route_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    data = await transport_route_stops(scope, user, route_id)
    return success_response([s.model_dump() for s in data], request_id=get_request_id())


@student_portal_router.get("/me/transport/schedules", response_model=ApiResponse[list])
async def transport_schedules_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    route_id: Annotated[str | None, Query()] = None,
) -> ApiResponse[list]:
    return success_response(await transport_schedules(scope, user, route_id), request_id=get_request_id())


@student_portal_router.get("/me/transport/fees", response_model=ApiResponse[dict])
async def transport_fees_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[dict]:
    return success_response(await transport_fee_details(scope, user), request_id=get_request_id())


@student_portal_router.post("/me/transport/requests", response_model=ApiResponse[dict])
async def transport_request_route(
    payload: TransportRequestInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(student_portal_request_rate_limit)],
) -> ApiResponse[dict]:
    return success_response(await submit_transport_request(scope, user, payload), request_id=get_request_id())


@student_portal_router.get("/me/transport/notifications", response_model=ApiResponse[list])
async def transport_notifications_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    return success_response(await transport_notifications_feed(scope, user), request_id=get_request_id())


# Services
@student_portal_router.get("/me/services", response_model=ApiResponse[list])
async def services_list_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    data = await list_services(scope, user)
    return success_response([s.model_dump() for s in data], request_id=get_request_id())


@student_portal_router.post("/me/services/requests", response_model=ApiResponse[ServiceRequestRead])
async def services_submit_route(
    payload: ServiceRequestInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(student_portal_request_rate_limit)],
) -> ApiResponse[ServiceRequestRead]:
    return success_response(await submit_service_request(scope, user, payload), request_id=get_request_id())


@student_portal_router.get("/me/services/requests/{request_id}", response_model=ApiResponse[ServiceRequestRead])
async def services_status_route(request_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[ServiceRequestRead]:
    return success_response(await service_request_status(scope, user, request_id), request_id=get_request_id())


@student_portal_router.get("/me/services/history", response_model=ApiResponse[Page[ServiceRequestRead]])
async def services_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ServiceRequestRead]]:
    return success_response(await service_history(scope, user, pagination), request_id=get_request_id())


@student_portal_router.get("/me/services/academic-requests", response_model=ApiResponse[Page[dict]])
async def academic_requests_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await academic_service_requests(scope, user, pagination), request_id=get_request_id())


@student_portal_router.post("/me/services/academic-requests", response_model=ApiResponse)
async def academic_requests_submit_route(
    payload: EnrollmentRequestCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(student_portal_request_rate_limit)],
) -> ApiResponse:
    return success_response(await submit_enrollment_request(scope, user, payload), request_id=get_request_id())


# Communication
@student_portal_router.get("/me/announcements", response_model=ApiResponse[Page[AnnouncementFeedRead]])
async def announcements_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    scope_filter: Annotated[str | None, Query(alias="scope")] = None,
) -> ApiResponse[Page[AnnouncementFeedRead]]:
    return success_response(await announcements(scope, user, scope_filter=scope_filter, pagination=pagination), request_id=get_request_id())


@student_portal_router.get("/me/notifications", response_model=ApiResponse[Page[NotificationFeedRead]])
async def notifications_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[NotificationFeedRead]]:
    return success_response(await notifications_feed(scope, user, pagination), request_id=get_request_id())


@student_portal_router.post("/me/notifications/{notification_key}/read", response_model=ApiResponse[dict])
async def notification_read_route(notification_key: str, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[dict]:
    return success_response(await mark_notification_read(scope, user, notification_key), request_id=get_request_id())


@student_portal_router.get("/me/communication/preferences", response_model=ApiResponse[CommunicationPreferencesRead])
async def comm_prefs_get_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[CommunicationPreferencesRead]:
    return success_response(await get_preferences(scope, user), request_id=get_request_id())


@student_portal_router.patch("/me/communication/preferences", response_model=ApiResponse[CommunicationPreferencesRead])
async def comm_prefs_patch_route(
    payload: CommunicationPreferencesUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
) -> ApiResponse[CommunicationPreferencesRead]:
    return success_response(await update_preferences(scope, user, payload), request_id=get_request_id())


@student_portal_router.get("/me/documents/authorized", response_model=ApiResponse[list])
async def authorized_docs_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    data = await authorized_documents(scope, user)
    return success_response([d.model_dump() for d in data], request_id=get_request_id())


@student_portal_router.post("/me/documents/requests", response_model=ApiResponse[dict])
async def document_request_route(
    payload: DocumentRequestInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(student_portal_request_rate_limit)],
) -> ApiResponse[dict]:
    return success_response(await submit_document_request(scope, user, payload), request_id=get_request_id())


@student_portal_router.get("/me/documents/requests", response_model=ApiResponse[Page[dict]])
async def document_requests_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await document_request_history(scope, user, pagination), request_id=get_request_id())


@student_portal_router.get("/me/documents/{document_id}/download-token", response_model=ApiResponse)
async def document_download_token_route(document_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse:
    return success_response(await download_academic_document(scope, user, document_id), request_id=get_request_id())


@student_portal_router.post("/me/profile-corrections", response_model=ApiResponse[dict])
async def profile_correction_route(
    payload: ProfileCorrectionInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(student_portal_request_rate_limit)],
) -> ApiResponse[dict]:
    return success_response(await submit_profile_correction(scope, user, payload), request_id=get_request_id())


@student_portal_router.get("/me/profile-corrections", response_model=ApiResponse[list])
async def profile_corrections_history_route(scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[list]:
    return success_response(await correction_history(scope, user), request_id=get_request_id())


# Reports (list route before path parameter routes)
@student_portal_router.get("/me/reports", response_model=ApiResponse[Page[ReportExportRead]])
async def report_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ReportExportRead]]:
    return success_response(await report_history(scope, user, pagination), request_id=get_request_id())


@student_portal_router.post("/me/reports/generate", response_model=ApiResponse[ReportExportRead])
async def report_generate_route(
    payload: ReportGenerateInput,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    _: Annotated[None, Depends(student_portal_request_rate_limit)],
) -> ApiResponse[ReportExportRead]:
    return success_response(await generate_report(scope, user, payload), request_id=get_request_id())


@student_portal_router.get("/me/reports/{export_id}", response_model=ApiResponse[ReportExportRead])
async def report_status_route(export_id: str, scope: Annotated[AccessScope, Depends(get_access_scope)], user: Annotated[User, Depends(student_user)]) -> ApiResponse[ReportExportRead]:
    return success_response(await report_status(scope, user, export_id), request_id=get_request_id())


@student_portal_router.get("/me/reports/{export_id}/download", response_model=ApiResponse[dict])
async def report_download_route(
    export_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(student_user)],
    token: Annotated[str, Query(min_length=8)],
) -> ApiResponse[dict]:
    return success_response(await download_report(scope, user, export_id, token), request_id=get_request_id())
