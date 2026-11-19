"""Low-level examination security event recorder."""

from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId

from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.examinations.exam_cell_redaction import redact_mapping
from app.modules.examinations.exam_cell_security_enums import ExamSecurityEventType
from app.modules.examinations.exam_cell_security_models import ExamSecurityEvent


async def record_exam_security_event(
    tenant_id: PydanticObjectId,
    *,
    event_type: ExamSecurityEventType,
    actor_id: PydanticObjectId | None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ExamSecurityEvent:
    event_id = f"esec_{uuid4().hex[:12]}"
    redacted_meta = redact_mapping(metadata or {})
    doc = ExamSecurityEvent(
        tenant_id=tenant_id,
        event_id=event_id,
        event_type=event_type.value,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail[:1000],
        request_id=request_id,
        metadata=redacted_meta,
    )
    await doc.insert()
    await append_institution_audit(
        tenant_id,
        actor_id=actor_id,
        action=f"exam.security.{event_type.value}",
        module="examination_cell",
        resource_type=resource_type or "security_event",
        resource_id=resource_id or event_id,
        outcome="denied" if event_type == ExamSecurityEventType.UNAUTHORIZED_ACCESS else "blocked",
        metadata={"exam_security_event_id": event_id, **redacted_meta},
    )
    return doc