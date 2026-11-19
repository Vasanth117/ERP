"""Library audit search, timelines and reporting."""

from datetime import datetime
from typing import Any

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq, In

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.modules.college_admin.library_admin_models import LibraryCirculationRecord, LibraryInventoryHistory
from app.modules.college_admin.security_admin_models import InstitutionAuditLog
from app.modules.library.acquisition_models import LibraryAcquisitionHistory
from app.modules.library.audit_access import require_audit_export, require_audit_read
from app.modules.library.audit_enums import LibraryAuditDomain, StockAdjustmentRequestStatus, StockDiscrepancyStatus
from app.modules.library.audit_models import LibraryAuditEvent, LibraryStockAdjustmentRequest, LibraryStockDiscrepancy
from app.modules.library.audit_schemas import (
    LibraryAuditEventRead,
    LibraryAuditReportRead,
    LibraryAuditSearch,
    LibraryAuditTimelineItem,
)
from app.modules.library.facility_models import LibraryConfigurationHistory
from app.modules.library.fine_models import LibraryFineHistory
from app.modules.library.library_models import LibraryCatalogHistory
from app.modules.library.member_models import LibraryMembershipHistory
from app.modules.library.reservation_models import LibraryReservationHistory
from app.modules.library.settings_models import LibraryPolicyHistory

_LIBRARY_MODULES = (
    "library_activity",
    "library_catalogue",
    "library_inventory",
    "library_circulation",
    "library_reservation",
    "library_fines",
    "library_members",
    "library_facility",
    "library_settings",
    "library_acquisition",
    "library_digital",
    "library_staff",
)


def _event_read(doc: LibraryAuditEvent) -> LibraryAuditEventRead:
    return LibraryAuditEventRead(
        event_id=doc.event_id,
        domain=doc.domain,
        action=doc.action,
        resource_type=doc.resource_type,
        resource_id=doc.resource_id,
        branch_code=doc.branch_code,
        actor_id=str(doc.actor_id) if doc.actor_id else None,
        before_state=dict(doc.before_state or {}),
        after_state=dict(doc.after_state or {}),
        metadata=dict(doc.metadata or {}),
        created_at=doc.created_at,
    )


