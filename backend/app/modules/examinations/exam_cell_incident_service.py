"""Examination incidents and malpractice compliance services."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.examinations.exam_cell_audit import record_exam_activity
from app.modules.examinations.exam_cell_incident_models import (
    ExamDisciplinaryDecision,
    ExamIncidentEvidence,
    ExamIncidentHistory,
    ExamIncidentRecord,
    ExamInvestigationRecord,
    ExamMalpracticeCase,
)
from app.modules.examinations.exam_cell_incident_schemas import (
    ExamDisciplinaryDecisionCreate,
    ExamIncidentAssignInvestigator,
    ExamIncidentCreate,
    ExamIncidentEvidenceCreate,
    ExamIncidentRead,
    ExamInvestigationStatement,
    ExamMalpracticeCaseCreate,
    ExamMalpracticeCaseRead,
    ExamMalpracticeFinding,
)
from app.modules.examinations.exam_cell_policy import (
    authorize_examination_cell_incident_investigate,
    authorize_examination_cell_incident_manage,
    require_examination_cell_tenant,
)
from app.modules.examinations.exam_cell_publication_schemas import ExamPublicationWithholdRequest
from app.modules.examinations.exam_cell_publication_service import withhold_student_result
from app.modules.examinations.exam_cell_revaluation_enums import (
    ExamDisciplinaryActionType,
    ExamIncidentHistoryAction,
    ExamIncidentStatus,
    ExamIncidentType,
    ExamMalpracticeCaseStatus,
)


def _incident_id() -> str:
    return f"einc_{uuid4().hex[:10]}"


def _case_id() -> str:
    return f"emc_{uuid4().hex[:10]}"


def _evidence_id() -> str:
    return f"eev_{uuid4().hex[:10]}"


def _investigation_id() -> str:
    return f"einv_{uuid4().hex[:10]}"


def _decision_id() -> str:
    return f"edc_{uuid4().hex[:10]}"


def _incident_history_id() -> str:
    return f"eih_{uuid4().hex[:10]}"


async def _incident_history(
    tenant_id: PydanticObjectId,
    *,
    incident_id: str,
    action: ExamIncidentHistoryAction,
    actor_id: PydanticObjectId | None,
    case_id: str | None = None,
    note: str | None = None,
) -> None:
    await ExamIncidentHistory(
        tenant_id=tenant_id,
        history_id=_incident_history_id(),
        incident_id=incident_id,
        case_id=case_id,
        action=action,
        actor_id=actor_id,
        note=note,
        restricted=True,
    ).insert()


def _can_view_restricted(scope: AccessScope) -> None:
    allowed = {
        Permission.EXAMINATION_CELL_INCIDENT_INVESTIGATE,
        Permission.EXAMINATION_CELL_INCIDENT_MANAGE,
        Permission.EXAMINATION_ADMIN_CONFIG,
    }
    if not (scope.effective_permissions & allowed):
        authorize_examination_cell_incident_investigate(scope)


async def register_incident(scope: AccessScope, actor: User, payload: ExamIncidentCreate) -> ExamIncidentRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_incident_manage(scope)

    session_oid = to_object_id(payload.exam_session_id, "exam_session_id") if payload.exam_session_id else None
    student_ids = [to_object_id(x, "student_user_id") for x in payload.student_user_ids]
    staff_ids = [to_object_id(x, "staff_user_id") for x in payload.staff_user_ids]

    doc = ExamIncidentRecord(
        tenant_id=tenant_id,
        incident_id=_incident_id(),
        exam_session_id=session_oid,
        incident_type=payload.incident_type,
        location_label=payload.location_label,
        occurred_at=payload.occurred_at,
        description=payload.description,
        student_user_ids=student_ids,
        staff_user_ids=staff_ids,
        reported_by=actor.id,
    )
    await doc.insert()
    await _incident_history(tenant_id, incident_id=doc.incident_id, action=ExamIncidentHistoryAction.REPORTED, actor_id=actor.id)
    await record_exam_activity(
        tenant_id,
        actor_id=actor.id,
        action="exam_incident_reported",
        summary=f"Incident {doc.incident_id} recorded",
        exam_session_id=session_oid,
    )
    return ExamIncidentRead.from_doc(doc)


async def open_malpractice_case(scope: AccessScope, actor: User, payload: ExamMalpracticeCaseCreate) -> ExamMalpracticeCaseRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_incident_manage(scope)

    incident = await ExamIncidentRecord.find_one(
        Eq(ExamIncidentRecord.tenant_id, tenant_id),
        Eq(ExamIncidentRecord.incident_id, payload.incident_id),
    )
    if incident is None:
        raise AppError(code="NOT_FOUND", message="Incident not found", status_code=404)

    student_oid = to_object_id(payload.student_user_id, "student_user_id")
    doc = ExamMalpracticeCase(
        tenant_id=tenant_id,
        case_id=_case_id(),
        incident_id=payload.incident_id,
        exam_session_id=incident.exam_session_id,
        student_user_id=student_oid,
        course_code=payload.course_code.strip().upper() if payload.course_code else None,
        allegation_summary=payload.allegation_summary,
        status=ExamMalpracticeCaseStatus.ALLEGED,
    )
    await doc.insert()
    incident.status = ExamIncidentStatus.UNDER_INVESTIGATION
    incident.incident_type = ExamIncidentType.MALPRACTICE_ALLEGATION
    incident.updated_at = utcnow()
    await incident.save()
    await _incident_history(
        tenant_id,
        incident_id=incident.incident_id,
        case_id=doc.case_id,
        action=ExamIncidentHistoryAction.REPORTED,
        actor_id=actor.id,
        note="Malpractice case opened",
    )
    return ExamMalpracticeCaseRead.from_doc(doc)


async def assign_investigator(
    scope: AccessScope,
    actor: User,
    case_id: str,
    payload: ExamIncidentAssignInvestigator,
) -> ExamMalpracticeCaseRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_incident_investigate(scope)

    doc = await ExamMalpracticeCase.find_one(
        Eq(ExamMalpracticeCase.tenant_id, tenant_id),
        Eq(ExamMalpracticeCase.case_id, case_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Case not found", status_code=404)

    investigator = to_object_id(payload.investigator_user_id, "investigator_user_id")
    doc.investigator_user_id = investigator
    doc.status = ExamMalpracticeCaseStatus.INVESTIGATING
    doc.updated_at = utcnow()
    await doc.save()
    await _incident_history(
        tenant_id,
        incident_id=doc.incident_id,
        case_id=case_id,
        action=ExamIncidentHistoryAction.INVESTIGATOR_ASSIGNED,
        actor_id=actor.id,
    )
    from app.modules.examinations.exam_cell_notification_triggers import notify_incident_workflow

    await notify_incident_workflow(
        tenant_id,
        recipient_user_id=investigator,
        case_id=case_id,
        summary="You were assigned as investigation officer",
        exam_session_id=doc.exam_session_id,
    )
    return ExamMalpracticeCaseRead.from_doc(doc)


async def record_investigation_statement(
    scope: AccessScope,
    actor: User,
    case_id: str,
    payload: ExamInvestigationStatement,
) -> None:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_incident_investigate(scope)

    case = await ExamMalpracticeCase.find_one(
        Eq(ExamMalpracticeCase.tenant_id, tenant_id),
        Eq(ExamMalpracticeCase.case_id, case_id),
    )
    if case is None:
        raise AppError(code="NOT_FOUND", message="Case not found", status_code=404)
    if case.investigator_user_id and actor.id != case.investigator_user_id:
        if Permission.EXAMINATION_CELL_INCIDENT_MANAGE not in scope.effective_permissions:
            raise AppError(code="FORBIDDEN", message="Not assigned investigator", status_code=403)

    await ExamInvestigationRecord(
        tenant_id=tenant_id,
        investigation_id=_investigation_id(),
        case_id=case_id,
        investigator_user_id=actor.id,
        statement=payload.statement,
    ).insert()
    await _incident_history(
        tenant_id,
        incident_id=case.incident_id,
        case_id=case_id,
        action=ExamIncidentHistoryAction.STATEMENT_RECORDED,
        actor_id=actor.id,
    )


async def record_malpractice_finding(
    scope: AccessScope,
    actor: User,
    case_id: str,
    payload: ExamMalpracticeFinding,
) -> ExamMalpracticeCaseRead:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_incident_investigate(scope)

    doc = await ExamMalpracticeCase.find_one(
        Eq(ExamMalpracticeCase.tenant_id, tenant_id),
        Eq(ExamMalpracticeCase.case_id, case_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Case not found", status_code=404)

    doc.finding_summary = payload.finding_summary
    doc.committee_recommendation = payload.committee_recommendation
    doc.proven = payload.proven
    if payload.proven is True:
        doc.status = ExamMalpracticeCaseStatus.PROVEN
    elif payload.proven is False:
        doc.status = ExamMalpracticeCaseStatus.NOT_PROVEN
    else:
        doc.status = ExamMalpracticeCaseStatus.COMMITTEE_REVIEW
    doc.updated_at = utcnow()
    await doc.save()

    incident = await ExamIncidentRecord.find_one(
        Eq(ExamIncidentRecord.tenant_id, tenant_id),
        Eq(ExamIncidentRecord.incident_id, doc.incident_id),
    )
    if incident:
        incident.status = ExamIncidentStatus.COMMITTEE_REVIEW
        incident.updated_at = utcnow()
        await incident.save()

    await _incident_history(
        tenant_id,
        incident_id=doc.incident_id,
        case_id=case_id,
        action=ExamIncidentHistoryAction.FINDING_RECORDED,
        actor_id=actor.id,
        note=str(payload.proven),
    )
    return ExamMalpracticeCaseRead.from_doc(doc)


async def record_disciplinary_decision(
    scope: AccessScope,
    actor: User,
    case_id: str,
    payload: ExamDisciplinaryDecisionCreate,
) -> None:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_incident_manage(scope)

    case = await ExamMalpracticeCase.find_one(
        Eq(ExamMalpracticeCase.tenant_id, tenant_id),
        Eq(ExamMalpracticeCase.case_id, case_id),
    )
    if case is None:
        raise AppError(code="NOT_FOUND", message="Case not found", status_code=404)
    if case.status not in {ExamMalpracticeCaseStatus.PROVEN, ExamMalpracticeCaseStatus.COMMITTEE_REVIEW, ExamMalpracticeCaseStatus.NOT_PROVEN}:
        raise AppError(code="INVALID_STATE", message="Case not ready for disciplinary decision", status_code=409)

    await ExamDisciplinaryDecision(
        tenant_id=tenant_id,
        decision_id=_decision_id(),
        case_id=case_id,
        action_type=payload.action_type,
        authorized_by=actor.id,
        details=payload.details,
        result_withheld=payload.result_withheld,
    ).insert()

    case.updated_at = utcnow()
    if payload.result_withheld:
        case.status = ExamMalpracticeCaseStatus.WITHHELD
        pub = await withhold_for_case(tenant_id, case, actor, scope)
        _ = pub
    else:
        case.status = ExamMalpracticeCaseStatus.CLOSED
    await case.save()

    incident = await ExamIncidentRecord.find_one(
        Eq(ExamIncidentRecord.tenant_id, tenant_id),
        Eq(ExamIncidentRecord.incident_id, case.incident_id),
    )
    if incident:
        incident.status = ExamIncidentStatus.DECISION_RECORDED
        incident.updated_at = utcnow()
        await incident.save()

    await _incident_history(
        tenant_id,
        incident_id=case.incident_id,
        case_id=case_id,
        action=ExamIncidentHistoryAction.DECISION_RECORDED,
        actor_id=actor.id,
        note=payload.action_type.value,
    )
    if payload.result_withheld:
        await _incident_history(
            tenant_id,
            incident_id=case.incident_id,
            case_id=case_id,
            action=ExamIncidentHistoryAction.WITHHOLDING_APPLIED,
            actor_id=actor.id,
        )


async def withhold_for_case(
    tenant_id: PydanticObjectId,
    case: ExamMalpracticeCase,
    actor: User,
    scope: AccessScope,
) -> str | None:
    from app.modules.examinations.exam_cell_publication_models import ExamResultPublication
    from app.modules.examinations.exam_cell_publication_enums import ExamPublicationStatus

    if case.exam_session_id is None:
        return None
    publication = await ExamResultPublication.find_one(
        Eq(ExamResultPublication.tenant_id, tenant_id),
        Eq(ExamResultPublication.exam_session_id, case.exam_session_id),
        Eq(ExamResultPublication.status, ExamPublicationStatus.PUBLISHED),
    )
    if publication is None:
        return None
    await withhold_student_result(
        scope,
        actor,
        publication.publication_id,
        ExamPublicationWithholdRequest(student_user_id=str(case.student_user_id), withhold=True, note="Malpractice disciplinary withholding"),
    )
    return publication.publication_id


async def add_incident_evidence(
    scope: AccessScope,
    actor: User,
    incident_id: str,
    payload: ExamIncidentEvidenceCreate,
) -> None:
    tenant_id = require_examination_cell_tenant(scope)
    authorize_examination_cell_incident_investigate(scope)

    incident = await ExamIncidentRecord.find_one(
        Eq(ExamIncidentRecord.tenant_id, tenant_id),
        Eq(ExamIncidentRecord.incident_id, incident_id),
    )
    if incident is None:
        raise AppError(code="NOT_FOUND", message="Incident not found", status_code=404)

    await ExamIncidentEvidence(
        tenant_id=tenant_id,
        evidence_id=_evidence_id(),
        incident_id=incident_id,
        reference_label=payload.reference_label,
        storage_key=payload.storage_key,
        description=payload.description,
        uploaded_by=actor.id,
    ).insert()
    await _incident_history(
        tenant_id,
        incident_id=incident_id,
        action=ExamIncidentHistoryAction.EVIDENCE_ADDED,
        actor_id=actor.id,
    )


async def get_malpractice_case(scope: AccessScope, case_id: str) -> ExamMalpracticeCaseRead:
    tenant_id = require_examination_cell_tenant(scope)
    try:
        _can_view_restricted(scope)
    except AppError as exc:
        if exc.code == "FORBIDDEN":
            from app.common.context import get_request_id
            from app.modules.examinations.exam_cell_security_enums import ExamSecurityEventType
            from app.modules.examinations.exam_cell_security_recorder import record_exam_security_event

            await record_exam_security_event(
                tenant_id,
                event_type=ExamSecurityEventType.UNAUTHORIZED_ACCESS,
                actor_id=scope.user_id,
                resource_type="exam_malpractice_case",
                resource_id=case_id,
                detail="Restricted malpractice case access denied",
                request_id=get_request_id(),
            )
        raise
    doc = await ExamMalpracticeCase.find_one(
        Eq(ExamMalpracticeCase.tenant_id, tenant_id),
        Eq(ExamMalpracticeCase.case_id, case_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Case not found", status_code=404)
    return ExamMalpracticeCaseRead.from_doc(doc)