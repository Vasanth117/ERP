"""College admin attendance administration routes."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_access_scope, pagination_params
from app.common.access import AccessScope
from app.common.context import get_request_id
from app.common.envelope import ApiResponse, success_response
from app.common.schemas import Page, Pagination
from app.modules.auth.models import User
from app.modules.college_admin.attendance_admin_schemas import (
    AttendancePolicyRead,
    AttendancePolicyUpsert,
    AttendanceReportGenerate,
    ComplianceSnapshotRead,
    CorrectionDecision,
    CorrectionRequestRead,
    DepartmentAttendanceSummary,
)
from app.modules.college_admin.attendance_admin_service import (
    attendance_history,
    attendance_shortages,
    decide_correction,
    department_summaries,
    generate_compliance_snapshot,
    list_attendance_policies,
    list_correction_requests,
    missing_submissions,
    refresh_submission_monitoring,
    upsert_attendance_policy,
)
from app.modules.college_admin.deps import college_admin_user

router = APIRouter()


@router.put("/policies", response_model=ApiResponse[AttendancePolicyRead])
async def upsert_policy_route(
    payload: AttendancePolicyUpsert,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[AttendancePolicyRead]:
    return success_response(await upsert_attendance_policy(scope, payload), request_id=get_request_id())


@router.get("/policies", response_model=ApiResponse[list[AttendancePolicyRead]])
async def list_policies_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[AttendancePolicyRead]]:
    return success_response(await list_attendance_policies(scope), request_id=get_request_id())


@router.get("/summaries/departments", response_model=ApiResponse[list[DepartmentAttendanceSummary]])
async def department_summary_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[list[DepartmentAttendanceSummary]]:
    return success_response(await department_summaries(scope), request_id=get_request_id())


@router.post("/monitoring/refresh", response_model=ApiResponse[dict])
async def refresh_monitoring_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await refresh_submission_monitoring(scope), request_id=get_request_id())


@router.get("/submissions/missing", response_model=ApiResponse[Page[dict]])
async def missing_submissions_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[dict]]:
    return success_response(await missing_submissions(scope, pagination), request_id=get_request_id())


@router.get("/corrections", response_model=ApiResponse[Page[CorrectionRequestRead]])
async def list_corrections_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
) -> ApiResponse[Page[CorrectionRequestRead]]:
    return success_response(await list_correction_requests(scope, pagination), request_id=get_request_id())


@router.post("/corrections/decide", response_model=ApiResponse[dict])
async def decide_correction_route(
    payload: CorrectionDecision,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[dict]:
    return success_response(await decide_correction(scope, payload), request_id=get_request_id())


@router.get("/shortages", response_model=ApiResponse[list[dict]])
async def shortages_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    course_code: Annotated[str | None, Query()] = None,
    section: Annotated[str | None, Query()] = None,
) -> ApiResponse[list[dict]]:
    return success_response(await attendance_shortages(scope, course_code=course_code, section=section), request_id=get_request_id())


@router.get("/history", response_model=ApiResponse[Page[dict]])
async def attendance_history_route(
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
    pagination: Annotated[Pagination, Depends(pagination_params)],
    faculty_user_id: Annotated[str | None, Query()] = None,
    session_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[Page[dict]]:
    return success_response(
        await attendance_history(scope, faculty_user_id=faculty_user_id, session_date=session_date, pagination=pagination),
        request_id=get_request_id(),
    )


@router.post("/reports/compliance", response_model=ApiResponse[ComplianceSnapshotRead], status_code=status.HTTP_201_CREATED)
async def compliance_report_route(
    payload: AttendanceReportGenerate,
    scope: Annotated[AccessScope, Depends(get_access_scope)],
    _: Annotated[User, Depends(college_admin_user)],
) -> ApiResponse[ComplianceSnapshotRead]:
    return success_response(await generate_compliance_snapshot(scope, payload), request_id=get_request_id())
