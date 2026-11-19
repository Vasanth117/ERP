"""Examination cell dashboard service."""

from beanie import PydanticObjectId

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_dashboard_filters import build_exam_dashboard_context
from app.modules.examinations.exam_cell_dashboard_repository import ExamCellDashboardRepository
from app.modules.examinations.exam_cell_dashboard_schemas import ExamDashboardFilters, ExamDashboardOverview
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_dashboard,
    require_examination_cell_tenant,
    resolve_department_code_filter,
)

_repo = ExamCellDashboardRepository()


async def get_examination_dashboard(
    scope: AccessScope,
    user: User,
    *,
    academic_year_label: str | None = None,
    semester_label: str | None = None,
    exam_session_id: str | None = None,
    session_code: str | None = None,
    department_code: str | None = None,
    course_code: str | None = None,
    examination_status: ExamSessionStatus | None = None,
    examination_type: ExamSessionType | None = None,
) -> ExamDashboardOverview:
    _ = user
    authorize_examination_cell_dashboard(scope)
    tenant_id = require_examination_cell_tenant(scope)
    dept_scope = await resolve_department_code_filter(scope)
    if dept_scope and department_code and dept_scope != department_code.strip().upper():
        department_code = dept_scope
    elif dept_scope and not department_code:
        department_code = dept_scope

    session_oid: PydanticObjectId | None = None
    if exam_session_id:
        session_oid = to_object_id(exam_session_id, "exam session id")

    ctx = await build_exam_dashboard_context(
        tenant_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        exam_session_id=session_oid,
        session_code=session_code,
        department_code=department_code,
        course_code=course_code,
        examination_status=examination_status,
        examination_type=examination_type,
    )
    filters = ExamDashboardFilters(
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        exam_session_id=exam_session_id,
        session_code=session_code,
        department_code=department_code,
        course_code=course_code,
        examination_status=examination_status,
        examination_type=examination_type,
    )
    return ExamDashboardOverview(
        filters=filters,
        sessions=await _repo.session_counts(ctx),
        registration=await _repo.registration_summary(ctx),
        hall_tickets=await _repo.hall_ticket_summary(ctx),
        marks=await _repo.marks_summary(ctx),
        results=await _repo.results_summary(ctx),
        supplementary_revaluation=await _repo.supplementary_revaluation_summary(ctx),
        incidents=await _repo.incident_summary(ctx),
        upcoming_timetable=await _repo.upcoming_timetable(ctx),
        recent_activities=await _repo.recent_activities(ctx),
        session_statistics=await _repo.session_statistics(ctx),
        department_statistics=await _repo.department_statistics(ctx),
    )