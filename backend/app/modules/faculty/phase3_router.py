"""Faculty Phase 3 — attendance and LMS routes."""

from datetime import date
from typing import Annotated

from fastapi import Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.faculty.attendance_schemas import (
    AssignedClassRead,
    AttendanceCorrectionCreate,
    AttendanceCorrectionRead,
    AttendanceRecordRead,
    AttendanceReportRead,
    AttendanceSessionCreate,
    AttendanceSessionRead,
    AttendanceShortageStudent,
    AttendanceSubmitPayload,
    StudentAttendanceSummary,
    SubjectAttendanceSummary,
)
from app.modules.faculty.attendance_service import (
    attendance_report,
    attendance_shortages,
    create_attendance_session,
    daily_attendance,
    get_session_records,
    list_assigned_classes,
    list_attendance_sessions,
    list_correction_requests,
    missing_submissions,
    roster_for_class,
    student_summaries,
    submit_attendance,
    submit_correction_request,
    subject_summaries,
)
from app.modules.faculty.deps import faculty_user
from app.modules.faculty.lms_schemas import (
    EvaluationCreate,
    EvaluationRead,
    LearningMaterialRead,
    LearningMaterialUpdate,
    LmsAssignmentCreate,
    LmsAssignmentRead,
    LmsAssignmentUpdate,
    ResubmissionAuthorize,
    SubmissionRead,
)
from app.modules.faculty.lms_service import (
    cancel_lms_assignment,
    create_lms_assignment,
    delete_learning_material,
    download_learning_material,
    evaluate_submission,
    authorize_resubmission,
    list_learning_materials,
    list_lms_assignments,
    list_submissions,
    publish_lms_assignment,
    submission_status_summary,
    update_learning_material,
    update_lms_assignment,
    upload_learning_material,
)
from fastapi import APIRouter

phase3_router = APIRouter()


@phase3_router.get("/me/attendance/classes", response_model=ApiResponse[list[AssignedClassRead]])
async def attendance_classes_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[AssignedClassRead]]:
    return success_response(await list_assigned_classes(scope, user), request_id=get_request_id())


@phase3_router.get("/me/attendance/classes/{course_code}/{section}/roster")
async def attendance_roster_route(
    course_code: str,
    section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[dict[str, str]]]:
    return success_response(await roster_for_class(scope, user, course_code, section), request_id=get_request_id())


