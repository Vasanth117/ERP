"""Hostel rules and incident services."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.authorization.permissions import Permission
from app.core.exceptions import AppError
from app.modules.auth.models import User
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.hostel.hostel_notify import notify_hostel_student
from app.modules.hostel.policy import (
    authorize_hostel_incident_investigate,
    authorize_hostel_incident_manage,
    authorize_hostel_incident_read,
    authorize_hostel_rules_manage,
    authorize_hostel_rules_read,
    require_hostel_tenant_scope,
)
from app.modules.hostel.rules_incident_models import (
    HostelIncident,
    HostelIncidentAction,
    HostelIncidentEvidence,
    HostelIncidentHistory,
    HostelIncidentInvestigation,
    HostelIncidentParticipant,
    HostelIncidentSeverity,
    HostelIncidentStatus,
    HostelRule,
    HostelRuleAcknowledgement,
    HostelRuleApprovalStatus,
    HostelRuleVersion,
)
from app.modules.hostel.rules_incident_schemas import (
    DisciplinaryActionInput,
    HostelRuleRead,
    HostelRuleUpsertPortal,
    IncidentEvidenceInput,
    IncidentInvestigationUpdate,
    IncidentOverview,
    IncidentRead,
    IncidentReportInput,
    IncidentStatusUpdate,
    RuleAcknowledgeInput,
    RulePublishInput,
)


async def _incident_history(tenant_id: PydanticObjectId, incident_id: str, action: str, actor_id: PydanticObjectId | None, detail: dict | None = None) -> None:
    await HostelIncidentHistory(
        tenant_id=tenant_id,
        incident_id=incident_id,
        action=action,
        detail=detail or {},
        actor_id=actor_id,
    ).insert()


def _rule_read(doc: HostelRule) -> HostelRuleRead:
    return HostelRuleRead(
        rule_code=doc.rule_code,
        title=doc.title,
        body=doc.body,
        category=doc.category,
        version=doc.version,
        published=doc.published,
        approval_status=doc.approval_status,
        effective_from=doc.effective_from,
        updated_at=doc.updated_at,
    )


def _incident_read(doc: HostelIncident) -> IncidentRead:
    return IncidentRead(
        incident_id=doc.incident_id,
        category=doc.category,
        description=doc.description,
        severity=doc.severity,
        status=doc.status,
        building_code=doc.building_code,
        confidential=doc.confidential,
        allegation_only=doc.allegation_only,
        created_at=doc.created_at,
    )


async def upsert_rule(scope: AccessScope, payload: HostelRuleUpsertPortal) -> HostelRuleRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_rules_manage(scope)
    code = payload.rule_code.strip().upper()
    doc = await HostelRule.find_one(Eq(HostelRule.tenant_id, tenant_id), Eq(HostelRule.rule_code, code))
    if doc:
        doc.title = payload.title
        doc.body = payload.body
        doc.category = payload.category
        doc.hostel_codes = [h.upper() for h in payload.hostel_codes]
        doc.resident_categories = payload.resident_categories
        doc.effective_from = payload.effective_from
        doc.effective_to = payload.effective_to
        doc.severity = payload.severity
        doc.requires_acknowledgement = payload.requires_acknowledgement
        doc.consequence_policy = payload.consequence_policy
        doc.version += 1
        doc.approval_status = HostelRuleApprovalStatus.PENDING_REVIEW
        doc.published = False
        doc.updated_at = utcnow()
        await doc.save()
    else:
        doc = await HostelRule(
            tenant_id=tenant_id,
            rule_code=code,
            title=payload.title,
            body=payload.body,
            category=payload.category,
            hostel_codes=[h.upper() for h in payload.hostel_codes],
            resident_categories=payload.resident_categories,
            effective_from=payload.effective_from,
            effective_to=payload.effective_to,
            severity=payload.severity,
            requires_acknowledgement=payload.requires_acknowledgement,
            consequence_policy=payload.consequence_policy,
            approval_status=HostelRuleApprovalStatus.PENDING_REVIEW,
        ).insert()
    return _rule_read(doc)


async def publish_rule(scope: AccessScope, payload: RulePublishInput) -> HostelRuleRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_rules_manage(scope)
    doc = await HostelRule.find_one(Eq(HostelRule.tenant_id, tenant_id), Eq(HostelRule.rule_code, payload.rule_code.upper()))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Rule not found", status_code=404)
    if not payload.approve:
        doc.approval_status = HostelRuleApprovalStatus.REJECTED
        await doc.save()
        return _rule_read(doc)
    today = date.today()
    if doc.effective_from and doc.effective_from > today:
        raise AppError(code="VALIDATION_ERROR", message="Cannot publish before effective date", status_code=422)
    doc.approval_status = HostelRuleApprovalStatus.APPROVED
    doc.published = True
    doc.published_at = utcnow()
    doc.updated_at = utcnow()
    await doc.save()
    await HostelRuleVersion(
        tenant_id=tenant_id,
        version_id=f"rv_{uuid4().hex[:10]}",
        rule_code=doc.rule_code,
        version=doc.version,
        title=doc.title,
        body=doc.body,
        snapshot=doc.model_dump(mode="json"),
        published_at=doc.published_at,
        actor_id=scope.user_id,
    ).insert()
    return _rule_read(doc)


async def list_published_rules_for_resident(scope: AccessScope, user: User) -> list[HostelRuleRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    if user.tenant_id != tenant_id:
        raise AppError(code="FORBIDDEN", message="Tenant mismatch", status_code=403)
    rows = await HostelRule.find({"tenant_id": tenant_id, "published": True}).to_list()
    today = date.today()
    rows = [r for r in rows if (not r.effective_from or r.effective_from <= today) and (not r.effective_to or r.effective_to >= today)]
    return [_rule_read(r) for r in rows]


async def list_published_rules(scope: AccessScope, *, hostel_code: str | None = None) -> list[HostelRuleRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_rules_read(scope)
    rows = await HostelRule.find({"tenant_id": tenant_id, "published": True}).to_list()
    if hostel_code:
        hc = hostel_code.upper()
        rows = [r for r in rows if not r.hostel_codes or hc in r.hostel_codes]
    return [_rule_read(r) for r in rows]


async def acknowledge_rule(scope: AccessScope, user: User, payload: RuleAcknowledgeInput) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelRule.find_one(
        Eq(HostelRule.tenant_id, tenant_id), Eq(HostelRule.rule_code, payload.rule_code.upper()), Eq(HostelRule.published, True)
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Published rule not found", status_code=404)
    if not doc.requires_acknowledgement:
        raise AppError(code="VALIDATION_ERROR", message="Rule does not require acknowledgement", status_code=422)
    existing = await HostelRuleAcknowledgement.find_one(
        {
            "tenant_id": tenant_id,
            "rule_code": doc.rule_code,
            "student_user_id": user.id,
            "rule_version": doc.version,
        }
    )
    if existing:
        return {"rule_code": doc.rule_code, "already_acknowledged": True}
    await HostelRuleAcknowledgement(
        tenant_id=tenant_id,
        ack_id=f"ack_{uuid4().hex[:10]}",
        rule_code=doc.rule_code,
        rule_version=doc.version,
        student_user_id=user.id,
    ).insert()
    return {"rule_code": doc.rule_code, "acknowledged": True}


async def report_incident(scope: AccessScope, payload: IncidentReportInput) -> IncidentRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_incident_manage(scope)
    incident_id = f"inc_{uuid4().hex[:10]}"
    doc = await HostelIncident(
        tenant_id=tenant_id,
        incident_id=incident_id,
        category=payload.category,
        hostel_code=payload.hostel_code.upper() if payload.hostel_code else None,
        building_code=payload.building_code.upper() if payload.building_code else None,
        block_code=payload.block_code.upper() if payload.block_code else None,
        room_code=payload.room_code.upper() if payload.room_code else None,
        incident_at=payload.incident_at or utcnow(),
        description=payload.description,
        severity=payload.severity,
        status=HostelIncidentStatus.REPORTED,
        reporter_id=scope.user_id,
        actor_id=scope.user_id,
        immediate_action=payload.immediate_action,
        confidential=payload.confidential,
        allegation_only=True,
    ).insert()
    for uid in payload.participant_user_ids:
        await HostelIncidentParticipant(
            tenant_id=tenant_id,
            participant_id=f"ipp_{uuid4().hex[:10]}",
            incident_id=incident_id,
            student_user_id=to_object_id(uid, "participant_user_id"),
            role="involved",
        ).insert()
    await _incident_history(tenant_id, incident_id, "reported", scope.user_id)
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="hostel.incident.reported",
        module="hostel_incident",
        resource_type="incident",
        resource_id=incident_id,
    )
    return _incident_read(doc)


async def get_incident(scope: AccessScope, incident_id: str, *, include_confidential: bool = False) -> IncidentRead:
    tenant_id = require_hostel_tenant_scope(scope)
    doc = await HostelIncident.find_one(Eq(HostelIncident.tenant_id, tenant_id), Eq(HostelIncident.incident_id, incident_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Incident not found", status_code=404)
    if doc.confidential or include_confidential:
        authorize_hostel_incident_investigate(scope)
    else:
        authorize_hostel_incident_read(scope)
    return _incident_read(doc)


async def update_incident_status(scope: AccessScope, payload: IncidentStatusUpdate) -> IncidentRead:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_incident_manage(scope)
    doc = await HostelIncident.find_one(
        Eq(HostelIncident.tenant_id, tenant_id), Eq(HostelIncident.incident_id, payload.incident_id)
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Incident not found", status_code=404)
    prev = doc.status
    doc.status = payload.status
    if payload.status == HostelIncidentStatus.RESOLVED:
        doc.allegation_only = True
    doc.updated_at = utcnow()
    await doc.save()
    await _incident_history(
        tenant_id,
        doc.incident_id,
        "status_change",
        scope.user_id,
        {"from": prev.value, "to": doc.status.value, "note": payload.note},
    )
    return _incident_read(doc)


async def update_investigation(scope: AccessScope, payload: IncidentInvestigationUpdate) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_incident_investigate(scope)
    inv = await HostelIncidentInvestigation.find_one(
        Eq(HostelIncidentInvestigation.tenant_id, tenant_id), Eq(HostelIncidentInvestigation.incident_id, payload.incident_id)
    )
    if inv is None:
        inv = await HostelIncidentInvestigation(
            tenant_id=tenant_id,
            investigation_id=f"ivi_{uuid4().hex[:10]}",
            incident_id=payload.incident_id,
            investigator_id=scope.user_id,
        ).insert()
    if payload.notes:
        inv.notes = payload.notes
    if payload.finding_classification:
        inv.finding_classification = payload.finding_classification
    if payload.review_comments:
        inv.review_comments = payload.review_comments
    if payload.management_decision:
        inv.management_decision = payload.management_decision
    inc = await HostelIncident.find_one(Eq(HostelIncident.tenant_id, tenant_id), Eq(HostelIncident.incident_id, payload.incident_id))
    if inc and inc.status == HostelIncidentStatus.REPORTED:
        inc.status = HostelIncidentStatus.UNDER_INVESTIGATION
        inc.updated_at = utcnow()
        await inc.save()
    await _incident_history(tenant_id, payload.incident_id, "investigation_update", scope.user_id)
    return {"investigation_id": inv.investigation_id}


async def add_incident_evidence(scope: AccessScope, payload: IncidentEvidenceInput) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_incident_investigate(scope)
    evidence_id = f"iev_{uuid4().hex[:10]}"
    await HostelIncidentEvidence(
        tenant_id=tenant_id,
        evidence_id=evidence_id,
        incident_id=payload.incident_id,
        document_ref=payload.document_ref,
        description=payload.description,
        restricted=payload.restricted,
        uploaded_by=scope.user_id,
    ).insert()
    return {"evidence_id": evidence_id}


async def record_disciplinary_action(scope: AccessScope, payload: DisciplinaryActionInput) -> dict:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_incident_manage(scope)
    inc = await HostelIncident.find_one(
        Eq(HostelIncident.tenant_id, tenant_id), Eq(HostelIncident.incident_id, payload.incident_id)
    )
    if inc is None:
        raise AppError(code="NOT_FOUND", message="Incident not found", status_code=404)
    action_id = f"ida_{uuid4().hex[:10]}"
    await HostelIncidentAction(
        tenant_id=tenant_id,
        action_id=action_id,
        incident_id=payload.incident_id,
        student_user_id=to_object_id(payload.student_user_id, "student_user_id"),
        outcome=payload.outcome,
        description=payload.description,
        approved_by=scope.user_id,
        resident_response=payload.resident_response,
    ).insert()
    await notify_hostel_student(
        tenant_id,
        student_user_id=to_object_id(payload.student_user_id, "student_user_id"),
        event_type="incident.disciplinary",
        title="Hostel disciplinary notice",
        body="A hostel disciplinary outcome has been recorded for review.",
        aggregate_id=payload.incident_id,
    )
    return {"action_id": action_id}


async def list_incidents(
    scope: AccessScope,
    pagination: Pagination,
    *,
    status: HostelIncidentStatus | None = None,
) -> Page[IncidentRead]:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_incident_read(scope)
    q: dict = {"tenant_id": tenant_id, "confidential": False}
    if status:
        q["status"] = status.value
    if Permission.HOSTEL_INCIDENT_INVESTIGATE in scope.effective_permissions:
        q.pop("confidential", None)
    total = await HostelIncident.find(q).count()
    skip = (pagination.page - 1) * pagination.page_size
    rows = await HostelIncident.find(q).sort("-created_at").skip(skip).limit(pagination.page_size).to_list()
    return Page(items=[_incident_read(r) for r in rows], total=total, page=pagination.page, page_size=pagination.page_size)


async def incident_overview(scope: AccessScope) -> IncidentOverview:
    tenant_id = require_hostel_tenant_scope(scope)
    authorize_hostel_incident_read(scope)
    q_base = {"tenant_id": tenant_id}
    reported = await HostelIncident.find({**q_base, "status": HostelIncidentStatus.REPORTED.value}).count()
    investigating = await HostelIncident.find({**q_base, "status": HostelIncidentStatus.UNDER_INVESTIGATION.value}).count()
    awaiting = await HostelIncident.find(
        {**q_base, "status": {"$in": [HostelIncidentStatus.AWAITING_MGMT_REVIEW.value, HostelIncidentStatus.AWAITING_EVIDENCE.value]}}
    ).count()
    resolved = await HostelIncident.find(
        {**q_base, "status": {"$in": [HostelIncidentStatus.RESOLVED.value, HostelIncidentStatus.CLOSED.value]}}
    ).count()
    high = await HostelIncident.find(
        {
            **q_base,
            "severity": {"$in": [HostelIncidentSeverity.HIGH.value, HostelIncidentSeverity.CRITICAL.value]},
            "status": {"$nin": [HostelIncidentStatus.CLOSED.value, HostelIncidentStatus.DISMISSED.value]},
        }
    ).count()
    return IncidentOverview(
        reported=reported,
        under_investigation=investigating,
        awaiting_review=awaiting,
        resolved=resolved,
        high_severity_open=high,
    )