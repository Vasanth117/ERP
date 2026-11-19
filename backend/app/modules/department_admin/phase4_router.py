"""Department Admin phase 4 — timetable and attendance oversight."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.department_admin.attendance_oversight_service import (
    attendance_classes,
    attendance_overview,
    attendance_shortages,
    attendance_students,
    attendance_subjects,
    faculty_submissions,
    get_correction_request,
    list_correction_requests,
    list_discrepancies,
    missing_attendance,
    review_correction_request,
    scan_discrepancies,
)
from app.modules.department_admin.deps import department_admin_user
from app.modules.department_admin.phase4_schemas import (
    AttendanceClassSummary,
    AttendanceCorrectionRead,
    AttendanceCorrectionReview,
    AttendanceDiscrepancyRead,
    AttendanceFacultySubmissionRead,
    AttendanceMissingSessionRead,
    AttendanceOverviewFilters,
    AttendanceOverviewRead,
    AttendanceShortageRead,
    AttendanceStudentSummary,
    AttendanceSubjectSummary,
    TimetableChangeCreate,
    TimetableChangeRead,
    TimetableConflictRead,
    TimetablePlanCreate,
    TimetablePlanRead,
    TimetablePlanUpdate,
    TimetablePublishBody,
    TimetableSlotCreate,
    TimetableSlotRead,
    TimetableSlotUpdate,
    TimetableValidationResult,
)
from app.modules.department_admin.timetable_management_service import (
    add_slot,
    approve_timetable,
    create_timetable,
    create_timetable_change,
    get_timetable,
    list_plan_slots,
    list_timetable_conflicts,
    list_timetables,
    publish_timetable,
    submit_timetable,
    timetable_view_by_faculty,
    timetable_view_by_room,
    timetable_view_by_section,
    update_slot,
    update_timetable,
    validate_timetable,
)

phase4_router = APIRouter()


def _attendance_filters(
    date_from: Annotated[date | None, Query()] = None,
    date_to: Annotated[date | None, Query()] = None,
    programme_code: Annotated[str | None, Query()] = None,
    batch_label: Annotated[str | None, Query()] = None,
    section_code: Annotated[str | None, Query()] = None,
) -> AttendanceOverviewFilters:
    return AttendanceOverviewFilters(
        date_from=date_from,
        date_to=date_to,
        programme_code=programme_code,
        batch_label=batch_label,
        section_code=section_code,
    )


@phase4_router.get("/timetables", response_model=ApiResponse[Page[TimetablePlanRead]])
async def timetables_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[TimetablePlanRead]]:
    return success_response(await list_timetables(scope, user, pagination=pagination), request_id=get_request_id())


@phase4_router.post("/timetables", response_model=ApiResponse[TimetablePlanRead])
async def timetables_create_route(
    payload: TimetablePlanCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TimetablePlanRead]:
    return success_response(await create_timetable(scope, user, payload), request_id=get_request_id())


@phase4_router.get("/timetables/section/{section_id}", response_model=ApiResponse[list[TimetableSlotRead]])
async def timetable_section_view_route(
    section_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[TimetableSlotRead]]:
    return success_response(await timetable_view_by_section(scope, user, section_id), request_id=get_request_id())


@phase4_router.get("/timetables/faculty/{faculty_id}", response_model=ApiResponse[list[TimetableSlotRead]])
async def timetable_faculty_view_route(
    faculty_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[TimetableSlotRead]]:
    return success_response(await timetable_view_by_faculty(scope, user, faculty_id), request_id=get_request_id())


@phase4_router.get("/timetables/rooms/{room_id}", response_model=ApiResponse[list[TimetableSlotRead]])
async def timetable_room_view_route(
    room_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[TimetableSlotRead]]:
    return success_response(await timetable_view_by_room(scope, user, room_id), request_id=get_request_id())


@phase4_router.get("/timetables/{timetable_id}", response_model=ApiResponse[TimetablePlanRead])
async def timetables_get_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TimetablePlanRead]:
    return success_response(await get_timetable(scope, user, timetable_id), request_id=get_request_id())


@phase4_router.patch("/timetables/{timetable_id}", response_model=ApiResponse[TimetablePlanRead])
async def timetables_update_route(
    timetable_id: str,
    payload: TimetablePlanUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TimetablePlanRead]:
    return success_response(await update_timetable(scope, user, timetable_id, payload), request_id=get_request_id())


@phase4_router.get("/timetables/{timetable_id}/slots", response_model=ApiResponse[list[TimetableSlotRead]])
async def timetables_slots_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[TimetableSlotRead]]:
    return success_response(await list_plan_slots(scope, user, timetable_id), request_id=get_request_id())


@phase4_router.post("/timetables/{timetable_id}/slots", response_model=ApiResponse[TimetableSlotRead])
async def timetables_slot_create_route(
    timetable_id: str,
    payload: TimetableSlotCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TimetableSlotRead]:
    return success_response(await add_slot(scope, user, timetable_id, payload), request_id=get_request_id())


@phase4_router.patch("/timetables/slots/{slot_id}", response_model=ApiResponse[TimetableSlotRead])
async def timetables_slot_update_route(
    slot_id: str,
    payload: TimetableSlotUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TimetableSlotRead]:
    return success_response(await update_slot(scope, user, slot_id, payload), request_id=get_request_id())


@phase4_router.post("/timetables/{timetable_id}/validate", response_model=ApiResponse[TimetableValidationResult])
async def timetables_validate_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TimetableValidationResult]:
    return success_response(await validate_timetable(scope, user, timetable_id), request_id=get_request_id())


@phase4_router.post("/timetables/{timetable_id}/submit", response_model=ApiResponse[TimetablePlanRead])
async def timetables_submit_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TimetablePlanRead]:
    return success_response(await submit_timetable(scope, user, timetable_id), request_id=get_request_id())


@phase4_router.post("/timetables/{timetable_id}/approve", response_model=ApiResponse[TimetablePlanRead])
async def timetables_approve_route(
    timetable_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TimetablePlanRead]:
    return success_response(await approve_timetable(scope, user, timetable_id), request_id=get_request_id())


@phase4_router.post("/timetables/{timetable_id}/publish", response_model=ApiResponse[TimetablePlanRead])
async def timetables_publish_route(
    timetable_id: str,
    body: TimetablePublishBody,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TimetablePlanRead]:
    return success_response(await publish_timetable(scope, user, timetable_id, body), request_id=get_request_id())


@phase4_router.get("/timetable-conflicts", response_model=ApiResponse[list[TimetableConflictRead]])
async def timetable_conflicts_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    plan_id: Annotated[str, Query()],
) -> ApiResponse[list[TimetableConflictRead]]:
    return success_response(await list_timetable_conflicts(scope, user, plan_id), request_id=get_request_id())


@phase4_router.post("/timetables/{timetable_id}/changes", response_model=ApiResponse[TimetableChangeRead])
async def timetables_change_route(
    timetable_id: str,
    payload: TimetableChangeCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[TimetableChangeRead]:
    return success_response(await create_timetable_change(scope, user, timetable_id, payload), request_id=get_request_id())


@phase4_router.get("/attendance/overview", response_model=ApiResponse[AttendanceOverviewRead])
async def attendance_overview_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[AttendanceOverviewFilters, Depends(_attendance_filters)],
) -> ApiResponse[AttendanceOverviewRead]:
    return success_response(await attendance_overview(scope, user, filters), request_id=get_request_id())


@phase4_router.get("/attendance/classes", response_model=ApiResponse[list[AttendanceClassSummary]])
async def attendance_classes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    filters: Annotated[AttendanceOverviewFilters, Depends(_attendance_filters)],
) -> ApiResponse[list[AttendanceClassSummary]]:
    return success_response(await attendance_classes(scope, user, filters), request_id=get_request_id())


@phase4_router.get("/attendance/subjects", response_model=ApiResponse[list[AttendanceSubjectSummary]])
async def attendance_subjects_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[AttendanceSubjectSummary]]:
    return success_response(await attendance_subjects(scope, user), request_id=get_request_id())


@phase4_router.get("/attendance/students", response_model=ApiResponse[Page[AttendanceStudentSummary]])
async def attendance_students_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AttendanceStudentSummary]]:
    return success_response(await attendance_students(scope, user, pagination=pagination), request_id=get_request_id())


@phase4_router.get("/attendance/faculty-submissions", response_model=ApiResponse[list[AttendanceFacultySubmissionRead]])
async def attendance_faculty_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[AttendanceFacultySubmissionRead]]:
    return success_response(await faculty_submissions(scope, user), request_id=get_request_id())


@phase4_router.get("/attendance/missing", response_model=ApiResponse[Page[AttendanceMissingSessionRead]])
async def attendance_missing_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AttendanceMissingSessionRead]]:
    return success_response(await missing_attendance(scope, user, pagination=pagination), request_id=get_request_id())


@phase4_router.get("/attendance/shortages", response_model=ApiResponse[list[AttendanceShortageRead]])
async def attendance_shortages_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[AttendanceShortageRead]]:
    return success_response(await attendance_shortages(scope, user), request_id=get_request_id())


@phase4_router.get("/attendance/discrepancies", response_model=ApiResponse[Page[AttendanceDiscrepancyRead]])
async def attendance_discrepancies_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AttendanceDiscrepancyRead]]:
    return success_response(await list_discrepancies(scope, user, pagination=pagination), request_id=get_request_id())


@phase4_router.post("/attendance/discrepancies/scan", response_model=ApiResponse[list[AttendanceDiscrepancyRead]])
async def attendance_discrepancies_scan_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[list[AttendanceDiscrepancyRead]]:
    return success_response(await scan_discrepancies(scope, user), request_id=get_request_id())


@phase4_router.get("/attendance/correction-requests", response_model=ApiResponse[Page[AttendanceCorrectionRead]])
async def attendance_corrections_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AttendanceCorrectionRead]]:
    return success_response(await list_correction_requests(scope, user, pagination=pagination), request_id=get_request_id())


@phase4_router.get("/attendance/correction-requests/{request_id}", response_model=ApiResponse[AttendanceCorrectionRead])
async def attendance_correction_get_route(
    request_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AttendanceCorrectionRead]:
    return success_response(await get_correction_request(scope, user, request_id), request_id=get_request_id())


@phase4_router.post("/attendance/correction-requests/{request_id}/review", response_model=ApiResponse[AttendanceCorrectionRead])
async def attendance_correction_review_route(
    request_id: str,
    payload: AttendanceCorrectionReview,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(department_admin_user)],
) -> ApiResponse[AttendanceCorrectionRead]:
    return success_response(await review_correction_request(scope, user, request_id, payload), request_id=get_request_id())