@phase3_router.post(
    "/me/attendance/sessions",
    response_model=ApiResponse[AttendanceSessionRead],
    status_code=status.HTTP_201_CREATED,
)
async def attendance_session_create_route(
    payload: AttendanceSessionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[AttendanceSessionRead]:
    return success_response(await create_attendance_session(scope, user, payload), request_id=get_request_id())


@phase3_router.get("/me/attendance/sessions", response_model=ApiResponse[list[AttendanceSessionRead]])
async def attendance_sessions_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    course_code: Annotated[str | None, Query()] = None,
    section: Annotated[str | None, Query()] = None,
    session_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[list[AttendanceSessionRead]]:
    return success_response(
        await list_attendance_sessions(scope, user, course_code=course_code, section=section, session_date=session_date),
        request_id=get_request_id(),
    )


@phase3_router.get("/me/attendance/daily", response_model=ApiResponse[list[AttendanceSessionRead]])
async def attendance_daily_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    session_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[list[AttendanceSessionRead]]:
    return success_response(await daily_attendance(scope, user, session_date or date.today()), request_id=get_request_id())


@phase3_router.post("/me/attendance/sessions/{session_id}/submit", response_model=ApiResponse[AttendanceSessionRead])
async def attendance_submit_route(
    session_id: str,
    payload: AttendanceSubmitPayload,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[AttendanceSessionRead]:
    data = await submit_attendance(scope, user, to_object_id(session_id, "session id"), payload)
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/me/attendance/sessions/{session_id}/records", response_model=ApiResponse[list[AttendanceRecordRead]])
async def attendance_records_route(
    session_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[AttendanceRecordRead]]:
    return success_response(
        await get_session_records(scope, user, to_object_id(session_id, "session id")),
        request_id=get_request_id(),
    )


@phase3_router.get(
    "/me/attendance/classes/{course_code}/{section}/summaries/students",
    response_model=ApiResponse[list[StudentAttendanceSummary]],
)
async def attendance_student_summary_route(
    course_code: str,
    section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[StudentAttendanceSummary]]:
    return success_response(await student_summaries(scope, user, course_code, section), request_id=get_request_id())


@phase3_router.get(
    "/me/attendance/classes/{course_code}/{section}/summaries/subjects",
    response_model=ApiResponse[list[SubjectAttendanceSummary]],
)
async def attendance_subject_summary_route(
    course_code: str,
    section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[SubjectAttendanceSummary]]:
    return success_response(await subject_summaries(scope, user, course_code, section), request_id=get_request_id())


@phase3_router.get(
    "/me/attendance/classes/{course_code}/{section}/shortages",
    response_model=ApiResponse[list[AttendanceShortageStudent]],
)
async def attendance_shortages_route(
    course_code: str,
    section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[AttendanceShortageStudent]]:
    return success_response(await attendance_shortages(scope, user, course_code, section), request_id=get_request_id())


@phase3_router.get("/me/attendance/missing-submissions")
async def attendance_missing_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[dict]]:
    return success_response(await missing_submissions(scope, user), request_id=get_request_id())


@phase3_router.post(
    "/me/attendance/corrections",
    response_model=ApiResponse[AttendanceCorrectionRead],
    status_code=status.HTTP_201_CREATED,
)
async def attendance_correction_route(
    payload: AttendanceCorrectionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[AttendanceCorrectionRead]:
    return success_response(await submit_correction_request(scope, user, payload), request_id=get_request_id())


@phase3_router.get("/me/attendance/corrections", response_model=ApiResponse[Page[AttendanceCorrectionRead]])
async def attendance_corrections_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[AttendanceCorrectionRead]]:
    return success_response(await list_correction_requests(scope, user, pagination), request_id=get_request_id())


@phase3_router.get(
    "/me/attendance/classes/{course_code}/{section}/report",
    response_model=ApiResponse[AttendanceReportRead],
)
async def attendance_report_route(
    course_code: str,
    section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[AttendanceReportRead]:
    return success_response(await attendance_report(scope, user, course_code, section), request_id=get_request_id())


@phase3_router.post(
    "/me/lms/materials",
    response_model=ApiResponse[LearningMaterialRead],
    status_code=status.HTTP_201_CREATED,
)
async def lms_material_upload_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    course_code: Annotated[str, Form()],
    title: Annotated[str, Form()],
    section: Annotated[str | None, Form()] = None,
    subject_id: Annotated[str | None, Form()] = None,
    unit_no: Annotated[int | None, Form()] = None,
    file: UploadFile = File(...),
) -> ApiResponse[LearningMaterialRead]:
    data = await upload_learning_material(
        scope, user, course_code=course_code, section=section, subject_id=subject_id, unit_no=unit_no, title=title, upload=file
    )
    return success_response(data, request_id=get_request_id())


@phase3_router.get("/me/lms/materials", response_model=ApiResponse[list[LearningMaterialRead]])
async def lms_materials_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    course_code: Annotated[str, Query()],
    section: Annotated[str | None, Query()] = None,
    published_only: Annotated[bool, Query()] = False,
) -> ApiResponse[list[LearningMaterialRead]]:
    return success_response(
        await list_learning_materials(scope, user, course_code, section=section, published_only=published_only),
        request_id=get_request_id(),
    )