async def search_audit_events(
    scope: AccessScope,
    pagination: Pagination,
    filters: LibraryAuditSearch,
) -> Page[LibraryAuditEventRead]:
    tenant_id = require_audit_read(scope)
    clauses: list[Any] = [Eq(LibraryAuditEvent.tenant_id, tenant_id)]
    if filters.domain is not None:
        clauses.append(Eq(LibraryAuditEvent.domain, filters.domain))
    if filters.branch_code:
        clauses.append(Eq(LibraryAuditEvent.branch_code, filters.branch_code.strip().upper()))
    if filters.resource_type:
        clauses.append(Eq(LibraryAuditEvent.resource_type, filters.resource_type.strip()))
    if filters.resource_id:
        clauses.append(Eq(LibraryAuditEvent.resource_id, filters.resource_id.strip()))
    if filters.actor_id:
        clauses.append(Eq(LibraryAuditEvent.actor_id, PydanticObjectId(filters.actor_id)))
    query = LibraryAuditEvent.find(*clauses)
    if filters.action_prefix:
        prefix = filters.action_prefix.strip()
        rows = await query.sort("-created_at").to_list()
        rows = [r for r in rows if r.action.startswith(prefix)]
        total = len(rows)
        page = rows[pagination.offset : pagination.offset + pagination.limit]
    else:
        total = await query.count()
        page = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(
        items=[_event_read(r) for r in page],
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


async def search_institution_library_audit(
    scope: AccessScope,
    pagination: Pagination,
    *,
    branch_code: str | None = None,
    module: str | None = None,
) -> Page[dict[str, Any]]:
    """Read-only view of institution audit rows for library modules."""
    tenant_id = require_audit_read(scope)
    clauses: list[Any] = [
        Eq(InstitutionAuditLog.tenant_id, tenant_id),
        In(InstitutionAuditLog.module, _LIBRARY_MODULES),
    ]
    if module and module in _LIBRARY_MODULES:
        clauses = [Eq(InstitutionAuditLog.tenant_id, tenant_id), Eq(InstitutionAuditLog.module, module)]
    query = InstitutionAuditLog.find(*clauses)
    rows = await query.sort("-created_at").to_list()
    if branch_code:
        bc = branch_code.strip().upper()
        rows = [r for r in rows if (r.metadata or {}).get("branch_code") == bc]
    total = len(rows)
    page = rows[pagination.offset : pagination.offset + pagination.limit]
    items = [
        {
            "action": r.action,
            "module": r.module,
            "resource_type": r.resource_type,
            "resource_id": r.resource_id,
            "actor_id": str(r.actor_id) if r.actor_id else None,
            "metadata": dict(r.metadata or {}),
            "created_at": r.created_at,
        }
        for r in page
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def resource_timeline(
    scope: AccessScope,
    resource_type: str,
    resource_id: str,
    pagination: Pagination,
) -> Page[LibraryAuditTimelineItem]:
    tenant_id = require_audit_read(scope)
    resource_id = resource_id.strip()
    resource_type = resource_type.strip().lower()
    combined: list[LibraryAuditTimelineItem] = []

    for row in await LibraryAuditEvent.find(
        Eq(LibraryAuditEvent.tenant_id, tenant_id),
        Eq(LibraryAuditEvent.resource_type, resource_type),
        Eq(LibraryAuditEvent.resource_id, resource_id),
    ).sort("-created_at").to_list():
        combined.append(
            LibraryAuditTimelineItem(
                source="library_audit_event",
                event_type=row.action,
                resource_id=row.resource_id,
                summary=row.action,
                actor_id=str(row.actor_id) if row.actor_id else None,
                branch_code=row.branch_code,
                before_state=dict(row.before_state or {}),
                after_state=dict(row.after_state or {}),
                metadata=dict(row.metadata or {}),
                created_at=row.created_at,
            )
        )

    if resource_type == "copy":
        for row in await LibraryInventoryHistory.find(
            Eq(LibraryInventoryHistory.tenant_id, tenant_id),
            Eq(LibraryInventoryHistory.copy_id, resource_id.upper()),
        ).sort("-created_at").to_list():
            combined.append(
                LibraryAuditTimelineItem(
                    source="inventory_history",
                    event_type=row.event_type,
                    resource_id=row.copy_id,
                    summary=row.note or row.event_type,
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    branch_code=row.branch_code,
                    metadata=dict(row.metadata or {}),
                    created_at=row.created_at,
                )
            )
    elif resource_type == "circulation":
        for row in await LibraryCirculationRecord.find(
            Eq(LibraryCirculationRecord.tenant_id, tenant_id),
            Eq(LibraryCirculationRecord.circulation_id, resource_id),
        ).sort("-created_at").to_list():
            combined.append(
                LibraryAuditTimelineItem(
                    source="circulation_record",
                    event_type=row.action,
                    resource_id=row.circulation_id,
                    summary=f"Circulation {row.action}",
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    branch_code=row.branch_code,
                    metadata=dict(row.metadata or {}),
                    created_at=row.created_at,
                )
            )
    elif resource_type == "book" or resource_type == "catalogue":
        for row in await LibraryCatalogHistory.find(
            Eq(LibraryCatalogHistory.tenant_id, tenant_id),
            Eq(LibraryCatalogHistory.book_id, resource_id),
        ).sort("-created_at").to_list():
            combined.append(
                LibraryAuditTimelineItem(
                    source="catalogue_history",
                    event_type=row.action,
                    resource_id=row.book_id,
                    summary=row.action,
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    metadata=dict(row.snapshot or {}),
                    created_at=row.created_at,
                )
            )
    elif resource_type == "reservation":
        for row in await LibraryReservationHistory.find(
            Eq(LibraryReservationHistory.tenant_id, tenant_id),
            Eq(LibraryReservationHistory.reservation_id, resource_id),
        ).sort("-created_at").to_list():
            combined.append(
                LibraryAuditTimelineItem(
                    source="reservation_history",
                    event_type=row.action,
                    resource_id=row.reservation_id,
                    summary=row.action,
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    metadata=dict(row.changes or {}),
                    created_at=row.created_at,
                )
            )
    elif resource_type == "fine":
        for row in await LibraryFineHistory.find(
            Eq(LibraryFineHistory.tenant_id, tenant_id),
            Eq(LibraryFineHistory.fine_id, resource_id),
        ).sort("-created_at").to_list():
            combined.append(
                LibraryAuditTimelineItem(
                    source="fine_history",
                    event_type=row.action,
                    resource_id=row.fine_id,
                    summary=row.action,
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    metadata=dict(row.changes or {}),
                    created_at=row.created_at,
                )
            )
    elif resource_type == "member":
        member_clauses = [Eq(LibraryMembershipHistory.tenant_id, tenant_id)]
        try:
            member_clauses.append(Eq(LibraryMembershipHistory.member_user_id, PydanticObjectId(resource_id)))
        except Exception:
            member_clauses.append(Eq(LibraryMembershipHistory.membership_number, resource_id))
        for row in await LibraryMembershipHistory.find(*member_clauses).sort("-created_at").to_list():
            combined.append(
                LibraryAuditTimelineItem(
                    source="membership_history",
                    event_type=row.action,
                    resource_id=str(row.member_user_id),
                    summary=row.action,
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    metadata=dict(row.changes or {}),
                    created_at=row.created_at,
                )
            )
    elif resource_type == "policy":
        for row in await LibraryPolicyHistory.find(
            Eq(LibraryPolicyHistory.tenant_id, tenant_id),
            Eq(LibraryPolicyHistory.policy_id, resource_id),
        ).sort("-created_at").to_list():
            combined.append(
                LibraryAuditTimelineItem(
                    source="policy_history",
                    event_type=row.action,
                    resource_id=row.policy_id,
                    summary=row.action,
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    metadata=dict(row.changes or {}),
                    created_at=row.created_at,
                )
            )
    elif resource_type in ("library", "branch", "facility"):
        for row in await LibraryConfigurationHistory.find(
            Eq(LibraryConfigurationHistory.tenant_id, tenant_id),
            Eq(LibraryConfigurationHistory.entity_key, resource_id),
        ).sort("-created_at").to_list():
            combined.append(
                LibraryAuditTimelineItem(
                    source="configuration_history",
                    event_type=row.action,
                    resource_id=row.entity_key,
                    summary=row.action,
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    metadata=dict(row.changes or {}),
                    created_at=row.created_at,
                )
            )
    elif resource_type == "acquisition":
        for row in await LibraryAcquisitionHistory.find(
            Eq(LibraryAcquisitionHistory.tenant_id, tenant_id),
            Eq(LibraryAcquisitionHistory.acquisition_id, resource_id),
        ).sort("-created_at").to_list():
            combined.append(
                LibraryAuditTimelineItem(
                    source="acquisition_history",
                    event_type=row.action,
                    resource_id=row.acquisition_id,
                    summary=row.action,
                    actor_id=str(row.actor_id) if row.actor_id else None,
                    metadata=dict(row.changes or {}),
                    created_at=row.created_at,
                )
            )

    combined.sort(key=lambda item: item.created_at, reverse=True)
    total = len(combined)
    page = combined[pagination.offset : pagination.offset + pagination.limit]
    return Page(items=page, total=total, limit=pagination.limit, offset=pagination.offset)


async def generate_audit_report(
    scope: AccessScope,
    *,
    branch_code: str | None = None,
    domains: list[LibraryAuditDomain] | None = None,
) -> LibraryAuditReportRead:
    tenant_id = require_audit_export(scope)
    clauses: list[Any] = [Eq(LibraryAuditEvent.tenant_id, tenant_id)]
    if branch_code:
        clauses.append(Eq(LibraryAuditEvent.branch_code, branch_code.strip().upper()))
    if domains:
        clauses.append(In(LibraryAuditEvent.domain, domains))
    events = await LibraryAuditEvent.find(*clauses).sort("-created_at").limit(500).to_list()
    disc_query: dict[str, Any] = {"tenant_id": tenant_id, "status": StockDiscrepancyStatus.OPEN.value}
    adj_query: dict[str, Any] = {"tenant_id": tenant_id, "status": StockAdjustmentRequestStatus.PENDING.value}
    if branch_code:
        bc = branch_code.strip().upper()
        disc_query["branch_code"] = bc
        adj_query["branch_code"] = bc
    open_disc = await LibraryStockDiscrepancy.find(disc_query).count()
    pending_adj = await LibraryStockAdjustmentRequest.find(adj_query).count()
    domain_list = [d.value for d in domains] if domains else [d.value for d in LibraryAuditDomain]
    return LibraryAuditReportRead(
        generated_at=utcnow(),
        branch_code=branch_code.strip().upper() if branch_code else None,
        domains=domain_list,
        event_count=len(events),
        open_discrepancies=open_disc,
        pending_adjustments=pending_adj,
        sample_events=[_event_read(e) for e in events[:25]],
    )