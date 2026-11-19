"""Examination cell — result processing and publication."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import as_utc_aware, utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_grading_enums import (
    ExamResultReviewStatus,
    ExamSubjectResultOutcome,
    ExamSubjectResultStatus,
)
from app.modules.examinations.exam_cell_grading_models import ExamSemesterResult, ExamStudentSubjectResult
from app.modules.examinations.exam_cell_models import ExamSession
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_publication_manage,
    authorize_examination_cell_publication_publish,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_publication_enums import (
    ExamPublicationHistoryAction,
    ExamPublicationScopeType,
    ExamPublicationStatus,
)
from app.modules.examinations.exam_cell_publication_models import (
    ExamPublicationBatch,
    ExamPublicationHistory,
    ExamResultPublication,
    ExamStudentResultVisibility,
)
from app.modules.examinations.exam_cell_publication_schemas import (
    ExamPublicationApprove,
    ExamPublicationCreate,
    ExamPublicationHistoryRead,
    ExamPublicationProcessRequest,
    ExamPublicationRead,
    ExamPublicationReleaseRequest,
    ExamPublicationReviseRequest,
    ExamPublicationValidationReport,
    ExamPublicationWithholdRequest,
    ExamStudentPublishedResultRead,
)
from app.modules.examinations.exam_cell_result_models import ExamResultApprovalWorkflow
from app.modules.students.models import StudentProfile


def _publication_id() -> str:
    return f"erp_{uuid4().hex[:10]}"


def _batch_id() -> str:
    return f"epb_{uuid4().hex[:10]}"


def _history_id() -> str:
    return f"eph_{uuid4().hex[:10]}"


def _visibility_id() -> str:
    return f"erv_{uuid4().hex[:10]}"


async def _history(
    tenant_id: PydanticObjectId,
    *,
    publication_id: str,
    exam_session_id: PydanticObjectId,
    action: ExamPublicationHistoryAction,
    actor_id: PydanticObjectId | None,
    note: str | None = None,
    metadata: dict | None = None,
) -> None:
    await ExamPublicationHistory(
        tenant_id=tenant_id,
        history_id=_history_id(),
        publication_id=publication_id,
        exam_session_id=exam_session_id,
        action=action,
        actor_id=actor_id,
        note=note,
        metadata=dict(metadata or {}),
    ).insert()


async def validate_publication_ready(
    scope: AccessScope,
    payload: ExamPublicationProcessRequest,
) -> ExamPublicationValidationReport:
    tenant_id = require_examination_cell_tenant(scope)
    session_oid = to_object_id(payload.exam_session_id, "exam_session_id")

    workflow = None
    if payload.workflow_id:
        workflow = await ExamResultApprovalWorkflow.find_one(
            Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
            Eq(ExamResultApprovalWorkflow.workflow_id, payload.workflow_id),
        )
    else:
        workflow = await ExamResultApprovalWorkflow.find_one(
            Eq(ExamResultApprovalWorkflow.tenant_id, tenant_id),
            Eq(ExamResultApprovalWorkflow.exam_session_id, session_oid),
        )

    workflow_approved = workflow is not None and workflow.status == ExamResultReviewStatus.APPROVED

    subjects = await ExamStudentSubjectResult.find(
        Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
        Eq(ExamStudentSubjectResult.exam_session_id, session_oid),
    ).to_list()

    pending = sum(1 for s in subjects if s.status != ExamSubjectResultStatus.APPROVED)
    withheld = sum(
        1
        for s in subjects
        if s.outcome in {ExamSubjectResultOutcome.WITHHELD, ExamSubjectResultOutcome.MALPRACTICE}
    )
    unresolved = sum(1 for s in subjects if s.outcome == ExamSubjectResultOutcome.INCOMPLETE)

    policy_id = subjects[0].policy_id if subjects else None
    policy_version = subjects[0].policy_version if subjects else None

    issues: list[str] = []
    if not workflow_approved:
        issues.append("Result review workflow is not approved")
    if pending:
        issues.append(f"{pending} subject results are not approved")
    if unresolved:
        issues.append(f"{unresolved} subject results are incomplete")
    if not subjects:
        issues.append("No subject results found for session")

    ready = workflow_approved and pending == 0 and unresolved == 0 and bool(subjects)

    return ExamPublicationValidationReport(
        ready=ready,
        workflow_approved=workflow_approved,
        pending_results=pending,
        withheld_results=withheld,
        unresolved_results=unresolved,
        approved_subjects=len(subjects) - pending,
        policy_id=policy_id,
        policy_version=policy_version,
        issues=issues,
    )


async def create_publication(scope: AccessScope, actor: User, payload: ExamPublicationCreate) -> ExamPublicationRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_publication_manage(scope)

    session_oid = to_object_id(payload.exam_session_id, "exam_session_id")
    report = await validate_publication_ready(
        scope,
        ExamPublicationProcessRequest(exam_session_id=payload.exam_session_id, workflow_id=payload.workflow_id),
    )
    if not report.ready:
        raise AppError(code="VALIDATION_ERROR", message="; ".join(report.issues), status_code=422)

    semester_rows = await ExamSemesterResult.find(
        Eq(ExamSemesterResult.tenant_id, tenant_id),
        Eq(ExamSemesterResult.exam_session_id, session_oid),
        Eq(ExamSemesterResult.status, ExamSubjectResultStatus.APPROVED),
    ).to_list()

    if payload.scope_type == ExamPublicationScopeType.PROGRAMME and payload.programme_code:
        semester_rows = [r for r in semester_rows if r.programme_code == payload.programme_code]
    elif payload.scope_type == ExamPublicationScopeType.SEMESTER and payload.semester_label:
        semester_rows = [r for r in semester_rows if r.semester_label == payload.semester_label]

    student_ids = [str(r.student_user_id) for r in semester_rows]

    status = ExamPublicationStatus.SCHEDULED if payload.publish_at else ExamPublicationStatus.DRAFT
    if payload.publish_at and as_utc_aware(payload.publish_at) <= utcnow():
        status = ExamPublicationStatus.DRAFT

    doc = ExamResultPublication(
        tenant_id=tenant_id,
        publication_id=_publication_id(),
        exam_session_id=session_oid,
        workflow_id=payload.workflow_id,
        scope_type=payload.scope_type,
        programme_code=payload.programme_code,
        semester_label=payload.semester_label,
        student_group_label=payload.student_group_label,
        status=status,
        policy_id=report.policy_id,
        policy_version=report.policy_version,
        publish_at=payload.publish_at,
        visibility_default=payload.visibility_default,
        pending_count=report.pending_results,
        withheld_count=report.withheld_results,
        unresolved_count=report.unresolved_results,
        students_included=len(student_ids),
        dataset_snapshot={
            "student_user_ids": student_ids,
            "policy_id": report.policy_id,
            "policy_version": report.policy_version,
        },
        created_by=actor.id,
    )
    await doc.insert()

    await ExamPublicationBatch(
        tenant_id=tenant_id,
        batch_id=_batch_id(),
        publication_id=doc.publication_id,
        exam_session_id=session_oid,
        student_count=len(student_ids),
        status=status,
    ).insert()

    for student_oid in {r.student_user_id for r in semester_rows}:
        await ExamStudentResultVisibility(
            tenant_id=tenant_id,
            visibility_id=_visibility_id(),
            publication_id=doc.publication_id,
            exam_session_id=session_oid,
            student_user_id=student_oid,
            visible=payload.visibility_default,
            withheld=False,
        ).insert()

    await _history(
        tenant_id,
        publication_id=doc.publication_id,
        exam_session_id=session_oid,
        action=ExamPublicationHistoryAction.CREATED,
        actor_id=actor.id,
    )
    await _history(
        tenant_id,
        publication_id=doc.publication_id,
        exam_session_id=session_oid,
        action=ExamPublicationHistoryAction.VALIDATED,
        actor_id=actor.id,
        metadata={"ready": True},
    )
    if payload.publish_at:
        await _history(
            tenant_id,
            publication_id=doc.publication_id,
            exam_session_id=session_oid,
            action=ExamPublicationHistoryAction.SCHEDULED,
            actor_id=actor.id,
            note=str(payload.publish_at),
        )

    return ExamPublicationRead.from_doc(doc)


async def approve_publication(scope: AccessScope, actor: User, publication_id: str, payload: ExamPublicationApprove) -> ExamPublicationRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_publication_publish(scope)

    doc = await ExamResultPublication.find_one(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.publication_id, publication_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Publication not found", status_code=404)
    if doc.status not in {ExamPublicationStatus.DRAFT, ExamPublicationStatus.SCHEDULED, ExamPublicationStatus.REVISED}:
        raise AppError(code="INVALID_STATE", message="Publication cannot be approved from current status", status_code=409)

    doc.status = ExamPublicationStatus.PENDING_APPROVAL
    doc.approved_by = actor.id
    doc.updated_at = utcnow()
    await doc.save()
    await _history(
        tenant_id,
        publication_id=doc.publication_id,
        exam_session_id=doc.exam_session_id,
        action=ExamPublicationHistoryAction.SUBMITTED,
        actor_id=actor.id,
        note=payload.note,
    )
    return ExamPublicationRead.from_doc(doc)


async def publish_results(scope: AccessScope, actor: User, publication_id: str) -> ExamPublicationRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_publication_publish(scope)

    doc = await ExamResultPublication.find_one(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.publication_id, publication_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Publication not found", status_code=404)

    if doc.publish_at and as_utc_aware(doc.publish_at) > utcnow():
        raise AppError(code="PUBLICATION_SCHEDULED", message="Scheduled publish time has not been reached", status_code=409)

    if doc.status not in {
        ExamPublicationStatus.PENDING_APPROVAL,
        ExamPublicationStatus.DRAFT,
        ExamPublicationStatus.SCHEDULED,
        ExamPublicationStatus.REVISED,
    }:
        raise AppError(code="INVALID_STATE", message="Publication is not ready to publish", status_code=409)

    report = await validate_publication_ready(
        scope,
        ExamPublicationProcessRequest(exam_session_id=str(doc.exam_session_id), workflow_id=doc.workflow_id),
    )
    if not report.ready:
        raise AppError(code="VALIDATION_ERROR", message="; ".join(report.issues), status_code=422)

    from app.common.context import get_request_id
    from app.modules.examinations.exam_cell_sod import assert_publication_separation

    await assert_publication_separation(tenant_id, actor, doc, request_id=get_request_id())

    now = utcnow()
    doc.status = ExamPublicationStatus.PUBLISHED
    doc.published_at = now
    doc.updated_at = now
    await doc.save()

    await ExamPublicationBatch.find(
        Eq(ExamPublicationBatch.tenant_id, tenant_id),
        Eq(ExamPublicationBatch.publication_id, publication_id),
    ).update({"$set": {"status": ExamPublicationStatus.PUBLISHED.value}})

    await _history(
        tenant_id,
        publication_id=doc.publication_id,
        exam_session_id=doc.exam_session_id,
        action=ExamPublicationHistoryAction.PUBLISHED,
        actor_id=actor.id,
        metadata={"version": doc.version},
    )
    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_results_published",
        summary=f"Published results v{doc.version}",
        exam_session_id=doc.exam_session_id,
        metadata={"publication_id": doc.publication_id},
    )
    from app.modules.examinations.exam_cell_models import ExamSession
    from app.modules.examinations.exam_cell_notification_triggers import notify_result_published
    from app.modules.examinations.exam_cell_publication_models import ExamStudentResultVisibility

    session = await ExamSession.get(doc.exam_session_id)
    session_name = session.name if session else doc.publication_id
    vis_rows = await ExamStudentResultVisibility.find(
        Eq(ExamStudentResultVisibility.tenant_id, tenant_id),
        Eq(ExamStudentResultVisibility.publication_id, publication_id),
    ).to_list()
    for vis in vis_rows:
        if vis.visible and not vis.withheld:
            await notify_result_published(
                tenant_id,
                student_user_id=vis.student_user_id,
                exam_session_id=doc.exam_session_id,
                session_name=session_name,
                publication_id=publication_id,
            )
    return ExamPublicationRead.from_doc(doc)


async def execute_scheduled_publications(scope: AccessScope, actor: User) -> list[ExamPublicationRead]:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_publication_publish(scope)
    now = utcnow()
    rows = await ExamResultPublication.find(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.status, ExamPublicationStatus.SCHEDULED),
    ).to_list()
    published: list[ExamPublicationRead] = []
    for row in rows:
        if row.publish_at and as_utc_aware(row.publish_at) <= now:
            row.status = ExamPublicationStatus.PENDING_APPROVAL
            await row.save()
            published.append(await publish_results(scope, actor, row.publication_id))
    return published


async def withhold_student_result(
    scope: AccessScope,
    actor: User,
    publication_id: str,
    payload: ExamPublicationWithholdRequest,
) -> None:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_publication_manage(scope)
    student_oid = to_object_id(payload.student_user_id, "student_user_id")

    vis = await ExamStudentResultVisibility.find_one(
        Eq(ExamStudentResultVisibility.tenant_id, tenant_id),
        Eq(ExamStudentResultVisibility.publication_id, publication_id),
        Eq(ExamStudentResultVisibility.student_user_id, student_oid),
    )
    if vis is None:
        raise AppError(code="NOT_FOUND", message="Visibility record not found", status_code=404)

    vis.withheld = payload.withhold
    vis.visible = False if payload.withhold else True
    vis.updated_at = utcnow()
    await vis.save()

    pub = await ExamResultPublication.find_one(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.publication_id, publication_id),
    )
    if pub:
        pub.withheld_count = await ExamStudentResultVisibility.find(
            Eq(ExamStudentResultVisibility.tenant_id, tenant_id),
            Eq(ExamStudentResultVisibility.publication_id, publication_id),
            Eq(ExamStudentResultVisibility.withheld, True),
        ).count()
        pub.updated_at = utcnow()
        await pub.save()
        await _history(
            tenant_id,
            publication_id=publication_id,
            exam_session_id=pub.exam_session_id,
            action=ExamPublicationHistoryAction.WITHHELD if payload.withhold else ExamPublicationHistoryAction.RELEASED,
            actor_id=actor.id,
            note=payload.note,
            metadata={"student_user_id": str(student_oid)},
        )


async def release_withheld_result(
    scope: AccessScope,
    actor: User,
    publication_id: str,
    payload: ExamPublicationReleaseRequest,
) -> None:
    await withhold_student_result(
        scope,
        actor,
        publication_id,
        ExamPublicationWithholdRequest(student_user_id=payload.student_user_id, withhold=False, note=payload.note),
    )
    tenant_id = require_examination_cell_tenant(scope)
    student_oid = to_object_id(payload.student_user_id, "student_user_id")
    vis = await ExamStudentResultVisibility.find_one(
        Eq(ExamStudentResultVisibility.tenant_id, tenant_id),
        Eq(ExamStudentResultVisibility.publication_id, publication_id),
        Eq(ExamStudentResultVisibility.student_user_id, student_oid),
    )
    if vis:
        vis.released_at = utcnow()
        await vis.save()


async def revise_publication(scope: AccessScope, actor: User, publication_id: str, payload: ExamPublicationReviseRequest) -> ExamPublicationRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_publication_publish(scope)

    doc = await ExamResultPublication.find_one(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.publication_id, publication_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Publication not found", status_code=404)
    if doc.status != ExamPublicationStatus.PUBLISHED:
        raise AppError(code="INVALID_STATE", message="Only published results can be revised", status_code=409)

    new_doc = ExamResultPublication(
        tenant_id=tenant_id,
        publication_id=_publication_id(),
        exam_session_id=doc.exam_session_id,
        workflow_id=doc.workflow_id,
        scope_type=doc.scope_type,
        programme_code=doc.programme_code,
        semester_label=doc.semester_label,
        student_group_label=doc.student_group_label,
        status=ExamPublicationStatus.REVISED,
        version=doc.version + 1,
        policy_id=doc.policy_id,
        policy_version=doc.policy_version,
        visibility_default=doc.visibility_default,
        pending_count=doc.pending_count,
        withheld_count=doc.withheld_count,
        unresolved_count=doc.unresolved_count,
        students_included=doc.students_included,
        dataset_snapshot=dict(doc.dataset_snapshot),
        created_by=actor.id,
    )
    await new_doc.insert()
    doc.status = ExamPublicationStatus.REVISED
    doc.updated_at = utcnow()
    await doc.save()

    await _history(
        tenant_id,
        publication_id=new_doc.publication_id,
        exam_session_id=new_doc.exam_session_id,
        action=ExamPublicationHistoryAction.REVISED,
        actor_id=actor.id,
        note=payload.note,
        metadata={"supersedes": publication_id, "version": new_doc.version},
    )
    return ExamPublicationRead.from_doc(new_doc)


async def publication_history(scope: AccessScope, publication_id: str) -> list[ExamPublicationHistoryRead]:
    tenant_id = require_examination_cell_tenant(scope)
    rows = await ExamPublicationHistory.find(
        Eq(ExamPublicationHistory.tenant_id, tenant_id),
        Eq(ExamPublicationHistory.publication_id, publication_id),
    ).sort("-created_at").to_list()
    return [ExamPublicationHistoryRead.from_doc(r) for r in rows]


def _student_may_view_publication(
    pub: ExamResultPublication,
    vis: ExamStudentResultVisibility | None,
) -> bool:
    if pub.status != ExamPublicationStatus.PUBLISHED:
        return False
    if pub.publish_at and as_utc_aware(pub.publish_at) > utcnow():
        return False
    if vis is None:
        return pub.visibility_default
    if vis.withheld or not vis.visible:
        return False
    return True


def _require_tenant(scope: AccessScope) -> PydanticObjectId:
    if scope.tenant_id is None:
        raise AppError(code="TENANT_REQUIRED", message="College context is required", status_code=403)
    return scope.tenant_id


async def list_student_published_results(scope: AccessScope, student_user_id: str) -> list[ExamStudentPublishedResultRead]:
    from app.authorization.permissions import Permission

    tenant_id = _require_tenant(scope)
    student_oid = to_object_id(student_user_id, "student_user_id")
    is_staff = (
        Permission.EXAMINATION_CELL_PUBLICATION_READ in scope.effective_permissions
        or Permission.EXAMINATION_ADMIN_READ in scope.effective_permissions
    )
    if scope.user_id != student_oid and not is_staff:
        raise AppError(code="FORBIDDEN", message="Cannot view another student's results", status_code=403)

    publications = await ExamResultPublication.find(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.status, ExamPublicationStatus.PUBLISHED),
    ).to_list()

    reads: list[ExamStudentPublishedResultRead] = []
    for pub in publications:
        if pub.publish_at and as_utc_aware(pub.publish_at) > utcnow():
            continue
        student_ids = pub.dataset_snapshot.get("student_user_ids") or []
        if student_ids and str(student_oid) not in student_ids:
            continue
        vis = await ExamStudentResultVisibility.find_one(
            Eq(ExamStudentResultVisibility.tenant_id, tenant_id),
            Eq(ExamStudentResultVisibility.publication_id, pub.publication_id),
            Eq(ExamStudentResultVisibility.student_user_id, student_oid),
        )
        if not _student_may_view_publication(pub, vis):
            continue

        subjects = await ExamStudentSubjectResult.find(
            Eq(ExamStudentSubjectResult.tenant_id, tenant_id),
            Eq(ExamStudentSubjectResult.exam_session_id, pub.exam_session_id),
            Eq(ExamStudentSubjectResult.student_user_id, student_oid),
            Eq(ExamStudentSubjectResult.status, ExamSubjectResultStatus.APPROVED),
        ).to_list()
        sem = await ExamSemesterResult.find_one(
            Eq(ExamSemesterResult.tenant_id, tenant_id),
            Eq(ExamSemesterResult.exam_session_id, pub.exam_session_id),
            Eq(ExamSemesterResult.student_user_id, student_oid),
        )
        for sub in subjects:
            reads.append(
                ExamStudentPublishedResultRead(
                    course_code=sub.course_code,
                    grade_letter=sub.grade_letter,
                    grade_point=sub.grade_point,
                    credits_earned=sub.credits_earned,
                    gpa=sem.gpa if sem else None,
                    cgpa=sem.cgpa if sem else None,
                    publication_id=pub.publication_id,
                    published_at=pub.published_at,
                )
            )
    return reads