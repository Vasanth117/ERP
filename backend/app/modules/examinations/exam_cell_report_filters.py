"""Examination report filter resolution."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.ids import to_object_id
from app.core.exceptions import AppError
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_report_schemas import ExamReportFilters


@dataclass(frozen=True)
class ExamReportContext:
    tenant_id: PydanticObjectId
    filters: ExamReportFilters
    session_ids: frozenset[PydanticObjectId]
    window_start: datetime
    window_end: datetime


def _date_bounds(date_from: date, date_to: date) -> tuple[datetime, datetime]:
    if date_to < date_from:
        raise AppError(code="VALIDATION_ERROR", message="date_to must be on or after date_from", status_code=422)
    start = datetime.combine(date_from, datetime.min.time(), tzinfo=timezone.utc)
    end = datetime.combine(date_to + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    return start, end


async def build_report_context(tenant_id: PydanticObjectId, filters: ExamReportFilters) -> ExamReportContext:
    df = filters.date_from or date.today() - timedelta(days=365)
    dt = filters.date_to or date.today()
    window_start, window_end = _date_bounds(df, dt)

    query: dict = {"tenant_id": tenant_id}
    if filters.academic_year_label:
        query["academic_year_label"] = filters.academic_year_label
    if filters.semester_label:
        query["semester_label"] = filters.semester_label
    if filters.examination_type:
        query["examination_type"] = filters.examination_type.value
    if filters.exam_session_id:
        query["_id"] = to_object_id(filters.exam_session_id, "exam_session_id")

    sessions = await ExamSession.find(query).to_list()
    if filters.department_code or filters.programme_code or filters.course_code:
        # Session list is not department-scoped in phase 1 model; filters apply at aggregate stage.
        pass
    session_ids = frozenset(s.id for s in sessions if s.id is not None)
    # If explicit session id but not found, empty scope
    if filters.exam_session_id and not session_ids:
        session_ids = frozenset({to_object_id(filters.exam_session_id, "exam_session_id")})
    elif not filters.exam_session_id and not session_ids:
        session_ids = frozenset(s.id for s in await ExamSession.find(Eq(ExamSession.tenant_id, tenant_id)).to_list() if s.id)

    return ExamReportContext(
        tenant_id=tenant_id,
        filters=filters,
        session_ids=session_ids,
        window_start=window_start,
        window_end=window_end,
    )