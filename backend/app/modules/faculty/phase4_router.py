"""Faculty Phase 4 — assessment and student support routes."""

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.faculty.assessment_schemas import (
    ApprovalHistoryRead,
    AssessmentComponentRead,
    AssessmentReportRead,
    AssignedAssessmentRead,
    EligibleStudentRead,
    MarksBatchRead,
    MarksCorrectionCreate,
    MarksCorrectionRead,
    MarksDraftSave,
    MarksSubmitRequest,
    StudentMarkRead,
)
from app.modules.faculty.assessment_service import (
    approval_history_for_batch,
    approved_marks,
    correction_history,
    eligible_students,
    incomplete_evaluations,
    list_assessment_components,
    list_assigned_assessments,
    list_marks_batches,
    save_marks_draft,
    submit_marks,
    submit_marks_correction,
    subject_marks_report,
)
from app.modules.faculty.deps import faculty_user
from app.modules.faculty.student_support_service import (
    create_followup,
    create_improvement_plan,
    create_mentoring_record,
    generate_course_report,
    generate_student_report,
    pending_followups,
    record_counselling,
    student_performance_list,
    students_requiring_support,
    update_followup,
)
from app.modules.faculty.support_schemas import (
    AcademicReportRead,
    CounsellingSessionCreate,
    CounsellingSessionRead,
    FollowupCreate,
    FollowupRead,
    FollowupUpdate,
    ImprovementPlanCreate,
    ImprovementPlanRead,
    MentoringRecordCreate,
    MentoringRecordRead,
    StudentPerformanceRead,
)

phase4_router = APIRouter()


@phase4_router.get("/me/assessments", response_model=ApiResponse[list[AssignedAssessmentRead]])
async def assigned_assessments_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[AssignedAssessmentRead]]:
    return success_response(await list_assigned_assessments(scope, user), request_id=get_request_id())


@phase4_router.get("/me/assessments/{assessment_id}/components", response_model=ApiResponse[list[AssessmentComponentRead]])
async def assessment_components_route(
    assessment_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[AssessmentComponentRead]]:
    return success_response(await list_assessment_components(scope, user, assessment_id), request_id=get_request_id())


@phase4_router.get(
    "/me/assessments/{assessment_id}/courses/{course_code}/sections/{section}/students",
    response_model=ApiResponse[list[EligibleStudentRead]],
)
async def assessment_eligible_students_route(
    assessment_id: str,
    course_code: str,
    section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[EligibleStudentRead]]:
    return success_response(
        await eligible_students(scope, user, assessment_id, course_code, section),
        request_id=get_request_id(),
    )


@phase4_router.put("/me/assessments/marks/draft", response_model=ApiResponse[MarksBatchRead])
async def marks_draft_route(
    payload: MarksDraftSave,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[MarksBatchRead]:
    return success_response(await save_marks_draft(scope, user, payload), request_id=get_request_id())


@phase4_router.post("/me/assessments/marks/submit", response_model=ApiResponse[MarksBatchRead])
async def marks_submit_route(
    payload: MarksSubmitRequest,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[MarksBatchRead]:
    return success_response(await submit_marks(scope, user, payload), request_id=get_request_id())


@phase4_router.get("/me/assessments/marks/batches", response_model=ApiResponse[list[MarksBatchRead]])
async def marks_batches_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[MarksBatchRead]]:
    return success_response(await list_marks_batches(scope, user), request_id=get_request_id())


@phase4_router.get("/me/assessments/marks/incomplete", response_model=ApiResponse[list[MarksBatchRead]])
async def marks_incomplete_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[MarksBatchRead]]:
    return success_response(await incomplete_evaluations(scope, user), request_id=get_request_id())


@phase4_router.get(
    "/me/assessments/{assessment_id}/components/{component_id}/sections/{section}/approved",
    response_model=ApiResponse[list[StudentMarkRead]],
)
async def approved_marks_route(
    assessment_id: str,
    component_id: str,
    section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[StudentMarkRead]]:
    return success_response(
        await approved_marks(scope, user, assessment_id, component_id, section),
        request_id=get_request_id(),
    )


@phase4_router.post(
    "/me/assessments/marks/corrections",
    response_model=ApiResponse[MarksCorrectionRead],
    status_code=status.HTTP_201_CREATED,
)
async def marks_correction_route(
    payload: MarksCorrectionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[MarksCorrectionRead]:
    return success_response(await submit_marks_correction(scope, user, payload), request_id=get_request_id())


@phase4_router.get("/me/assessments/marks/corrections", response_model=ApiResponse[Page[MarksCorrectionRead]])
async def marks_corrections_list_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[MarksCorrectionRead]]:
    return success_response(await correction_history(scope, user, pagination), request_id=get_request_id())


