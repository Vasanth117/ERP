"""Stock audit discrepancies and approval-gated inventory adjustments."""

from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.library_admin_models import LibraryBookCopyRecord
from app.modules.library.audit_access import require_audit_read, require_discrepancy_manage, require_stock_adjust_approve
from app.modules.library.audit_enums import LibraryAuditDomain, StockAdjustmentRequestStatus, StockDiscrepancyKind, StockDiscrepancyStatus
from app.modules.library.audit_models import LibraryStockAdjustmentRequest, LibraryStockDiscrepancy
from app.modules.library.audit_recorder import record_library_audit
from app.modules.library.audit_schemas import (
    StockAdjustmentDecision,
    StockAdjustmentPropose,
    StockAdjustmentRequestRead,
    StockDiscrepancyRead,
    StockDiscrepancyResolve,
)
from app.modules.library.inventory_enums import StockVerificationItemOutcome
from app.modules.library.inventory_models import (
    LibraryInventoryAdjustment,
    LibraryStockVerification,
    LibraryStockVerificationItem,
)
from app.modules.library.inventory_schemas import InventoryAdjustmentRequest
from app.modules.library.library_models import LibraryCopy


def _disc_read(doc: LibraryStockDiscrepancy) -> StockDiscrepancyRead:
    return StockDiscrepancyRead(
        discrepancy_id=doc.discrepancy_id,
        verification_id=doc.verification_id,
        branch_code=doc.branch_code,
        copy_id=doc.copy_id,
        kind=doc.kind,
        status=doc.status,
        note=doc.note,
        resolution_note=doc.resolution_note,
        created_at=doc.created_at,
        resolved_at=doc.resolved_at,
    )


def _adj_read(doc: LibraryStockAdjustmentRequest) -> StockAdjustmentRequestRead:
    return StockAdjustmentRequestRead(
        request_id=doc.request_id,
        discrepancy_id=doc.discrepancy_id,
        copy_id=doc.copy_id,
        branch_code=doc.branch_code,
        adjustment_type=doc.adjustment_type,
        proposed_status=doc.proposed_status,
        proposed_condition=doc.proposed_condition,
        expected_version=doc.expected_version,
        reason=doc.reason,
        status=doc.status,
        adjustment_id=doc.adjustment_id,
        requested_by=str(doc.requested_by) if doc.requested_by else None,
        decided_by=str(doc.decided_by) if doc.decided_by else None,
        created_at=doc.created_at,
        decided_at=doc.decided_at,
        applied_at=doc.applied_at,
    )


async def create_discrepancies_from_verification(
    scope: AccessScope,
    verification_id: str,
) -> list[StockDiscrepancyRead]:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    session = await LibraryStockVerification.find_one(
        Eq(LibraryStockVerification.tenant_id, tenant_id),
        Eq(LibraryStockVerification.verification_id, verification_id),
    )
    if session is None:
        return []
    items = await LibraryStockVerificationItem.find(
        Eq(LibraryStockVerificationItem.tenant_id, tenant_id),
        Eq(LibraryStockVerificationItem.verification_id, verification_id),
    ).to_list()
    created: list[StockDiscrepancyRead] = []
    for item in items:
        if item.outcome == StockVerificationItemOutcome.FOUND:
            continue
        kind = (
            StockDiscrepancyKind.MISSING
            if item.outcome == StockVerificationItemOutcome.MISSING
            else StockDiscrepancyKind.UNEXPECTED
        )
        disc_id = f"disc_{uuid4().hex[:10]}"
        existing = await LibraryStockDiscrepancy.find_one(
            Eq(LibraryStockDiscrepancy.tenant_id, tenant_id),
            Eq(LibraryStockDiscrepancy.verification_id, verification_id),
            Eq(LibraryStockDiscrepancy.copy_id, item.copy_id),
            Eq(LibraryStockDiscrepancy.kind, kind),
        )
        if existing is not None:
            created.append(_disc_read(existing))
            continue
        doc = LibraryStockDiscrepancy(
            tenant_id=tenant_id,
            discrepancy_id=disc_id,
            verification_id=verification_id,
            branch_code=session.branch_code,
            copy_id=item.copy_id,
            kind=kind,
            note=f"Auto-reported from verification {verification_id}",
            reported_by=scope.user_id,
            metadata={"outcome": item.outcome.value},
        )
        await doc.insert()
        await record_library_audit(
            tenant_id,
            actor_id=scope.user_id,
            domain=LibraryAuditDomain.INVENTORY,
            action="library_inventory.discrepancy.reported",
            resource_type="stock_discrepancy",
            resource_id=disc_id,
            branch_code=session.branch_code,
            after_state={"kind": kind.value, "copy_id": item.copy_id, "verification_id": verification_id},
        )
        created.append(_disc_read(doc))
    return created


