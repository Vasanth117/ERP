"""Parent routes scoped to a verified linked student."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.parents.academic_overview_service import (
    get_academic_overview,
    get_student_profile_view,
    list_academic_enquiries,
    list_academic_history,
    submit_academic_enquiry,
)
from app.modules.parents.attendance_monitoring_service import (
    acknowledge_alert,
    get_attendance_dashboard,
    get_attendance_history,
    get_attendance_shortages,
    get_daily_attendance,
    get_subject_attendance,
    list_attendance_alerts,
    list_attendance_enquiries,
    submit_attendance_enquiry,
)
from app.modules.parents.deps import parent_enquiry_rate_limit, parent_user
from app.modules.parents.phase2_schemas import (
    ParentAcademicEnquiryCreate,
    ParentAcademicEnquiryRead,
    ParentAcademicHistoryTermRead,
    ParentAcademicOverviewRead,
    ParentAttendanceAlertRead,
    ParentAttendanceDashboardRead,
    ParentAttendanceEnquiryCreate,
    ParentAttendanceEnquiryRead,
    ParentStudentProfileRead,
)
from app.modules.students.student_schedule_schemas import AttendanceMarkRead, AttendanceShortageRead, SubjectAttendanceDetailRead

router = APIRouter()


@router.get("/{student_user_id}/profile", response_model=ApiResponse[ParentStudentProfileRead])
async def parent_student_profile_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ApiResponse[ParentStudentProfileRead]:
    return success_response(
        await get_student_profile_view(
            scope, user, student_user_id, academic_year_label=academic_year_label, semester_label=semester_label
        ),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/academics/overview", response_model=ApiResponse[ParentAcademicOverviewRead])
async def parent_academic_overview_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ApiResponse[ParentAcademicOverviewRead]:
    return success_response(
        await get_academic_overview(
            scope, user, student_user_id, academic_year_label=academic_year_label, semester_label=semester_label
        ),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/academics/history", response_model=ApiResponse[Page[ParentAcademicHistoryTermRead]])
async def parent_academic_history_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[ParentAcademicHistoryTermRead]]:
    return success_response(
        await list_academic_history(scope, user, student_user_id, pagination),
        request_id=get_request_id(),
    )


@router.post("/{student_user_id}/academics/enquiries", response_model=ApiResponse[ParentAcademicEnquiryRead])
async def parent_academic_enquiry_post_route(
    student_user_id: str,
    payload: ParentAcademicEnquiryCreate,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[None, Depends(parent_enquiry_rate_limit)],
) -> ApiResponse[ParentAcademicEnquiryRead]:
    return success_response(
        await submit_academic_enquiry(scope, user, student_user_id, payload),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/academics/enquiries", response_model=ApiResponse[list[ParentAcademicEnquiryRead]])
async def parent_academic_enquiries_list_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentAcademicEnquiryRead]]:
    return success_response(await list_academic_enquiries(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/attendance/dashboard", response_model=ApiResponse[ParentAttendanceDashboardRead])
async def parent_attendance_dashboard_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ApiResponse[ParentAttendanceDashboardRead]:
    return success_response(
        await get_attendance_dashboard(
            scope, user, student_user_id, academic_year_label=academic_year_label, semester_label=semester_label
        ),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/attendance/subjects", response_model=ApiResponse[list[SubjectAttendanceDetailRead]])
async def parent_attendance_subjects_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ApiResponse[list[SubjectAttendanceDetailRead]]:
    return success_response(
        await get_subject_attendance(
            scope, user, student_user_id, academic_year_label=academic_year_label, semester_label=semester_label
        ),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/attendance/daily", response_model=ApiResponse[list[AttendanceMarkRead]])
async def parent_attendance_daily_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    session_date: date,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ApiResponse[list[AttendanceMarkRead]]:
    return success_response(
        await get_daily_attendance(
            scope, user, student_user_id, session_date, academic_year_label=academic_year_label, semester_label=semester_label
        ),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/attendance/history", response_model=ApiResponse[Page[AttendanceMarkRead]])
async def parent_attendance_history_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ApiResponse[Page[AttendanceMarkRead]]:
    return success_response(
        await get_attendance_history(
            scope,
            user,
            student_user_id,
            pagination,
            academic_year_label=academic_year_label,
            semester_label=semester_label,
        ),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/attendance/shortages", response_model=ApiResponse[list[AttendanceShortageRead]])
async def parent_attendance_shortages_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ApiResponse[list[AttendanceShortageRead]]:
    return success_response(
        await get_attendance_shortages(
            scope, user, student_user_id, academic_year_label=academic_year_label, semester_label=semester_label
        ),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/attendance/alerts", response_model=ApiResponse[list[ParentAttendanceAlertRead]])
async def parent_attendance_alerts_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    unacknowledged_only: bool = False,
) -> ApiResponse[list[ParentAttendanceAlertRead]]:
    return success_response(
        await list_attendance_alerts(scope, user, student_user_id, unacknowledged_only=unacknowledged_only),
        request_id=get_request_id(),
    )


@router.post("/{student_user_id}/attendance/alerts/{alert_id}/acknowledge", response_model=ApiResponse[dict])
async def parent_attendance_alert_ack_route(
    student_user_id: str,
    alert_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[dict]:
    return success_response(
        await acknowledge_alert(scope, user, student_user_id, alert_id),
        request_id=get_request_id(),
    )


@router.post("/{student_user_id}/attendance/enquiries", response_model=ApiResponse[ParentAttendanceEnquiryRead])
async def parent_attendance_enquiry_post_route(
    student_user_id: str,
    payload: ParentAttendanceEnquiryCreate,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[None, Depends(parent_enquiry_rate_limit)],
) -> ApiResponse[ParentAttendanceEnquiryRead]:
    return success_response(
        await submit_attendance_enquiry(scope, user, student_user_id, payload),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/attendance/enquiries", response_model=ApiResponse[list[ParentAttendanceEnquiryRead]])
async def parent_attendance_enquiries_list_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentAttendanceEnquiryRead]]:
    return success_response(await list_attendance_enquiries(scope, user, student_user_id), request_id=get_request_id())


from app.modules.parents.examination_portal_service import (
    download_hall_ticket_parent,
    get_academic_calendar,
    get_examination_overview,
    get_examination_timetable,
    get_published_results_summary,
    get_subject_wise_published_results,
    hall_ticket_availability_parent,
    list_exam_notifications,
    list_result_statuses,
    list_revaluation_status,
)
from app.modules.parents.finance_portal_service import (
    get_fee_statement,
    get_finance_dashboard,
    get_payment_status_parent,
    initiate_parent_payment,
    list_finance_enquiries,
    list_installments,
    list_receipts_parent,
    list_scholarships,
    payment_history_parent,
    submit_finance_enquiry,
)
from app.modules.parents.deps import parent_payment_rate_limit
from app.modules.parents.phase3_schemas import (
    ParentExamCalendarEventRead,
    ParentExaminationOverviewRead,
    ParentExamNotificationRead,
    ParentExamResultStatusRead,
    ParentExamReviewStatusRead,
    ParentExamTimetableRead,
    ParentFinanceDashboardRead,
    ParentFinanceEnquiryCreate,
    ParentFinanceEnquiryRead,
    ParentFinanceStatementRead,
    ParentPaymentInitiateInput,
)
from app.modules.students.examination_registration_schemas import HallTicketAvailabilityRead, HallTicketDownloadRead
from app.modules.students.examination_results_schemas import SemesterResultSummaryRead, SubjectWiseMarksRead
from app.modules.students.student_finance_schemas import (
    InstallmentScheduleRead,
    PaymentInitiateRead,
    PaymentStatusRead,
    PaymentHistoryRead,
    ReceiptRead,
    ScholarshipEligibilityRead,
)


@router.get("/{student_user_id}/examinations/overview", response_model=ApiResponse[ParentExaminationOverviewRead])
async def parent_exam_overview_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentExaminationOverviewRead]:
    return success_response(await get_examination_overview(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/examinations/timetable", response_model=ApiResponse[ParentExamTimetableRead])
async def parent_exam_timetable_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    academic_year_label: str | None = None,
    semester_label: str | None = None,
) -> ApiResponse[ParentExamTimetableRead]:
    return success_response(
        await get_examination_timetable(
            scope, user, student_user_id, academic_year_label=academic_year_label, semester_label=semester_label
        ),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/examinations/notifications", response_model=ApiResponse[list[ParentExamNotificationRead]])
async def parent_exam_notifications_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentExamNotificationRead]]:
    return success_response(await list_exam_notifications(scope, user, student_user_id), request_id=get_request_id())


@router.get(
    "/{student_user_id}/examinations/results/{season_id}",
    response_model=ApiResponse[SemesterResultSummaryRead],
)
async def parent_exam_results_route(
    student_user_id: str,
    season_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[SemesterResultSummaryRead]:
    return success_response(
        await get_published_results_summary(scope, user, student_user_id, season_id),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/examinations/results", response_model=ApiResponse[list[SubjectWiseMarksRead]])
async def parent_exam_subject_marks_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    season_id: str | None = None,
) -> ApiResponse[list[SubjectWiseMarksRead]]:
    return success_response(
        await get_subject_wise_published_results(scope, user, student_user_id, season_id=season_id),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/examinations/result-status", response_model=ApiResponse[list[ParentExamResultStatusRead]])
async def parent_exam_result_status_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentExamResultStatusRead]]:
    return success_response(await list_result_statuses(scope, user, student_user_id), request_id=get_request_id())


@router.get(
    "/{student_user_id}/examinations/hall-ticket/{season_id}/availability",
    response_model=ApiResponse[HallTicketAvailabilityRead],
)
async def parent_hall_ticket_availability_route(
    student_user_id: str,
    season_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[HallTicketAvailabilityRead]:
    return success_response(
        await hall_ticket_availability_parent(scope, user, student_user_id, season_id),
        request_id=get_request_id(),
    )


@router.post(
    "/{student_user_id}/examinations/hall-ticket/{season_id}/download",
    response_model=ApiResponse[HallTicketDownloadRead],
)
async def parent_hall_ticket_download_route(
    student_user_id: str,
    season_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[HallTicketDownloadRead]:
    return success_response(
        await download_hall_ticket_parent(scope, user, student_user_id, season_id),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/examinations/reviews", response_model=ApiResponse[list[ParentExamReviewStatusRead]])
async def parent_exam_reviews_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentExamReviewStatusRead]]:
    return success_response(await list_revaluation_status(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/examinations/calendar", response_model=ApiResponse[list[ParentExamCalendarEventRead]])
async def parent_exam_calendar_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentExamCalendarEventRead]]:
    return success_response(await get_academic_calendar(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/finance/dashboard", response_model=ApiResponse[ParentFinanceDashboardRead])
async def parent_finance_dashboard_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentFinanceDashboardRead]:
    return success_response(await get_finance_dashboard(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/finance/statement", response_model=ApiResponse[ParentFinanceStatementRead])
async def parent_finance_statement_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentFinanceStatementRead]:
    return success_response(await get_fee_statement(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/finance/installments", response_model=ApiResponse[list[InstallmentScheduleRead]])
async def parent_finance_installments_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[InstallmentScheduleRead]]:
    return success_response(await list_installments(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/finance/scholarships", response_model=ApiResponse[list[ScholarshipEligibilityRead]])
async def parent_finance_scholarships_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ScholarshipEligibilityRead]]:
    return success_response(await list_scholarships(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/finance/receipts", response_model=ApiResponse[list[ReceiptRead]])
async def parent_finance_receipts_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ReceiptRead]]:
    return success_response(await list_receipts_parent(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/finance/payments", response_model=ApiResponse[list[PaymentHistoryRead]])
async def parent_finance_payments_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[PaymentHistoryRead]]:
    return success_response(await payment_history_parent(scope, user, student_user_id), request_id=get_request_id())


@router.post("/{student_user_id}/finance/payments/initiate", response_model=ApiResponse[PaymentInitiateRead])
async def parent_finance_payment_initiate_route(
    student_user_id: str,
    payload: ParentPaymentInitiateInput,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[None, Depends(parent_payment_rate_limit)],
) -> ApiResponse[PaymentInitiateRead]:
    return success_response(
        await initiate_parent_payment(scope, user, student_user_id, payload),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/finance/payments/{transaction_id}", response_model=ApiResponse[PaymentStatusRead])
async def parent_finance_payment_status_route(
    student_user_id: str,
    transaction_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[PaymentStatusRead]:
    return success_response(
        await get_payment_status_parent(scope, user, student_user_id, transaction_id),
        request_id=get_request_id(),
    )


@router.post("/{student_user_id}/finance/enquiries", response_model=ApiResponse[ParentFinanceEnquiryRead])
async def parent_finance_enquiry_post_route(
    student_user_id: str,
    payload: ParentFinanceEnquiryCreate,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[None, Depends(parent_enquiry_rate_limit)],
) -> ApiResponse[ParentFinanceEnquiryRead]:
    return success_response(
        await submit_finance_enquiry(scope, user, student_user_id, payload),
        request_id=get_request_id(),
    )


from app.modules.parents.document_portal_service import (
    download_document,
    get_document_dashboard,
    get_document_detail,
    list_document_access_requests,
    list_documents,
    submit_document_access_request,
)
from app.modules.parents.phase4_schemas import (
    ParentDocumentAccessRequestCreate,
    ParentDocumentAccessRequestRead,
    ParentDocumentDashboardRead,
    ParentDocumentDownloadRead,
    ParentDocumentSummaryRead,
    ParentServiceRequestCommentCreate,
    ParentServiceRequestCommentRead,
    ParentServiceRequestCreate,
    ParentServiceRequestRead,
)
from app.modules.parents.service_request_service import (
    add_service_request_comment,
    create_service_request,
    get_service_request,
    list_service_request_comments,
    list_service_requests,
)


@router.get("/{student_user_id}/documents/dashboard", response_model=ApiResponse[ParentDocumentDashboardRead])
async def parent_document_dashboard_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentDocumentDashboardRead]:
    return success_response(await get_document_dashboard(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/documents", response_model=ApiResponse[list[ParentDocumentSummaryRead]])
async def parent_documents_list_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentDocumentSummaryRead]]:
    return success_response(await list_documents(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/documents/{document_id}", response_model=ApiResponse[ParentDocumentSummaryRead])
async def parent_document_detail_route(
    student_user_id: str,
    document_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentDocumentSummaryRead]:
    return success_response(await get_document_detail(scope, user, student_user_id, document_id), request_id=get_request_id())


@router.post("/{student_user_id}/documents/{document_id}/download", response_model=ApiResponse[ParentDocumentDownloadRead])
async def parent_document_download_route(
    student_user_id: str,
    document_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentDocumentDownloadRead]:
    return success_response(await download_document(scope, user, student_user_id, document_id), request_id=get_request_id())


@router.post("/{student_user_id}/documents/requests", response_model=ApiResponse[ParentDocumentAccessRequestRead])
async def parent_document_request_post_route(
    student_user_id: str,
    payload: ParentDocumentAccessRequestCreate,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[None, Depends(parent_enquiry_rate_limit)],
) -> ApiResponse[ParentDocumentAccessRequestRead]:
    return success_response(
        await submit_document_access_request(scope, user, student_user_id, payload),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/documents/requests", response_model=ApiResponse[list[ParentDocumentAccessRequestRead]])
async def parent_document_requests_list_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentDocumentAccessRequestRead]]:
    return success_response(await list_document_access_requests(scope, user, student_user_id), request_id=get_request_id())


@router.post("/{student_user_id}/service-requests", response_model=ApiResponse[ParentServiceRequestRead])
async def parent_service_request_create_route(
    student_user_id: str,
    payload: ParentServiceRequestCreate,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[None, Depends(parent_enquiry_rate_limit)],
) -> ApiResponse[ParentServiceRequestRead]:
    return success_response(
        await create_service_request(scope, user, student_user_id, payload),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/service-requests", response_model=ApiResponse[list[ParentServiceRequestRead]])
async def parent_service_requests_list_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentServiceRequestRead]]:
    return success_response(await list_service_requests(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/service-requests/{request_id}", response_model=ApiResponse[ParentServiceRequestRead])
async def parent_service_request_get_route(
    student_user_id: str,
    request_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentServiceRequestRead]:
    return success_response(await get_service_request(scope, user, student_user_id, request_id), request_id=get_request_id())


@router.post(
    "/{student_user_id}/service-requests/{request_id}/comments",
    response_model=ApiResponse[ParentServiceRequestCommentRead],
)
async def parent_service_request_comment_route(
    student_user_id: str,
    request_id: str,
    payload: ParentServiceRequestCommentCreate,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentServiceRequestCommentRead]:
    return success_response(
        await add_service_request_comment(scope, user, student_user_id, request_id, payload),
        request_id=get_request_id(),
    )


@router.get(
    "/{student_user_id}/service-requests/{request_id}/comments",
    response_model=ApiResponse[list[ParentServiceRequestCommentRead]],
)
async def parent_service_request_comments_list_route(
    student_user_id: str,
    request_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentServiceRequestCommentRead]]:
    return success_response(
        await list_service_request_comments(scope, user, student_user_id, request_id),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/finance/enquiries", response_model=ApiResponse[list[ParentFinanceEnquiryRead]])
async def parent_finance_enquiries_list_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentFinanceEnquiryRead]]:
    return success_response(await list_finance_enquiries(scope, user, student_user_id), request_id=get_request_id())


from app.modules.parents.meeting_portal_service import (
    cancel_meeting_request,
    create_meeting_request,
    get_meeting_dashboard,
    get_meeting_outcome,
    list_appointments,
    list_meeting_requests,
    request_reschedule,
)
from app.modules.parents.phase5_schemas import (
    ParentMeetingAppointmentRead,
    ParentMeetingCancelCreate,
    ParentMeetingDashboardRead,
    ParentMeetingOutcomeRead,
    ParentMeetingRequestCreate,
    ParentMeetingRequestRead,
    ParentMeetingRescheduleCreate,
    ParentHostelSummaryRead,
    ParentLibrarySummaryRead,
    ParentMessSummaryRead,
    ParentServiceEnquiryCreate,
    ParentServiceEnquiryRead,
    ParentStudentServicesOverviewRead,
    ParentTransportSummaryRead,
    ParentReportExportRead,
)
from app.modules.parents.student_services_portal_service import (
    hostel_summary,
    library_summary,
    list_service_enquiries,
    mess_summary,
    services_overview,
    submit_service_enquiry,
    transport_summary,
)
from app.modules.parents.reports_portal_service import build_report
from app.modules.parents.enums import ParentReportCategory


@router.get("/{student_user_id}/meetings/dashboard", response_model=ApiResponse[ParentMeetingDashboardRead])
async def parent_student_meeting_dashboard_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentMeetingDashboardRead]:
    return success_response(
        await get_meeting_dashboard(scope, user, student_user_id=student_user_id),
        request_id=get_request_id(),
    )


@router.post("/{student_user_id}/meetings/requests", response_model=ApiResponse[ParentMeetingRequestRead])
async def parent_meeting_request_create_route(
    student_user_id: str,
    payload: ParentMeetingRequestCreate,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[None, Depends(parent_enquiry_rate_limit)],
) -> ApiResponse[ParentMeetingRequestRead]:
    return success_response(
        await create_meeting_request(scope, user, student_user_id, payload),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/meetings/requests", response_model=ApiResponse[list[ParentMeetingRequestRead]])
async def parent_meeting_requests_list_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentMeetingRequestRead]]:
    return success_response(await list_meeting_requests(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/meetings/appointments", response_model=ApiResponse[list[ParentMeetingAppointmentRead]])
async def parent_meeting_appointments_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentMeetingAppointmentRead]]:
    return success_response(await list_appointments(scope, user, student_user_id), request_id=get_request_id())


@router.post("/{student_user_id}/meetings/requests/{request_id}/reschedule", response_model=ApiResponse[ParentMeetingRequestRead])
async def parent_meeting_reschedule_route(
    student_user_id: str,
    request_id: str,
    payload: ParentMeetingRescheduleCreate,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentMeetingRequestRead]:
    return success_response(
        await request_reschedule(scope, user, student_user_id, request_id, payload),
        request_id=get_request_id(),
    )


@router.post("/{student_user_id}/meetings/requests/{request_id}/cancel", response_model=ApiResponse[ParentMeetingRequestRead])
async def parent_meeting_cancel_route(
    student_user_id: str,
    request_id: str,
    payload: ParentMeetingCancelCreate,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentMeetingRequestRead]:
    return success_response(
        await cancel_meeting_request(scope, user, student_user_id, request_id, payload),
        request_id=get_request_id(),
    )


@router.get(
    "/{student_user_id}/meetings/appointments/{appointment_id}/outcome",
    response_model=ApiResponse[ParentMeetingOutcomeRead],
)
async def parent_meeting_outcome_route(
    student_user_id: str,
    appointment_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentMeetingOutcomeRead]:
    return success_response(
        await get_meeting_outcome(scope, user, student_user_id, appointment_id),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/services/overview", response_model=ApiResponse[ParentStudentServicesOverviewRead])
async def parent_services_overview_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentStudentServicesOverviewRead]:
    return success_response(await services_overview(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/services/hostel", response_model=ApiResponse[ParentHostelSummaryRead])
async def parent_services_hostel_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentHostelSummaryRead]:
    return success_response(await hostel_summary(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/services/transport", response_model=ApiResponse[ParentTransportSummaryRead])
async def parent_services_transport_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentTransportSummaryRead]:
    return success_response(await transport_summary(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/services/library", response_model=ApiResponse[ParentLibrarySummaryRead])
async def parent_services_library_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentLibrarySummaryRead]:
    return success_response(await library_summary(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/services/mess", response_model=ApiResponse[ParentMessSummaryRead])
async def parent_services_mess_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[ParentMessSummaryRead]:
    return success_response(await mess_summary(scope, user, student_user_id), request_id=get_request_id())


@router.post("/{student_user_id}/services/enquiries", response_model=ApiResponse[ParentServiceEnquiryRead])
async def parent_service_enquiry_route(
    student_user_id: str,
    payload: ParentServiceEnquiryCreate,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[None, Depends(parent_enquiry_rate_limit)],
) -> ApiResponse[ParentServiceEnquiryRead]:
    return success_response(
        await submit_service_enquiry(scope, user, student_user_id, payload),
        request_id=get_request_id(),
    )


@router.get("/{student_user_id}/services/enquiries", response_model=ApiResponse[list[ParentServiceEnquiryRead]])
async def parent_service_enquiries_list_route(
    student_user_id: str,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
) -> ApiResponse[list[ParentServiceEnquiryRead]]:
    return success_response(await list_service_enquiries(scope, user, student_user_id), request_id=get_request_id())


@router.get("/{student_user_id}/reports/export", response_model=ApiResponse[ParentReportExportRead])
async def parent_student_report_export_route(
    student_user_id: str,
    category: ParentReportCategory,
    user: Annotated[User, Depends(parent_user)],
    scope: Annotated[AccessScope, Depends(get_access_scope)],
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