@phase4_router.get("/me/assessments/marks/batches/{batch_id}/approval-history", response_model=ApiResponse[list[ApprovalHistoryRead]])
async def marks_approval_history_route(
    batch_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[ApprovalHistoryRead]]:
    return success_response(
        await approval_history_for_batch(scope, user, to_object_id(batch_id, "batch id")),
        request_id=get_request_id(),
    )


@phase4_router.get(
    "/me/assessments/{assessment_id}/components/{component_id}/courses/{course_code}/sections/{section}/report",
    response_model=ApiResponse[AssessmentReportRead],
)
async def assessment_report_route(
    assessment_id: str,
    component_id: str,
    course_code: str,
    section: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[AssessmentReportRead]:
    return success_response(
        await subject_marks_report(scope, user, assessment_id, component_id, course_code, section),
        request_id=get_request_id(),
    )


@phase4_router.get("/me/student-support/performance", response_model=ApiResponse[list[StudentPerformanceRead]])
async def student_performance_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[StudentPerformanceRead]]:
    return success_response(await student_performance_list(scope, user), request_id=get_request_id())


@phase4_router.get("/me/student-support/at-risk", response_model=ApiResponse[list[StudentPerformanceRead]])
async def students_at_risk_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[StudentPerformanceRead]]:
    return success_response(await students_requiring_support(scope, user), request_id=get_request_id())


@phase4_router.post(
    "/me/student-support/mentoring",
    response_model=ApiResponse[MentoringRecordRead],
    status_code=status.HTTP_201_CREATED,
)
async def mentoring_create_route(
    payload: MentoringRecordCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[MentoringRecordRead]:
    return success_response(await create_mentoring_record(scope, user, payload), request_id=get_request_id())


@phase4_router.post(
    "/me/student-support/counselling",
    response_model=ApiResponse[CounsellingSessionRead],
    status_code=status.HTTP_201_CREATED,
)
async def counselling_create_route(
    payload: CounsellingSessionCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[CounsellingSessionRead]:
    return success_response(await record_counselling(scope, user, payload), request_id=get_request_id())


@phase4_router.post(
    "/me/student-support/followups",
    response_model=ApiResponse[FollowupRead],
    status_code=status.HTTP_201_CREATED,
)
async def followup_create_route(
    payload: FollowupCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[FollowupRead]:
    return success_response(await create_followup(scope, user, payload), request_id=get_request_id())


@phase4_router.patch("/me/student-support/followups/{followup_id}", response_model=ApiResponse[FollowupRead])
async def followup_update_route(
    followup_id: str,
    payload: FollowupUpdate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[FollowupRead]:
    return success_response(
        await update_followup(scope, user, to_object_id(followup_id, "followup id"), payload),
        request_id=get_request_id(),
    )


@phase4_router.get("/me/student-support/followups/pending", response_model=ApiResponse[list[FollowupRead]])
async def followups_pending_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[list[FollowupRead]]:
    return success_response(await pending_followups(scope, user), request_id=get_request_id())


@phase4_router.post(
    "/me/student-support/improvement-plans",
    response_model=ApiResponse[ImprovementPlanRead],
    status_code=status.HTTP_201_CREATED,
)
async def improvement_plan_route(
    payload: ImprovementPlanCreate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[ImprovementPlanRead]:
    return success_response(await create_improvement_plan(scope, user, payload), request_id=get_request_id())


@phase4_router.post(
    "/me/student-support/reports/courses/{course_code}",
    response_model=ApiResponse[AcademicReportRead],
    status_code=status.HTTP_201_CREATED,
)
async def course_report_route(
    course_code: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[AcademicReportRead]:
    return success_response(await generate_course_report(scope, user, course_code), request_id=get_request_id())


@phase4_router.post(
    "/me/student-support/reports/students/{student_user_id}",
    response_model=ApiResponse[AcademicReportRead],
    status_code=status.HTTP_201_CREATED,
)
async def student_report_route(
    student_user_id: str,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    user: Annotated[User, Depends(faculty_user)],
) -> ApiResponse[AcademicReportRead]:
    return success_response(
        await generate_student_report(scope, user, to_object_id(student_user_id, "student id")),
        request_id=get_request_id(),
    )
