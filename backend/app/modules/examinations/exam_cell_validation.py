"""Examination cell — session date and conflict validation."""

from datetime import datetime

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In, NE

from app.core.exceptions import AppError
from app.modules.examinations.exam_cell_enums import ExamSessionStatus, ExamSessionType
from app.modules.examinations.exam_cell_models import ExamSession, ExamSessionAcademicScope
from app.modules.examinations.exam_cell_schemas import ExamSessionAcademicScopeInput, ExamSessionCreate, ExamSessionUpdate


_TERMINAL_STATUSES = frozenset(
    {ExamSessionStatus.CANCELLED, ExamSessionStatus.ARCHIVED, ExamSessionStatus.PUBLISHED}
)


def validate_session_dates(
    *,
    registration_start_at: datetime,
    registration_end_at: datetime,
    examination_start_at: datetime,
    examination_end_at: datetime,
    result_processing_deadline_at: datetime | None,
) -> None:
    if registration_start_at >= registration_end_at:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Registration start must be before registration end",
            status_code=422,
        )
    if examination_start_at >= examination_end_at:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Examination start must be before examination end",
            status_code=422,
        )
    if registration_end_at > examination_start_at:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Registration must close on or before examination start",
            status_code=422,
        )
    if result_processing_deadline_at is not None and result_processing_deadline_at < examination_end_at:
        raise AppError(
            code="VALIDATION_ERROR",
            message="Result processing deadline cannot be before examination end",
            status_code=422,
        )


def _scopes_overlap(left: ExamSessionAcademicScopeInput, right: ExamSessionAcademicScope) -> bool:
    def overlap(a: list[str], b: list[str]) -> bool:
        if not a or not b:
            return True
        return bool(set(a) & set(b))

    return (
        overlap(left.department_codes, right.department_codes)
        and overlap(left.programme_codes, right.programme_codes)
        and overlap(left.batch_labels, right.batch_labels)
        and overlap(left.semester_labels, right.semester_labels)
    )


def _date_ranges_overlap(
    start_a: datetime,
    end_a: datetime,
    start_b: datetime,
    end_b: datetime,
) -> bool:
    return start_a <= end_b and start_b <= end_a


async def assert_no_conflicting_session(
    tenant_id: PydanticObjectId,
    payload: ExamSessionCreate | ExamSessionUpdate,
    *,
    scope_input: ExamSessionAcademicScopeInput,
    examination_type: ExamSessionType,
    academic_year_label: str,
    semester_label: str,
    examination_start_at: datetime,
    examination_end_at: datetime,
    exclude_session_id: PydanticObjectId | None = None,
) -> None:
    candidates = await ExamSession.find(
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.academic_year_label, academic_year_label),
        Eq(ExamSession.semester_label, semester_label),
        Eq(ExamSession.examination_type, examination_type),
        In(ExamSession.status, [s.value for s in ExamSessionStatus if s not in _TERMINAL_STATUSES]),
    ).to_list()
    if exclude_session_id is not None:
        candidates = [c for c in candidates if c.id != exclude_session_id]

    for candidate in candidates:
        if not _date_ranges_overlap(
            examination_start_at,
            examination_end_at,
            candidate.examination_start_at,
            candidate.examination_end_at,
        ):
            continue
        existing_scope = await ExamSessionAcademicScope.find_one(
            Eq(ExamSessionAcademicScope.tenant_id, tenant_id),
            Eq(ExamSessionAcademicScope.exam_session_id, candidate.id),
        )
        if existing_scope is None or _scopes_overlap(scope_input, existing_scope):
            raise AppError(
                code="SESSION_CONFLICT",
                message=(
                    f"Overlapping active session {candidate.session_code} exists for the same term, "
                    "type and academic scope"
                ),
                status_code=409,
            )


async def assert_unique_session_code(
    tenant_id: PydanticObjectId,
    session_code: str,
    *,
    exclude_session_id: PydanticObjectId | None = None,
) -> None:
    query_filters = [
        Eq(ExamSession.tenant_id, tenant_id),
        Eq(ExamSession.session_code, session_code),
    ]
    existing = await ExamSession.find_one(*query_filters)
    if existing is None:
        return
    if exclude_session_id is not None and existing.id == exclude_session_id:
        return
    raise AppError(
        code="DUPLICATE_SESSION_CODE",
        message="Exam session code already exists",
        status_code=409,
    )


async def assert_season_not_bound(
    tenant_id: PydanticObjectId,
    season_id: str,
    *,
    exclude_session_id: PydanticObjectId | None = None,
) -> None:
    filters = [Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.season_id, season_id)]
    if exclude_session_id is not None:
        filters.append(NE(ExamSession.id, exclude_session_id))
    row = await ExamSession.find_one(*filters)
    if row is not None:
        raise AppError(
            code="SEASON_ALREADY_LINKED",
            message="Season is already linked to another exam session",
            status_code=409,
        )