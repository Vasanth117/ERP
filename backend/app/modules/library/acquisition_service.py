"""Book acquisition and procurement (library module)."""

from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.finance_ext_models import (
    InstitutionPurchaseOrder,
    InstitutionPurchaseRequest,
    InstitutionVendorRecord,
)
from app.modules.college_admin.library_admin_models import LibraryAcquisition, LibraryBranch
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.acquisition_access import (
    authorize_acquisition_approve,
    authorize_acquisition_procurement,
    authorize_acquisition_read,
    require_acquisition_manage,
)
from app.modules.library.acquisition_enums import LibraryAcquisitionStatus, LibraryAcquisitionType
from app.modules.library.acquisition_models import (
    LibraryAcquisitionHistory,
    LibraryAcquisitionQuotation,
    LibraryAcquisitionReceipt,
    LibraryInventoryRegistrationRequest,
)
from app.modules.library.acquisition_schemas import (
    AcquisitionApprovalDecision,
    AcquisitionCreateRequest,
    AcquisitionHistoryEntry,
    AcquisitionRead,
    CatalogueLinkRequest,
    ProcurementSyncRequest,
    QuotationCreateRequest,
    ReceiptRecordRequest,
)
from app.modules.library.library_models import LibraryCatalogItem
from app.modules.library.policy import require_library_tenant_scope


def _norm_branch(code: str | None) -> str | None:
    if not code:
        return None
    return code.strip().upper()


def _acq_id(custom: str | None) -> str:
    if custom and custom.strip():
        return custom.strip()
    return f"acq_{uuid4().hex[:12]}"


async def _history(
    tenant_id: PydanticObjectId,
    *,
    acquisition_id: str,
    action: str,
    actor_id: PydanticObjectId | None,
    changes: dict[str, Any],
) -> None:
    await LibraryAcquisitionHistory(
        tenant_id=tenant_id,
        acquisition_id=acquisition_id,
        action=action,
        actor_id=actor_id,
        changes=changes,
    ).insert()


async def _assert_vendor(tenant_id: PydanticObjectId, vendor_id: str | None) -> None:
    if not vendor_id:
        return
    v = await InstitutionVendorRecord.find_one(
        Eq(InstitutionVendorRecord.tenant_id, tenant_id),
        Eq(InstitutionVendorRecord.vendor_id, vendor_id),
    )
    if v is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown vendor", status_code=422)


async def _assert_branch(tenant_id: PydanticObjectId, branch_code: str | None) -> None:
    if not branch_code:
        return
    exists = await LibraryBranch.find_one(Eq(LibraryBranch.tenant_id, tenant_id), Eq(LibraryBranch.branch_code, branch_code))
    if exists is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown branch", status_code=422)


def _to_read(doc: LibraryAcquisition) -> AcquisitionRead:
    try:
        req_type = LibraryAcquisitionType(doc.request_type)
    except ValueError:
        req_type = LibraryAcquisitionType.PURCHASE
    return AcquisitionRead(
        acquisition_id=doc.acquisition_id,
        request_type=req_type,
        title=doc.title or doc.metadata.get("title") or doc.acquisition_id,
        isbn=doc.isbn,
        book_id=doc.book_id,
        branch_code=doc.branch_code,
        vendor_id=doc.vendor_id,
        quantity=doc.quantity,
        quantity_received=doc.quantity_received,
        status=doc.status,
        approval_status=doc.approval_status,
        purchase_request_id=doc.purchase_request_id,
        purchase_order_id=doc.purchase_order_id,
        selected_quotation_id=doc.selected_quotation_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


async def create_acquisition(scope: AccessScope, payload: AcquisitionCreateRequest) -> AcquisitionRead:
    tenant_id = require_library_tenant_scope(scope)
    await require_acquisition_manage(scope, branch_code=payload.branch_code)
    branch = _norm_branch(payload.branch_code)
    await _assert_branch(tenant_id, branch)
    await _assert_vendor(tenant_id, payload.vendor_id)
    aid = _acq_id(payload.acquisition_id)
    if await LibraryAcquisition.find_one(Eq(LibraryAcquisition.tenant_id, tenant_id), Eq(LibraryAcquisition.acquisition_id, aid)):
        raise AppError(code="CONFLICT", message="Acquisition id already used", status_code=409)
    if payload.book_id:
        item = await LibraryCatalogItem.find_one(Eq(LibraryCatalogItem.tenant_id, tenant_id), Eq(LibraryCatalogItem.book_id, payload.book_id))
        if item is None:
            raise AppError(code="VALIDATION_ERROR", message="Unknown catalogue book_id", status_code=422)
    doc = LibraryAcquisition(
        tenant_id=tenant_id,
        acquisition_id=aid,
        request_type=payload.request_type.value,
        title=payload.title.strip(),
        isbn=payload.isbn.strip() if payload.isbn else None,
        book_id=payload.book_id,
        branch_code=branch,
        vendor_id=payload.vendor_id,
        quantity=payload.quantity,
        status=LibraryAcquisitionStatus.DRAFT.value,
        approval_status=LibraryAcquisitionStatus.DRAFT.value,
        suggested_by=scope.user_id if payload.request_type == LibraryAcquisitionType.SUGGESTION else None,
        actor_id=scope.user_id,
    )
    await doc.insert()
    await _history(tenant_id, acquisition_id=aid, action="create", actor_id=scope.user_id, changes=payload.model_dump(mode="json"))
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_acquisition.create",
        module="library_acquisition",
        resource_type="acquisition",
        resource_id=aid,
    )
    return _to_read(doc)


