"""Examination cell — timetable management service."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_timetable_approve,
    authorize_examination_cell_timetable_manage,
    authorize_examination_cell_timetable_publish,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_timetable_conflict import detect_entry_conflicts, load_timetable_entries
from app.modules.examinations.exam_cell_timetable_enums import (
    ExamScheduleApprovalDecision,
    ExamTimetableEntryStatus,
    ExamTimetableRevisionType,
    ExamTimetableStatus,
    assert_timetable_transition,
)
from app.modules.examinations.exam_cell_timetable_models import (
    ExamScheduleApproval,
    ExamTimetable,
    ExamTimetableEntry,
    ExamTimetableRevision,
)
from app.modules.examinations.exam_cell_timetable_schemas import (
    ExamScheduleApprovalRead,
    ExamTimetableApprovalRequest,
    ExamTimetableCreate,
    ExamTimetableEntryCreate,
    ExamTimetableEntryRead,
    ExamTimetableEntryReschedule,
    ExamTimetableRead,
    ExamTimetableRevisionRead,
    ExamTimetableValidationResult,
)
from app.modules.examinations.exam_cell_timetable_validation import (
    assert_course_reference,
    assert_editable_timetable,
    assert_exam_session_for_timetable,
    assert_venue_assignment,
    build_student_group_label,
    validate_entry_schedule,
)


def _timetable_id() -> str:
    return f"ett_{uuid4().hex[:10]}"


def _approval_id() -> str:
    return f"esa_{uuid4().hex[:10]}"


async def _revision(
    tenant_id: PydanticObjectId,
    timetable: ExamTimetable,
    *,
    change_type: ExamTimetableRevisionType,
    summary: str,
    actor_id: PydanticObjectId | None,
    previous: dict | None = None,
    new: dict | None = None,
) -> None:
    await ExamTimetableRevision(
        tenant_id=tenant_id,
        timetable_id=timetable.id,
        revision_number=timetable.revision_number,
        change_type=change_type,
        summary=summary,
        previous_values=dict(previous or {}),
        new_values=dict(new or {}),
        actor_id=actor_id,
    ).insert()


async def create_exam_timetable(scope: AccessScope, user: User, payload: ExamTimetableCreate) -> ExamTimetableRead:
    authorize_examination_cell_timetable_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    session_oid = to_object_id(payload.exam_session_id, "exam session id")
    await assert_exam_session_for_timetable(tenant_id, session_oid)
    doc = ExamTimetable(
        tenant_id=tenant_id,
        timetable_id=_timetable_id(),
        exam_session_id=session_oid,
        title=payload.title.strip(),
        shift_labels=[s.strip() for s in payload.shift_labels if s.strip()],
        created_by=user.id,
    )
    await doc.insert()
    await _revision(
        tenant_id,
        doc,
        change_type=ExamTimetableRevisionType.CREATED,
        summary="Timetable created",
        actor_id=user.id,
    )
    await record_exam_activity(
        tenant_id,
        actor_id=user.id,
        action="exam_timetable.created",
        summary=f"Created exam timetable {doc.timetable_id}",
        exam_session_id=session_oid,
        metadata={"timetable_id": doc.timetable_id},
    )
    return ExamTimetableRead.from_document(doc, entry_count=0)


async def get_exam_timetable(scope: AccessScope, timetable_oid: PydanticObjectId) -> ExamTimetableRead:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamTimetable.find_one(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.id, timetable_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam timetable not found", status_code=404)
    count = await ExamTimetableEntry.find({"tenant_id": tenant_id, "timetable_id": doc.id}).count()
    return ExamTimetableRead.from_document(doc, entry_count=count)


async def list_exam_timetables(
    scope: AccessScope,
    *,
    exam_session_id: str | None,
    pagination: Pagination,
) -> Page[ExamTimetableRead]:
    tenant_id = require_examination_cell_tenant(scope)
    query: dict = {"tenant_id": tenant_id}
    if exam_session_id:
        query["exam_session_id"] = to_object_id(exam_session_id, "exam session id")
    rows = await ExamTimetable.find(query).sort("-updated_at").skip(pagination.offset).limit(pagination.limit).to_list()
    total = await ExamTimetable.find(query).count()
    items: list[ExamTimetableRead] = []
    for row in rows:
        count = await ExamTimetableEntry.find({"tenant_id": tenant_id, "timetable_id": row.id}).count()
        items.append(ExamTimetableRead.from_document(row, entry_count=count))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def add_timetable_entry(
    scope: AccessScope,
    user: User,
    timetable_oid: PydanticObjectId,
    payload: ExamTimetableEntryCreate,
) -> ExamTimetableEntryRead:
    authorize_examination_cell_timetable_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    timetable = await assert_editable_timetable(tenant_id, timetable_oid)
    session = await assert_exam_session_for_timetable(tenant_id, timetable.exam_session_id)
    await assert_course_reference(
        tenant_id,
        course_code=payload.course_code,
        academic_year_label=session.academic_year_label,
        semester_label=session.semester_label,
        programme_code=payload.programme_code,
    )
    campus_oid = await assert_venue_assignment(
        tenant_id,
        centre_code=payload.centre_code,
        room_label=payload.room_label,
        facility_id=payload.facility_id,
        campus_id=payload.campus_id,
    )
    if await ExamTimetableEntry.find_one(
        Eq(ExamTimetableEntry.tenant_id, tenant_id),
        Eq(ExamTimetableEntry.timetable_id, timetable_oid),
        Eq(ExamTimetableEntry.entry_code, payload.entry_code),
    ):
        raise AppError(code="DUPLICATE_ENTRY_CODE", message="Timetable entry code already exists", status_code=409)
    duration = validate_entry_schedule(payload.scheduled_start, payload.scheduled_end)
    group_label = build_student_group_label(
        programme_code=payload.programme_code,
        batch_label=payload.batch_label,
        section=payload.section,
        course_code=payload.course_code,
    )
    entry = ExamTimetableEntry(
        tenant_id=tenant_id,
        timetable_id=timetable_oid,
        entry_code=payload.entry_code,
        course_code=payload.course_code,
        subject_code=payload.subject_code,
        paper_code=payload.paper_code,
        programme_code=payload.programme_code,
        batch_label=payload.batch_label,
        section=payload.section,
        student_group_label=group_label,
        scheduled_start=payload.scheduled_start,
        scheduled_end=payload.scheduled_end,
        duration_minutes=duration,
        shift_label=payload.shift_label,
        session_label=payload.session_label,
        centre_code=payload.centre_code.strip().upper() if payload.centre_code else None,
        facility_id=payload.facility_id.strip() if payload.facility_id else None,
        room_label=payload.room_label.strip().upper() if payload.room_label else None,
        campus_id=campus_oid,
        metadata=dict(payload.metadata),
    )
    prospective = (await load_timetable_entries(tenant_id, timetable_oid)) + [entry]
    conflicts = detect_entry_conflicts(prospective)
    if conflicts:
        raise AppError(
            code="TIMETABLE_CONFLICT",
            message="New entry introduces scheduling conflicts",
            status_code=409,
            details=conflicts,
        )
    await entry.insert()
    timetable.updated_at = utcnow()
    await timetable.save()
    await _revision(
        tenant_id,
        timetable,
        change_type=ExamTimetableRevisionType.ENTRY_ADDED,
        summary=f"Added entry {entry.entry_code}",
        actor_id=user.id,
        new={"entry_code": entry.entry_code},
    )
    return ExamTimetableEntryRead.from_document(entry)


async def validate_exam_timetable(scope: AccessScope, timetable_oid: PydanticObjectId) -> ExamTimetableValidationResult:
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamTimetable.find_one(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.id, timetable_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam timetable not found", status_code=404)
    entries = await load_timetable_entries(tenant_id, timetable_oid)
    conflicts = detect_entry_conflicts(entries)
    return ExamTimetableValidationResult(conflict_count=len(conflicts), conflicts=conflicts)


async def submit_exam_timetable(
    scope: AccessScope,
    user: User,
    timetable_oid: PydanticObjectId,
) -> ExamTimetableRead:
    authorize_examination_cell_timetable_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamTimetable.find_one(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.id, timetable_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam timetable not found", status_code=404)
    validation = await validate_exam_timetable(scope, timetable_oid)
    if validation.conflict_count:
        raise AppError(
            code="TIMETABLE_CONFLICT",
            message="Resolve timetable conflicts before submission",
            status_code=409,
            details=validation.conflicts,
        )
    entry_count = await ExamTimetableEntry.find({"tenant_id": tenant_id, "timetable_id": timetable_oid}).count()
    if entry_count == 0:
        raise AppError(code="VALIDATION_ERROR", message="Cannot submit an empty timetable", status_code=422)
    try:
        assert_timetable_transition(doc.status, ExamTimetableStatus.IN_REVIEW)
    except ValueError as exc:
        raise AppError(code="INVALID_TRANSITION", message=str(exc), status_code=409) from exc
    previous = doc.status
    doc.status = ExamTimetableStatus.IN_REVIEW
    doc.updated_at = utcnow()
    await doc.save()
    await ExamScheduleApproval(
        tenant_id=tenant_id,
        timetable_id=doc.id,
        approval_id=_approval_id(),
        decision=ExamScheduleApprovalDecision.PENDING,
        actor_id=user.id,
        note="Submitted for approval",
    ).insert()
    await _revision(
        tenant_id,
        doc,
        change_type=ExamTimetableRevisionType.SUBMITTED,
        summary="Submitted for approval",
        actor_id=user.id,
        previous={"status": previous.value},
        new={"status": doc.status.value},
    )
    return await get_exam_timetable(scope, timetable_oid)


async def approve_exam_timetable(
    scope: AccessScope,
    user: User,
    timetable_oid: PydanticObjectId,
    body: ExamTimetableApprovalRequest,
) -> ExamTimetableRead:
    authorize_examination_cell_timetable_approve(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamTimetable.find_one(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.id, timetable_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam timetable not found", status_code=404)
    try:
        assert_timetable_transition(doc.status, ExamTimetableStatus.APPROVED)
    except ValueError as exc:
        raise AppError(code="INVALID_TRANSITION", message=str(exc), status_code=409) from exc
    previous = doc.status
    doc.status = ExamTimetableStatus.APPROVED
    doc.approved_by = user.id
    doc.updated_at = utcnow()
    await doc.save()
    await ExamScheduleApproval(
        tenant_id=tenant_id,
        timetable_id=doc.id,
        approval_id=_approval_id(),
        decision=ExamScheduleApprovalDecision.APPROVED,
        actor_id=user.id,
        note=body.note,
    ).insert()
    await _revision(
        tenant_id,
        doc,
        change_type=ExamTimetableRevisionType.APPROVED,
        summary="Timetable approved",
        actor_id=user.id,
        previous={"status": previous.value},
        new={"status": doc.status.value},
    )
    return await get_exam_timetable(scope, timetable_oid)


async def reject_exam_timetable(
    scope: AccessScope,
    user: User,
    timetable_oid: PydanticObjectId,
    body: ExamTimetableApprovalRequest,
) -> ExamTimetableRead:
    authorize_examination_cell_timetable_approve(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamTimetable.find_one(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.id, timetable_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam timetable not found", status_code=404)
    try:
        assert_timetable_transition(doc.status, ExamTimetableStatus.DRAFT)
    except ValueError as exc:
        raise AppError(code="INVALID_TRANSITION", message=str(exc), status_code=409) from exc
    previous = doc.status
    doc.status = ExamTimetableStatus.DRAFT
    doc.updated_at = utcnow()
    await doc.save()
    await ExamScheduleApproval(
        tenant_id=tenant_id,
        timetable_id=doc.id,
        approval_id=_approval_id(),
        decision=ExamScheduleApprovalDecision.REJECTED,
        actor_id=user.id,
        note=body.note,
    ).insert()
    await _revision(
        tenant_id,
        doc,
        change_type=ExamTimetableRevisionType.REJECTED,
        summary="Timetable rejected",
        actor_id=user.id,
        previous={"status": previous.value},
        new={"status": doc.status.value},
    )
    return await get_exam_timetable(scope, timetable_oid)


async def publish_exam_timetable(scope: AccessScope, user: User, timetable_oid: PydanticObjectId) -> ExamTimetableRead:
    authorize_examination_cell_timetable_publish(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamTimetable.find_one(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.id, timetable_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam timetable not found", status_code=404)
    try:
        assert_timetable_transition(doc.status, ExamTimetableStatus.PUBLISHED)
    except ValueError as exc:
        raise AppError(code="INVALID_TRANSITION", message=str(exc), status_code=409) from exc
    validation = await validate_exam_timetable(scope, timetable_oid)
    if validation.conflict_count:
        raise AppError(code="TIMETABLE_CONFLICT", message="Conflicts must be resolved before publish", status_code=409)
    previous = doc.status
    doc.status = ExamTimetableStatus.PUBLISHED
    doc.published_version += 1
    doc.published_by = user.id
    doc.published_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await _revision(
        tenant_id,
        doc,
        change_type=ExamTimetableRevisionType.PUBLISHED,
        summary="Timetable published",
        actor_id=user.id,
        previous={"status": previous.value},
        new={"status": doc.status.value, "published_version": doc.published_version},
    )
    await record_exam_activity(
        tenant_id,
        actor_id=user.id,
        action="exam_timetable.published",
        summary=f"Published exam timetable {doc.timetable_id}",
        exam_session_id=doc.exam_session_id,
        metadata={"timetable_id": doc.timetable_id, "version": doc.published_version},
    )
    return await get_exam_timetable(scope, timetable_oid)


async def revise_exam_timetable(scope: AccessScope, user: User, timetable_oid: PydanticObjectId) -> ExamTimetableRead:
    authorize_examination_cell_timetable_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    doc = await ExamTimetable.find_one(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.id, timetable_oid))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Exam timetable not found", status_code=404)
    if doc.status != ExamTimetableStatus.PUBLISHED:
        raise AppError(code="INVALID_TRANSITION", message="Only published timetables can be revised", status_code=409)
    previous = doc.status
    doc.revision_number += 1
    doc.status = ExamTimetableStatus.DRAFT
    doc.updated_at = utcnow()
    await doc.save()
    await _revision(
        tenant_id,
        doc,
        change_type=ExamTimetableRevisionType.REVISED,
        summary="Timetable opened for revision",
        actor_id=user.id,
        previous={"status": previous.value},
        new={"status": doc.status.value, "revision_number": doc.revision_number},
    )
    return await get_exam_timetable(scope, timetable_oid)


async def cancel_timetable_entry(
    scope: AccessScope,
    user: User,
    timetable_oid: PydanticObjectId,
    entry_code: str,
) -> ExamTimetableEntryRead:
    authorize_examination_cell_timetable_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    timetable = await ExamTimetable.find_one(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.id, timetable_oid))
    if timetable is None:
        raise AppError(code="NOT_FOUND", message="Exam timetable not found", status_code=404)
    if timetable.status not in {ExamTimetableStatus.DRAFT, ExamTimetableStatus.PUBLISHED}:
        raise AppError(code="TIMETABLE_LOCKED", message="Entries cannot be cancelled in the current timetable status", status_code=409)
    entry = await ExamTimetableEntry.find_one(
        Eq(ExamTimetableEntry.tenant_id, tenant_id),
        Eq(ExamTimetableEntry.timetable_id, timetable_oid),
        Eq(ExamTimetableEntry.entry_code, entry_code.strip().upper()),
    )
    if entry is None:
        raise AppError(code="NOT_FOUND", message="Timetable entry not found", status_code=404)
    entry.status = ExamTimetableEntryStatus.CANCELLED
    entry.updated_at = utcnow()
    await entry.save()
    await _revision(
        tenant_id,
        timetable,
        change_type=ExamTimetableRevisionType.ENTRY_CANCELLED,
        summary=f"Cancelled entry {entry.entry_code}",
        actor_id=user.id,
    )
    return ExamTimetableEntryRead.from_document(entry)


async def reschedule_timetable_entry(
    scope: AccessScope,
    user: User,
    timetable_oid: PydanticObjectId,
    entry_code: str,
    payload: ExamTimetableEntryReschedule,
) -> ExamTimetableEntryRead:
    authorize_examination_cell_timetable_manage(scope)
    tenant_id = require_examination_cell_tenant(scope)
    timetable = await assert_editable_timetable(tenant_id, timetable_oid)
    entry = await ExamTimetableEntry.find_one(
        Eq(ExamTimetableEntry.tenant_id, tenant_id),
        Eq(ExamTimetableEntry.timetable_id, timetable_oid),
        Eq(ExamTimetableEntry.entry_code, entry_code.strip().upper()),
    )
    if entry is None:
        raise AppError(code="NOT_FOUND", message="Timetable entry not found", status_code=404)
    previous = {
        "scheduled_start": entry.scheduled_start.isoformat(),
        "scheduled_end": entry.scheduled_end.isoformat(),
        "centre_code": entry.centre_code,
        "room_label": entry.room_label,
        "facility_id": entry.facility_id,
    }
    campus_oid = await assert_venue_assignment(
        tenant_id,
        centre_code=payload.centre_code or entry.centre_code,
        room_label=payload.room_label or entry.room_label,
        facility_id=payload.facility_id or entry.facility_id,
        campus_id=str(entry.campus_id) if entry.campus_id else None,
    )
    duration = validate_entry_schedule(payload.scheduled_start, payload.scheduled_end)
    entry.scheduled_start = payload.scheduled_start
    entry.scheduled_end = payload.scheduled_end
    entry.duration_minutes = duration
    if payload.centre_code:
        entry.centre_code = payload.centre_code.strip().upper()
    if payload.room_label:
        entry.room_label = payload.room_label.strip().upper()
    if payload.facility_id:
        entry.facility_id = payload.facility_id.strip()
    entry.campus_id = campus_oid
    entry.status = ExamTimetableEntryStatus.RESCHEDULED
    entry.updated_at = utcnow()
    await entry.save()
    conflicts = detect_entry_conflicts(await load_timetable_entries(tenant_id, timetable_oid))
    if conflicts:
        raise AppError(code="TIMETABLE_CONFLICT", message="Reschedule introduces conflicts", status_code=409, details=conflicts)
    await _revision(
        tenant_id,
        timetable,
        change_type=ExamTimetableRevisionType.ENTRY_RESCHEDULED,
        summary=payload.note or f"Rescheduled entry {entry.entry_code}",
        actor_id=user.id,
        previous=previous,
        new={
            "scheduled_start": entry.scheduled_start.isoformat(),
            "scheduled_end": entry.scheduled_end.isoformat(),
        },
    )
    return ExamTimetableEntryRead.from_document(entry)


async def list_timetable_entries(
    scope: AccessScope,
    timetable_oid: PydanticObjectId,
) -> list[ExamTimetableEntryRead]:
    tenant_id = require_examination_cell_tenant(scope)
    if await ExamTimetable.find_one(Eq(ExamTimetable.tenant_id, tenant_id), Eq(ExamTimetable.id, timetable_oid)) is None:
        raise AppError(code="NOT_FOUND", message="Exam timetable not found", status_code=404)
    rows = await load_timetable_entries(tenant_id, timetable_oid)
    return [ExamTimetableEntryRead.from_document(r) for r in rows]


async def list_timetable_revisions(scope: AccessScope, timetable_oid: PydanticObjectId) -> list[ExamTimetableRevisionRead]:
    tenant_id = require_examination_cell_tenant(scope)
    rows = await ExamTimetableRevision.find(
        Eq(ExamTimetableRevision.tenant_id, tenant_id),
        Eq(ExamTimetableRevision.timetable_id, timetable_oid),
    ).sort("-created_at").to_list()
    return [ExamTimetableRevisionRead.from_document(r) for r in rows]


async def list_schedule_approvals(scope: AccessScope, timetable_oid: PydanticObjectId) -> list[ExamScheduleApprovalRead]:
    tenant_id = require_examination_cell_tenant(scope)
    rows = await ExamScheduleApproval.find(
        Eq(ExamScheduleApproval.tenant_id, tenant_id),
        Eq(ExamScheduleApproval.timetable_id, timetable_oid),
    ).sort("-created_at").to_list()
    return [
        ExamScheduleApprovalRead(
            approval_id=r.approval_id,
            decision=r.decision,
            actor_id=str(r.actor_id) if r.actor_id else None,
            note=r.note,
            created_at=r.created_at,
        )
        for r in rows
    ]