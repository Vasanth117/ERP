"""Record immutable library audit events (reuses institution audit chain)."""

from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId

from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.audit_enums import LibraryAuditDomain
from app.modules.library.audit_models import LibraryAuditEvent

_DOMAIN_MODULE: dict[LibraryAuditDomain, str] = {
    LibraryAuditDomain.ACTIVITY: "library_activity",
    LibraryAuditDomain.CATALOGUE: "library_catalogue",
    LibraryAuditDomain.INVENTORY: "library_inventory",
    LibraryAuditDomain.CIRCULATION: "library_circulation",
    LibraryAuditDomain.RESERVATION: "library_reservation",
    LibraryAuditDomain.FINE: "library_fines",
    LibraryAuditDomain.MEMBER: "library_members",
    LibraryAuditDomain.FACILITY: "library_facility",
    LibraryAuditDomain.SETTINGS: "library_settings",
    LibraryAuditDomain.ACQUISITION: "library_acquisition",
    LibraryAuditDomain.DIGITAL: "library_digital",
    LibraryAuditDomain.STAFF: "library_staff",
}


async def record_library_audit(
    tenant_id: PydanticObjectId,
    *,
    actor_id: PydanticObjectId | None,
    domain: LibraryAuditDomain,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    branch_code: str | None = None,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> LibraryAuditEvent:
    event_id = f"la_{uuid4().hex[:12]}"
    module = _DOMAIN_MODULE.get(domain, "library_activity")
    await append_institution_audit(
        tenant_id,
        actor_id=actor_id,
        action=action,
        module=module,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata={
            **(metadata or {}),
            "library_event_id": event_id,
            "branch_code": branch_code,
        },
    )
    doc = LibraryAuditEvent(
        tenant_id=tenant_id,
        event_id=event_id,
        domain=domain,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        branch_code=branch_code.strip().upper() if branch_code else None,
        actor_id=actor_id,
        before_state=dict(before_state or {}),
        after_state=dict(after_state or {}),
        metadata=dict(metadata or {}),
    )
    await doc.insert()
    return doc