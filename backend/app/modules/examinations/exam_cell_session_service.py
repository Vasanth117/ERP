"""Examination cell — exam session lifecycle."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_enums import (
    ExamSessionStatus,
    assert_exam_session_transition,
    target_status_for_action,
)
from app.modules.examinations.exam_cell_models import ExamSession, ExamSessionAcademicScope, ExamSessionStatusHistory
from app.modules.examinations.exam_cell_policy import authorize_examination_cell_manage, require_examination_cell_tenant
from app.modules.examinations.exam_cell_schemas import (
    ExamSessionAcademicScopeInput,
    ExamSessionCreate,
    ExamSessionListFilters,
    ExamSessionRead,
    ExamSessionStatusHistoryRead,
    ExamSessionTransitionRequest,
    ExamSessionUpdate,
)
from app.modules.examinations.exam_cell_validation import (
    assert_no_conflicting_session,
    assert_season_not_bound,
    assert_unique_session_code,
    validate_session_dates,
)


def _new_session_id() -> str:
    return f"es_{uuid4().hex[:10]}"


async def _load_scope(tenant_id: PydanticObjectId, exam_session_id: PydanticObjectId) -> ExamSessionAcademicScope | None:
    return await ExamSessionAcademicScope.find_one(
        Eq(ExamSessionAcademicScope.tenant_id, tenant_id),
        Eq(ExamSessionAcademicScope.exam_session_id, exam_session_id),
    )


async def create_exam_session(scope: AccessScope, user: User, payload: ExamSessionCreate) -> ExamSessionRead:
    authorize_examination_cell_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    session_code = payload.session_code.strip().upper()
    validate_session_dates(
        registration_start_at=payload.registration_start_at,
        registration_end_at=payload.registration_end_at,
        examination_start_at=payload.examination_start_at,
        examination_end_at=payload.examination_end_at,
        result_processing_deadline_at=payload.result_processing_deadline_at,
    )
    await assert_unique_session_code(tenant_id, session_code)
    season_id = payload.season_id.strip() if payload.season_id else None
    if season_id:
        await assert_season_not_bound(tenant_id, season_id)
    await assert_no_conflicting_session(
        tenant_id,
        payload,
        scope_input=payload.academic_scope,
        examination_type=payload.examination_type,
        academic_year_label=payload.academic_year_label,
        semester_label=payload.semester_label,
        examination_start_at=payload.examination_start_at,
        examination_end_at=payload.examination_end_at,
    )
    doc = ExamSession(
        tenant_id=tenant_id,
        session_id=_new_session_id(),
        session_code=session_code,
        name=payload.name.strip(),
        examination_type=payload.examination_type,
        academic_year_label=payload.academic_year_label.strip(),
        semester_label=payload.semester_label.strip(),
        season_id=season_id,
        registration_start_at=payload.registration_start_at,
        registration_end_at=payload.registration_end_at,
        examination_start_at=payload.examination_start_at,
        examination_end_at=payload.examination_end_at,
        result_processing_deadline_at=payload.result_processing_deadline_at,
        status=ExamSessionStatus.DRAFT,
        created_by=user.id,
        updated_by=user.id,
    )
    await doc.insert()
    scope_doc = ExamSessionAcademicScope(
        tenant_id=tenant_id,
        exam_session_id=doc.id,
        department_codes=list(payload.academic_scope.department_codes),
        programme_codes=list(payload.academic_scope.programme_codes),
        batch_labels=list(payload.academic_scope.batch_labels),
        semester_labels=list(payload.academic_scope.semester_labels),
    )
    await scope_doc.insert()
    await ExamSessionStatusHistory(
        tenant_id=tenant_id,
        exam_session_id=doc.id,
        from_status=None,
        to_status=ExamSessionStatus.DRAFT,
        actor_id=user.id,
        note="Session created",
    ).insert()
    await record_exam_activity(
        tenant_id,
        actor_id=user.id,
        action="exam_session.created",
        summary=f"Created exam session {session_code}",
        exam_session_id=doc.id,
        season_id=season_id,
        metadata={"session_code": session_code},
    )
    return ExamSessionRead.from_documents(doc, scope_doc)


async def update_exam_session(
    scope: AccessScope,
    user: User,
    exam_session_id: PydanticObjectId,
    payload: ExamSessionUpdate,
) -> ExamSessionRead:
    authorize_examination_cell_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, exam_session_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    if doc.status not in {ExamSessionStatus.DRAFT, ExamSessionStatus.SCHEDULED}:
        raise AppError(
            code="SESSION_LOCKED",
            message="Only draft or scheduled sessions can be edited",
            status_code=409,
        )
    scope_doc = await _load_scope(tenant_id, doc.id)
    scope_input = payload.academic_scope
    registration_start = payload.registration_start_at or doc.registration_start_at
    registration_end = payload.registration_end_at or doc.registration_end_at
    exam_start = payload.examination_start_at or doc.examination_start_at
    exam_end = payload.examination_end_at or doc.examination_end_at
    result_deadline = (
        payload.result_processing_deadline_at
        if payload.result_processing_deadline_at is not None
        else doc.result_processing_deadline_at
    )
    validate_session_dates(
        registration_start_at=registration_start,
        registration_end_at=registration_end,
        examination_start_at=exam_start,
        examination_end_at=exam_end,
        result_processing_deadline_at=result_deadline,
    )
    academic_scope = scope_input or ExamSessionAcademicScopeInput(
        department_codes=list(scope_doc.department_codes) if scope_doc else [],
        programme_codes=list(scope_doc.programme_codes) if scope_doc else [],
        batch_labels=list(scope_doc.batch_labels) if scope_doc else [],
        semester_labels=list(scope_doc.semester_labels) if scope_doc else [],
    )
    await assert_no_conflicting_session(
        tenant_id,
        payload,
        scope_input=academic_scope,  # type: ignore[arg-type]
        examination_type=doc.examination_type,
        academic_year_label=doc.academic_year_label,
        semester_label=doc.semester_label,
        examination_start_at=exam_start,
        examination_end_at=exam_end,
        exclude_session_id=doc.id,
    )
    if payload.name is not None:
        doc.name = payload.name.strip()
    doc.registration_start_at = registration_start
    doc.registration_end_at = registration_end
    doc.examination_start_at = exam_start
    doc.examination_end_at = exam_end
    doc.result_processing_deadline_at = result_deadline
    doc.updated_by = user.id
    doc.updated_at = utcnow()
    await doc.save()
    if scope_input is not None:
        if scope_doc is None:
            scope_doc = ExamSessionAcademicScope(
                tenant_id=tenant_id,
                exam_session_id=doc.id,
                department_codes=list(scope_input.department_codes),
                programme_codes=list(scope_input.programme_codes),
                batch_labels=list(scope_input.batch_labels),
                semester_labels=list(scope_input.semester_labels),
            )
            await scope_doc.insert()
        else:
            scope_doc.department_codes = list(scope_input.department_codes)
            scope_doc.programme_codes = list(scope_input.programme_codes)
            scope_doc.batch_labels = list(scope_input.batch_labels)
            scope_doc.semester_labels = list(scope_input.semester_labels)
            scope_doc.updated_at = utcnow()
            await scope_doc.save()
    await record_exam_activity(
        tenant_id,
        actor_id=user.id,
        action="exam_session.updated",
        summary=f"Updated exam session {doc.session_code}",
        exam_session_id=doc.id,
        season_id=doc.season_id,
    )
    scope_doc = await _load_scope(tenant_id, doc.id)
    return ExamSessionRead.from_documents(doc, scope_doc)


async def get_exam_session(scope: AccessScope, exam_session_id: PydanticObjectId) -> ExamSessionRead:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, exam_session_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    scope_doc = await _load_scope(tenant_id, doc.id)
    return ExamSessionRead.from_documents(doc, scope_doc)


async def list_exam_sessions(
    scope: AccessScope,
    filters: ExamSessionListFilters,
    pagination: Pagination,
) -> Page[ExamSessionRead]:
    tenant_id = require_examination_cell_tenant(scope)
    query: dict = {"tenant_id": tenant_id}
    if filters.academic_year_label:
        query["academic_year_label"] = filters.academic_year_label.strip()
    if filters.semester_label:
        query["semester_label"] = filters.semester_label.strip()
    if filters.examination_type:
        query["examination_type"] = filters.examination_type.value
    if filters.status:
        query["status"] = filters.status.value
    if filters.session_code:
        query["session_code"] = filters.session_code.strip().upper()

  # Department filter via scope join when needed
    if filters.department_code:
        dept = filters.department_code.strip().upper()
        scoped_ids = [
            s.exam_session_id
            for s in await ExamSessionAcademicScope.find(
                {"tenant_id": tenant_id, "department_codes": dept}
            ).to_list()
        ]
        institutional_wide = [
            s.exam_session_id
            for s in await ExamSessionAcademicScope.find(
                {"tenant_id": tenant_id, "department_codes": {"$size": 0}}
            ).to_list()
        ]
        allowed_ids = set(scoped_ids) | set(institutional_wide)
        if allowed_ids:
            query["_id"] = {"$in": list(allowed_ids)}
    rows = await ExamSession.find(query).sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    total = await ExamSession.find(query).count()
    results: list[ExamSessionRead] = []
    for row in rows:
        scope_doc = await _load_scope(tenant_id, row.id)
        results.append(ExamSessionRead.from_documents(row, scope_doc))
    return Page(items=results, total=total, limit=pagination.limit, offset=pagination.offset)


async def transition_exam_session(
    scope: AccessScope,
    user: User,
    exam_session_id: PydanticObjectId,
    payload: ExamSessionTransitionRequest,
) -> ExamSessionRead:
    authorize_examination_cell_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, exam_session_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    target = target_status_for_action(payload.action)
    try:
        assert_exam_session_transition(doc.status, target)
    except ValueError as exc:
        raise AppError(code="INVALID_TRANSITION", message=str(exc), status_code=409) from exc
    previous = doc.status
    doc.status = target
    doc.updated_by = user.id
    doc.updated_at = utcnow()
    if target == ExamSessionStatus.CANCELLED:
        doc.cancelled_at = utcnow()
    if target == ExamSessionStatus.ARCHIVED:
        doc.archived_at = utcnow()
    await doc.save()
    await ExamSessionStatusHistory(
        tenant_id=tenant_id,
        exam_session_id=doc.id,
        from_status=previous,
        to_status=target,
        actor_id=user.id,
        note=payload.note,
    ).insert()
    await record_exam_activity(
        tenant_id,
        actor_id=user.id,
        action=f"exam_session.{payload.action.value}",
        summary=f"Session {doc.session_code} moved to {target.value}",
        exam_session_id=doc.id,
        season_id=doc.season_id,
        metadata={"from_status": previous.value, "to_status": target.value},
    )
    scope_doc = await _load_scope(tenant_id, doc.id)
    return ExamSessionRead.from_documents(doc, scope_doc)


async def list_exam_session_history(
    scope: AccessScope,
    exam_session_id: PydanticObjectId,
) -> list[ExamSessionStatusHistoryRead]:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamSession.find_one(Eq(ExamSession.tenant_id, tenant_id), Eq(ExamSession.id, exam_session_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam session not found", status_code=404)
    rows = await ExamSessionStatusHistory.find(
        Eq(ExamSessionStatusHistory.tenant_id, tenant_id),
        Eq(ExamSessionStatusHistory.exam_session_id, exam_session_id),
    ).sort("-created_at").to_list()
    return [
        ExamSessionStatusHistoryRead(
            from_status=r.from_status,
            to_status=r.to_status,
            actor_id=str(r.actor_id) if r.actor_id else None,
            note=r.note,
            created_at=r.created_at,
        )
        for r in rows
    ]