async def list_discrepancies(
    scope: AccessScope,
    pagination: Pagination,
    *,
    branch_code: str | None = None,
    status: StockDiscrepancyStatus | None = None,
    verification_id: str | None = None,
) -> Page[StockDiscrepancyRead]:
    tenant_id = require_audit_read(scope)
    clauses = [Eq(LibraryStockDiscrepancy.tenant_id, tenant_id)]
    if branch_code:
        clauses.append(Eq(LibraryStockDiscrepancy.branch_code, branch_code.strip().upper()))
    if status is not None:
        clauses.append(Eq(LibraryStockDiscrepancy.status, status))
    if verification_id:
        clauses.append(Eq(LibraryStockDiscrepancy.verification_id, verification_id.strip()))
    query = LibraryStockDiscrepancy.find(*clauses)
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_disc_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def resolve_discrepancy(
    scope: AccessScope,
    discrepancy_id: str,
    payload: StockDiscrepancyResolve,
) -> StockDiscrepancyRead:
    tenant_id = require_discrepancy_manage(scope)
    if payload.resolution not in (StockDiscrepancyStatus.RESOLVED, StockDiscrepancyStatus.DISMISSED):
        raise AppError(code="VALIDATION_ERROR", message="resolution must be resolved or dismissed", status_code=422)
    doc = await LibraryStockDiscrepancy.find_one(
        Eq(LibraryStockDiscrepancy.tenant_id, tenant_id),
        Eq(LibraryStockDiscrepancy.discrepancy_id, discrepancy_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Discrepancy not found", status_code=404)
    if doc.status != StockDiscrepancyStatus.OPEN:
        raise AppError(code="CONFLICT", message="Discrepancy already closed", status_code=409)
    before = {"status": doc.status.value}
    doc.status = payload.resolution
    doc.resolution_note = payload.resolution_note
    doc.resolved_by = scope.user_id
    doc.resolved_at = utcnow()
    await doc.save()
    await record_library_audit(
        tenant_id,
        actor_id=scope.user_id,
        domain=LibraryAuditDomain.INVENTORY,
        action="library_inventory.discrepancy.resolve",
        resource_type="stock_discrepancy",
        resource_id=doc.discrepancy_id,
        branch_code=doc.branch_code,
        before_state=before,
        after_state={"status": doc.status.value, "resolution_note": doc.resolution_note},
    )
    return _disc_read(doc)


async def propose_stock_adjustment(scope: AccessScope, payload: StockAdjustmentPropose) -> StockAdjustmentRequestRead:
    tenant_id = require_discrepancy_manage(scope)
    copy = await LibraryCopy.find_one(
        Eq(LibraryCopy.tenant_id, tenant_id),
        Eq(LibraryCopy.copy_id, payload.copy_id.strip().upper()),
    )
    if copy is None:
        raise AppError(code="NOT_FOUND", message="Copy not found", status_code=404)
    branch_code = copy.branch_code
    if not branch_code:
        admin = await LibraryBookCopyRecord.find_one(
            Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
            Eq(LibraryBookCopyRecord.copy_id, copy.copy_id),
        )
        branch_code = admin.branch_code if admin else None
    if not branch_code:
        raise AppError(code="VALIDATION_ERROR", message="Copy has no branch", status_code=422)
    if payload.discrepancy_id:
        disc = await LibraryStockDiscrepancy.find_one(
            Eq(LibraryStockDiscrepancy.tenant_id, tenant_id),
            Eq(LibraryStockDiscrepancy.discrepancy_id, payload.discrepancy_id),
        )
        if disc is None or disc.status != StockDiscrepancyStatus.OPEN:
            raise AppError(code="VALIDATION_ERROR", message="Open discrepancy required", status_code=422)
    request_id = f"sar_{uuid4().hex[:10]}"
    doc = LibraryStockAdjustmentRequest(
        tenant_id=tenant_id,
        request_id=request_id,
        discrepancy_id=payload.discrepancy_id,
        copy_id=copy.copy_id,
        branch_code=branch_code,
        adjustment_type=payload.adjustment_type,
        proposed_status=payload.proposed_status,
        proposed_condition=payload.proposed_condition,
        expected_version=payload.expected_version,
        reason=payload.reason.strip(),
        requested_by=scope.user_id,
    )
    await doc.insert()
    await record_library_audit(
        tenant_id,
        actor_id=scope.user_id,
        domain=LibraryAuditDomain.INVENTORY,
        action="library_inventory.adjustment.proposed",
        resource_type="stock_adjustment_request",
        resource_id=request_id,
        branch_code=branch_code,
        after_state={
            "copy_id": copy.copy_id,
            "adjustment_type": payload.adjustment_type.value,
            "proposed_status": payload.proposed_status.value if payload.proposed_status else None,
        },
        metadata={"discrepancy_id": payload.discrepancy_id},
    )
    return _adj_read(doc)


async def list_stock_adjustment_requests(
    scope: AccessScope,
    pagination: Pagination,
    *,
    status: StockAdjustmentRequestStatus | None = None,
) -> Page[StockAdjustmentRequestRead]:
    tenant_id = require_discrepancy_manage(scope)
    clauses = [Eq(LibraryStockAdjustmentRequest.tenant_id, tenant_id)]
    if status is not None:
        clauses.append(Eq(LibraryStockAdjustmentRequest.status, status))
    query = LibraryStockAdjustmentRequest.find(*clauses)
    total = await query.count()
    rows = await query.sort("-created_at").skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_adj_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def approve_stock_adjustment(
    scope: AccessScope,
    request_id: str,
    payload: StockAdjustmentDecision,
) -> StockAdjustmentRequestRead:
    tenant_id = require_stock_adjust_approve(scope)
    if scope.user_id is None:
        raise AppError(code="FORBIDDEN", message="Actor required", status_code=403)
    doc = await LibraryStockAdjustmentRequest.find_one(
        Eq(LibraryStockAdjustmentRequest.tenant_id, tenant_id),
        Eq(LibraryStockAdjustmentRequest.request_id, request_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Adjustment request not found", status_code=404)
    if doc.status != StockAdjustmentRequestStatus.PENDING:
        raise AppError(code="CONFLICT", message="Request is not pending", status_code=409)
    if doc.requested_by == scope.user_id:
        raise AppError(code="FORBIDDEN", message="Separation of duties: cannot approve own request", status_code=403)
    copy = await LibraryCopy.find_one(
        Eq(LibraryCopy.tenant_id, tenant_id),
        Eq(LibraryCopy.copy_id, doc.copy_id),
    )
    if copy is None:
        raise AppError(code="NOT_FOUND", message="Copy not found", status_code=404)
    before = {"status": copy.status.value, "condition": copy.condition.value, "version": copy.version}
    from app.modules.library.inventory_service import apply_adjustment

    result = await apply_adjustment(
        scope,
        InventoryAdjustmentRequest(
            copy_id=doc.copy_id,
            adjustment_type=doc.adjustment_type,
            new_status=doc.proposed_status,
            new_condition=doc.proposed_condition,
            reason=doc.reason,
            expected_version=doc.expected_version,
        ),
    )
    doc.status = StockAdjustmentRequestStatus.APPLIED
    doc.decided_by = scope.user_id
    doc.decision_note = payload.decision_note
    doc.decided_at = utcnow()
    doc.applied_at = utcnow()
    latest_adj = (
        await LibraryInventoryAdjustment.find(
            Eq(LibraryInventoryAdjustment.tenant_id, tenant_id),
            Eq(LibraryInventoryAdjustment.copy_id, doc.copy_id),
        )
        .sort("-created_at")
        .first_or_none()
    )
    doc.adjustment_id = latest_adj.adjustment_id if latest_adj else None
    await doc.save()
    if doc.discrepancy_id:
        disc = await LibraryStockDiscrepancy.find_one(
            Eq(LibraryStockDiscrepancy.tenant_id, tenant_id),
            Eq(LibraryStockDiscrepancy.discrepancy_id, doc.discrepancy_id),
        )
        if disc and disc.status == StockDiscrepancyStatus.OPEN:
            disc.status = StockDiscrepancyStatus.RESOLVED
            disc.resolution_note = "Resolved via approved stock adjustment"
            disc.resolved_by = scope.user_id
            disc.resolved_at = utcnow()
            await disc.save()
    await record_library_audit(
        tenant_id,
        actor_id=scope.user_id,
        domain=LibraryAuditDomain.INVENTORY,
        action="library_inventory.adjustment.applied",
        resource_type="stock_adjustment_request",
        resource_id=doc.request_id,
        branch_code=doc.branch_code,
        before_state=before,
        after_state={"status": result.status.value, "condition": result.condition.value, "version": result.version},
    )
    return _adj_read(doc)


async def reject_stock_adjustment(
    scope: AccessScope,
    request_id: str,
    payload: StockAdjustmentDecision,
) -> StockAdjustmentRequestRead:
    tenant_id = require_stock_adjust_approve(scope)
    doc = await LibraryStockAdjustmentRequest.find_one(
        Eq(LibraryStockAdjustmentRequest.tenant_id, tenant_id),
        Eq(LibraryStockAdjustmentRequest.request_id, request_id),
    )
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Adjustment request not found", status_code=404)
    if doc.status != StockAdjustmentRequestStatus.PENDING:
        raise AppError(code="CONFLICT", message="Request is not pending", status_code=409)
    doc.status = StockAdjustmentRequestStatus.REJECTED
    doc.decided_by = scope.user_id
    doc.decision_note = payload.decision_note
    doc.decided_at = utcnow()
    await doc.save()
    await record_library_audit(
        tenant_id,
        actor_id=scope.user_id,
        domain=LibraryAuditDomain.INVENTORY,
        action="library_inventory.adjustment.rejected",
        resource_type="stock_adjustment_request",
        resource_id=doc.request_id,
        branch_code=doc.branch_code,
        after_state={"status": doc.status.value, "decision_note": doc.decision_note},
    )
    return _adj_read(doc)