@phase3_router.patch("/me/lms/materials/{material_id}", response_model=ApiResponse[LearningMaterialRead])
async def lms_material_update_route(
    material_id: str,
    payload: LearningMaterialUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[LearningMaterialRead]:
    return success_response(
        await update_learning_material(scope, user, to_object_id(material_id, "material id"), payload),
        request_id=get_request_id(),
    )


@phase3_router.delete("/me/lms/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def lms_material_delete_route(
    material_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> None:
    await delete_learning_material(scope, user, to_object_id(material_id, "material id"))


@phase3_router.get("/me/lms/materials/{material_id}/download")
async def lms_material_download_route(
    material_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> Response:
    data, name, mime = await download_learning_material(scope, user, to_object_id(material_id, "material id"))
    return Response(content=data, media_type=mime, headers={"Content-Disposition": f'attachment; filename="{name}"'})


@phase3_router.post(
    "/me/lms/assignments",
    response_model=ApiResponse[LmsAssignmentRead],
    status_code=status.HTTP_201_CREATED,
)
async def lms_assignment_create_route(
    payload: LmsAssignmentCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[LmsAssignmentRead]:
    return success_response(await create_lms_assignment(scope, user, payload), request_id=get_request_id())


@phase3_router.patch("/me/lms/assignments/{assignment_id}", response_model=ApiResponse[LmsAssignmentRead])
async def lms_assignment_update_route(
    assignment_id: str,
    payload: LmsAssignmentUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[LmsAssignmentRead]:
    return success_response(
        await update_lms_assignment(scope, user, to_object_id(assignment_id, "assignment id"), payload),
        request_id=get_request_id(),
    )


@phase3_router.post("/me/lms/assignments/{assignment_id}/publish", response_model=ApiResponse[LmsAssignmentRead])
async def lms_assignment_publish_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[LmsAssignmentRead]:
    return success_response(await publish_lms_assignment(scope, user, to_object_id(assignment_id, "assignment id")), request_id=get_request_id())


@phase3_router.post("/me/lms/assignments/{assignment_id}/cancel", response_model=ApiResponse[LmsAssignmentRead])
async def lms_assignment_cancel_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[LmsAssignmentRead]:
    return success_response(await cancel_lms_assignment(scope, user, to_object_id(assignment_id, "assignment id")), request_id=get_request_id())


@phase3_router.get("/me/lms/assignments", response_model=ApiResponse[list[LmsAssignmentRead]])
async def lms_assignments_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    course_code: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[LmsAssignmentRead]]:
    return success_response(await list_lms_assignments(scope, user, course_code), request_id=get_request_id())


@phase3_router.get("/me/lms/assignments/{assignment_id}/submissions", response_model=ApiResponse[list[SubmissionRead]])
async def lms_submissions_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[SubmissionRead]]:
    return success_response(await list_submissions(scope, user, to_object_id(assignment_id, "assignment id")), request_id=get_request_id())


@phase3_router.get("/me/lms/assignments/{assignment_id}/submission-status")
async def lms_submission_status_route(
    assignment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[dict[str, int]]:
    return success_response(
        await submission_status_summary(scope, user, to_object_id(assignment_id, "assignment id")),
        request_id=get_request_id(),
    )


@phase3_router.post(
    "/me/lms/submissions/{submission_id}/evaluate",
    response_model=ApiResponse[EvaluationRead],
)
async def lms_evaluate_route(
    submission_id: str,
    payload: EvaluationCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[EvaluationRead]:
    return success_response(
        await evaluate_submission(scope, user, to_object_id(submission_id, "submission id"), payload),
        request_id=get_request_id(),
    )


@phase3_router.post("/me/lms/assignments/{assignment_id}/resubmissions")
async def lms_resubmission_route(
    assignment_id: str,
    payload: ResubmissionAuthorize,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[dict[str, str]]:
    return success_response(
        await authorize_resubmission(scope, user, to_object_id(assignment_id, "assignment id"), payload),
        request_id=get_request_id(),
    )