async def submit_acquisition(scope: AccessScope, acquisition_id: str) -> AcquisitionRead:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryAcquisition.find_one(Eq(LibraryAcquisition.tenant_id, tenant_id), Eq(LibraryAcquisition.acquisition_id, acquisition_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Acquisition not found", status_code=404)
    await require_acquisition_manage(scope, branch_code=doc.branch_code)
    if doc.status != LibraryAcquisitionStatus.DRAFT.value:
        raise AppError(code="CONFLICT", message="Only draft requests can be submitted", status_code=409)
    doc.status = LibraryAcquisitionStatus.SUBMITTED.value
    doc.approval_status = LibraryAcquisitionStatus.PENDING_APPROVAL.value
    doc.metadata = {**doc.metadata, "submitted_by": str(scope.user_id)}
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, acquisition_id=acquisition_id, action="submit", actor_id=scope.user_id, changes={})
    return _to_read(doc)


async def decide_acquisition_approval(scope: AccessScope, acquisition_id: str, payload: AcquisitionApprovalDecision) -> AcquisitionRead:
    authorize_acquisition_approve(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryAcquisition.find_one(Eq(LibraryAcquisition.tenant_id, tenant_id), Eq(LibraryAcquisition.acquisition_id, acquisition_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Acquisition not found", status_code=404)
    if doc.approval_status != LibraryAcquisitionStatus.PENDING_APPROVAL.value:
        raise AppError(code="CONFLICT", message="Not pending approval", status_code=409)
    submitted_by = doc.metadata.get("submitted_by")
    if payload.approved and submitted_by and submitted_by == str(scope.user_id):
        raise AppError(code="FORBIDDEN", message="Approver must differ from submitter", status_code=403)
    if payload.approved:
        doc.approval_status = LibraryAcquisitionStatus.APPROVED.value
        doc.status = LibraryAcquisitionStatus.APPROVED.value
    else:
        doc.approval_status = LibraryAcquisitionStatus.REJECTED.value
        doc.status = LibraryAcquisitionStatus.REJECTED.value
    doc.updated_at = utcnow()
    await doc.save()
    await _history(
        tenant_id,
        acquisition_id=acquisition_id,
        action="approval",
        actor_id=scope.user_id,
        changes={"approved": payload.approved, "note": payload.note},
    )
    return _to_read(doc)


async def add_quotation(scope: AccessScope, acquisition_id: str, payload: QuotationCreateRequest) -> dict:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryAcquisition.find_one(Eq(LibraryAcquisition.tenant_id, tenant_id), Eq(LibraryAcquisition.acquisition_id, acquisition_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Acquisition not found", status_code=404)
    await require_acquisition_manage(scope, branch_code=doc.branch_code)
    await _assert_vendor(tenant_id, payload.vendor_id)
    qid = payload.quotation_id or f"qt_{uuid4().hex[:10]}"
    await LibraryAcquisitionQuotation(
        tenant_id=tenant_id,
        quotation_id=qid,
        acquisition_id=acquisition_id,
        vendor_id=payload.vendor_id,
        amount=payload.amount,
        valid_until=payload.valid_until,
        notes=payload.notes,
        created_by=scope.user_id,
    ).insert()
    doc.status = LibraryAcquisitionStatus.QUOTED.value
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, acquisition_id=acquisition_id, action="quotation", actor_id=scope.user_id, changes={"quotation_id": qid})
    return {"quotation_id": qid, "amount": payload.amount}


async def select_quotation(scope: AccessScope, acquisition_id: str, quotation_id: str) -> AcquisitionRead:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryAcquisition.find_one(Eq(LibraryAcquisition.tenant_id, tenant_id), Eq(LibraryAcquisition.acquisition_id, acquisition_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Acquisition not found", status_code=404)
    await require_acquisition_manage(scope, branch_code=doc.branch_code)
    quote = await LibraryAcquisitionQuotation.find_one(
        Eq(LibraryAcquisitionQuotation.tenant_id, tenant_id),
        Eq(LibraryAcquisitionQuotation.quotation_id, quotation_id),
        Eq(LibraryAcquisitionQuotation.acquisition_id, acquisition_id),
    )
    if quote is None:
        raise AppError(code="NOT_FOUND", message="Quotation not found", status_code=404)
    for other in await LibraryAcquisitionQuotation.find(
        Eq(LibraryAcquisitionQuotation.tenant_id, tenant_id),
        Eq(LibraryAcquisitionQuotation.acquisition_id, acquisition_id),
    ).to_list():
        if other.selected:
            other.selected = False
            await other.save()
    quote.selected = True
    await quote.save()
    doc.selected_quotation_id = quotation_id
    doc.vendor_id = quote.vendor_id
    doc.status = LibraryAcquisitionStatus.ORDERED.value
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, acquisition_id=acquisition_id, action="select_quote", actor_id=scope.user_id, changes={"quotation_id": quotation_id})
    return _to_read(doc)


async def sync_procurement_refs(scope: AccessScope, acquisition_id: str, payload: ProcurementSyncRequest) -> AcquisitionRead:
    authorize_acquisition_procurement(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryAcquisition.find_one(Eq(LibraryAcquisition.tenant_id, tenant_id), Eq(LibraryAcquisition.acquisition_id, acquisition_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Acquisition not found", status_code=404)
    pr = await InstitutionPurchaseRequest.find_one(
        Eq(InstitutionPurchaseRequest.tenant_id, tenant_id),
        Eq(InstitutionPurchaseRequest.request_id, payload.purchase_request_id),
    )
    if pr is None:
        raise AppError(code="NOT_FOUND", message="Purchase request not found", status_code=404)
    doc.purchase_request_id = payload.purchase_request_id
    if payload.purchase_order_id:
        po = await InstitutionPurchaseOrder.find_one(
            Eq(InstitutionPurchaseOrder.tenant_id, tenant_id),
            Eq(InstitutionPurchaseOrder.order_id, payload.purchase_order_id),
        )
        if po is None:
            raise AppError(code="NOT_FOUND", message="Purchase order not found", status_code=404)
        doc.purchase_order_id = payload.purchase_order_id
        doc.status = LibraryAcquisitionStatus.ORDERED.value
    doc.vendor_id = doc.vendor_id or pr.vendor_id
    doc.updated_at = utcnow()
    await doc.save()
    await _history(
        tenant_id,
        acquisition_id=acquisition_id,
        action="procurement_link",
        actor_id=scope.user_id,
        changes=payload.model_dump(),
    )
    return _to_read(doc)


async def record_receipt(scope: AccessScope, acquisition_id: str, payload: ReceiptRecordRequest) -> AcquisitionRead:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryAcquisition.find_one(Eq(LibraryAcquisition.tenant_id, tenant_id), Eq(LibraryAcquisition.acquisition_id, acquisition_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Acquisition not found", status_code=404)
    await require_acquisition_manage(scope, branch_code=doc.branch_code)
    if doc.status in (LibraryAcquisitionStatus.DRAFT.value, LibraryAcquisitionStatus.REJECTED.value, LibraryAcquisitionStatus.CANCELLED.value):
        raise AppError(code="CONFLICT", message="Cannot receive for this status", status_code=409)
    remaining = doc.quantity - doc.quantity_received
    if payload.quantity > remaining:
        raise AppError(code="VALIDATION_ERROR", message="Quantity exceeds outstanding order", status_code=422)
    rid = payload.receipt_id or f"rcv_{uuid4().hex[:10]}"
    await LibraryAcquisitionReceipt(
        tenant_id=tenant_id,
        receipt_id=rid,
        acquisition_id=acquisition_id,
        quantity=payload.quantity,
        verified_by=scope.user_id,
        notes=payload.notes,
    ).insert()
    doc.quantity_received += payload.quantity
    if doc.quantity_received >= doc.quantity:
        doc.status = LibraryAcquisitionStatus.RECEIVED.value
    else:
        doc.status = LibraryAcquisitionStatus.PARTIAL_RECEIVED.value
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, acquisition_id=acquisition_id, action="receive", actor_id=scope.user_id, changes={"quantity": payload.quantity, "receipt_id": rid})
    return _to_read(doc)


async def link_catalogue(scope: AccessScope, acquisition_id: str, payload: CatalogueLinkRequest) -> AcquisitionRead:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryAcquisition.find_one(Eq(LibraryAcquisition.tenant_id, tenant_id), Eq(LibraryAcquisition.acquisition_id, acquisition_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Acquisition not found", status_code=404)
    await require_acquisition_manage(scope, branch_code=doc.branch_code)
    item = await LibraryCatalogItem.find_one(Eq(LibraryCatalogItem.tenant_id, tenant_id), Eq(LibraryCatalogItem.book_id, payload.book_id.strip()))
    if item is None:
        raise AppError(code="NOT_FOUND", message="Catalogue title not found", status_code=404)
    doc.book_id = payload.book_id.strip()
    doc.title = item.title
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, acquisition_id=acquisition_id, action="link_catalogue", actor_id=scope.user_id, changes={"book_id": doc.book_id})
    return _to_read(doc)


async def request_inventory_registration(scope: AccessScope, acquisition_id: str) -> dict:
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryAcquisition.find_one(Eq(LibraryAcquisition.tenant_id, tenant_id), Eq(LibraryAcquisition.acquisition_id, acquisition_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Acquisition not found", status_code=404)
    await require_acquisition_manage(scope, branch_code=doc.branch_code)
    if not doc.book_id:
        raise AppError(code="VALIDATION_ERROR", message="Catalogue link required", status_code=422)
    if doc.quantity_received <= 0:
        raise AppError(code="VALIDATION_ERROR", message="No received quantity to register", status_code=422)
    reg_id = f"reg_{uuid4().hex[:10]}"
    await LibraryInventoryRegistrationRequest(
        tenant_id=tenant_id,
        registration_id=reg_id,
        acquisition_id=acquisition_id,
        book_id=doc.book_id,
        branch_code=doc.branch_code,
        quantity_expected=doc.quantity_received,
        created_by=scope.user_id,
    ).insert()
    doc.status = LibraryAcquisitionStatus.REGISTERED.value
    doc.updated_at = utcnow()
    await doc.save()
    await _history(tenant_id, acquisition_id=acquisition_id, action="inventory_registration", actor_id=scope.user_id, changes={"registration_id": reg_id})
    return {"registration_id": reg_id, "book_id": doc.book_id, "quantity_expected": doc.quantity_received}


async def get_acquisition(scope: AccessScope, acquisition_id: str) -> AcquisitionRead:
    authorize_acquisition_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    doc = await LibraryAcquisition.find_one(Eq(LibraryAcquisition.tenant_id, tenant_id), Eq(LibraryAcquisition.acquisition_id, acquisition_id))
    if doc is None:
        raise AppError(code="NOT_FOUND", message="Acquisition not found", status_code=404)
    return _to_read(doc)


async def search_acquisitions(
    scope: AccessScope,
    pagination: Pagination,
    *,
    branch_code: str | None = None,
    status: str | None = None,
) -> Page[AcquisitionRead]:
    authorize_acquisition_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if branch_code:
        filters["branch_code"] = _norm_branch(branch_code)
    if status:
        filters["status"] = status
    query = LibraryAcquisition.find(filters).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    return Page(items=[_to_read(r) for r in rows], total=total, limit=pagination.limit, offset=pagination.offset)


async def acquisition_history(scope: AccessScope, acquisition_id: str, pagination: Pagination) -> Page[AcquisitionHistoryEntry]:
    authorize_acquisition_read(scope)
    tenant_id = require_library_tenant_scope(scope)
    query = LibraryAcquisitionHistory.find(
        Eq(LibraryAcquisitionHistory.tenant_id, tenant_id),
        Eq(LibraryAcquisitionHistory.acquisition_id, acquisition_id),
    ).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        AcquisitionHistoryEntry(
            action=r.action,
            actor_id=str(r.actor_id) if r.actor_id else None,
            changes=r.changes,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def college_admin_create_acquisition(scope: AccessScope, payload: AcquisitionCreateRequest) -> dict:
    """Bridge for legacy college-admin route."""
    read = await create_acquisition(scope, payload)
    return {"acquisition_id": read.acquisition_id, "status": read.status}