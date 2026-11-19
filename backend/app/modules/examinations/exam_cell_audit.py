"""Examination cell activity and institution audit integration."""

from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId

from app.common.context import get_request_id
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.examinations.exam_cell_models import ExamActivityLog
from app.modules.examinations.exam_cell_redaction import redact_mapping
from app.modules.examinations.exam_cell_security_models import ExamAuditLog


async def record_exam_audit(
    tenant_id: PydanticObjectId,
    *,
    actor_id: PydanticObjectId | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    exam_session_id: PydanticObjectId | None = None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    reason: str | None = None,
    approval_reference: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ExamAuditLog:
    audit_id = f"aud_{uuid4().hex[:12]}"
    request_id = get_request_id()
    doc = ExamAuditLog(
        tenant_id=tenant_id,
        audit_id=audit_id,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        exam_session_id=exam_session_id,
        before_state=redact_mapping(before_state),
        after_state=redact_mapping(after_state),
        reason=reason,
        approval_reference=approval_reference,
        request_id=request_id,
        correlation_id=request_id,
        metadata=redact_mapping(metadata),
    )
    await doc.insert()
    await append_institution_audit(
        tenant_id,
        actor_id=actor_id,
        action=action,
        module="examination_cell",
        resource_type=resource_type,
        resource_id=resource_id,
        metadata={"exam_audit_id": audit_id, **redact_mapping(metadata)},
        source_audit_id=audit_id,
    )
    return doc


async def record_exam_activity(
    tenant_id: PydanticObjectId,
    *,
    actor_id: PydanticObjectId | None,
    action: str,
    summary: str,
    exam_session_id: PydanticObjectId | None = None,
    season_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    resource_type: str = "exam_session",
    resource_id: str | None = None,
) -> ExamActivityLog:
    event_id = f"ex_{uuid4().hex[:12]}"
    await record_exam_audit(
        tenant_id,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id or (str(exam_session_id) if exam_session_id else None),
        exam_session_id=exam_session_id,
        before_state=before_state,
        after_state=after_state,
        metadata={"summary": summary, "exam_event_id": event_id, **(metadata or {})},
    )
    doc = ExamActivityLog(
        tenant_id=tenant_id,
        event_id=event_id,
        exam_session_id=exam_session_id,
        season_id=season_id,
        action=action,
        summary=summary,
        actor_id=actor_id,
        metadata=dict(metadata or {}),
    )
    await doc.insert()
    return doc