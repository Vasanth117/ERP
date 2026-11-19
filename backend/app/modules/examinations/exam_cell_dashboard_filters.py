"""Examination dashboard filter resolution."""

from dataclasses import dataclass
from datetime import datetime

from beanie import PydanticObjectId
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_models import ExamSession


@dataclass(frozen=True)
class ExamDashboardContext:
    tenant_id: PydanticObjectId
    academic_year_label: str | None
    semester_label: str | None
    exam_session_id: PydanticObjectId | None
    session_code: str | None
    department_code: str | None
    course_code: str | None
    examination_status: ExamSessionStatus | None
    examination_type: ExamSessionType | None
    season_ids: frozenset[str]
    now: datetime


async def build_exam_dashboard_context(
    tenant_id: PydanticObjectId,
    *,
    academic_year_label: str | None,
    semester_label: str | None,
    exam_session_id: PydanticObjectId | None,
    session_code: str | None,
    department_code: str | None,
    course_code: str | None,
    examination_status: ExamSessionStatus | None,
    examination_type: ExamSessionType | None,
) -> ExamDashboardContext:
    session_query: dict = {"tenant_id": tenant_id}
    if exam_session_id is not None:
        session_query["_id"] = exam_session_id
    elif session_code:
        session_query["session_code"] = session_code.strip().upper()
    if academic_year_label:
        session_query["academic_year_label"] = academic_year_label.strip()
    if semester_label:
        session_query["semester_label"] = semester_label.strip()
    if examination_status:
        session_query["status"] = examination_status.value
    if examination_type:
        session_query["examination_type"] = examination_type.value

    sessions = await ExamSession.find(session_query).to_list()
    if exam_session_id is not None and not sessions:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)

    season_ids: set[str] = set()
    for row in sessions:
        if row.season_id:
            season_ids.add(row.season_id)

    return ExamDashboardContext(
        tenant_id=tenant_id,
        academic_year_label=academic_year_label,
        semester_label=semester_label,
        exam_session_id=exam_session_id,
        session_code=session_code.strip().upper() if session_code else None,
        department_code=department_code.strip().upper() if department_code else None,
        course_code=course_code.strip().upper() if course_code else None,
        examination_status=examination_status,
        examination_type=examination_type,
        season_ids=frozenset(season_ids),
        now=utcnow(),
    )