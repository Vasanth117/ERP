"""Book copy inventory management."""

from typing import Any
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.common.access import AccessScope
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.library_admin_models import LibraryBookCopyRecord, LibraryBranch, LibraryInventoryHistory
from app.modules.college_admin.security_admin_service import append_institution_audit
from app.modules.library.facility_models import LibraryShelfLocation
from app.modules.library.inventory_access import authorize_inventory_read, require_inventory_manage, require_inventory_read
from app.modules.library.inventory_enums import InventoryAdjustmentType, StockVerificationItemOutcome, StockVerificationStatus
from app.modules.library.inventory_models import LibraryInventoryAdjustment, LibraryStockVerification, LibraryStockVerificationItem
from app.modules.library.inventory_schemas import (
    CopyDuplicateMatch,
    CopyInventoryRead,
    CopyRegisterRequest,
    CopyTransferRequest,
    CopyUpdateRequest,
    InventoryAdjustmentRequest,
    InventoryHistoryRead,
    MissingCopySummary,
    StockVerificationCreate,
    StockVerificationRead,
    StockVerificationScan,
)
from app.modules.library.inventory_validation import assert_transferable_status, normalize_barcode
from app.modules.library.library_enums import LibraryCopyCondition, LibraryCopyStatus
from app.modules.library.library_models import LibraryCatalogItem, LibraryCopy


def _norm_branch(code: str) -> str:
    return code.strip().upper()


def _generate_copy_id() -> str:
    return f"CPY-{uuid4().hex[:10].upper()}"


async def _assert_catalogue(tenant_id: PydanticObjectId, book_id: str) -> LibraryCatalogItem:
    item = await LibraryCatalogItem.find_one(
        Eq(LibraryCatalogItem.tenant_id, tenant_id),
        Eq(LibraryCatalogItem.book_id, book_id.strip()),
    )
    if item is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown catalogue book_id", status_code=422)
    if item.archived:
        raise AppError(code="CONFLICT", message="Cannot attach copies to archived catalogue title", status_code=409)
    return item


async def _assert_branch(tenant_id: PydanticObjectId, branch_code: str) -> LibraryBranch:
    branch = await LibraryBranch.find_one(
        Eq(LibraryBranch.tenant_id, tenant_id),
        Eq(LibraryBranch.branch_code, _norm_branch(branch_code)),
    )
    if branch is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown branch", status_code=422)
    return branch


async def _assert_shelf(tenant_id: PydanticObjectId, branch_code: str, location_code: str | None) -> None:
    if not location_code:
        return
    loc = await LibraryShelfLocation.find_one(
        Eq(LibraryShelfLocation.tenant_id, tenant_id),
        Eq(LibraryShelfLocation.branch_code, _norm_branch(branch_code)),
        Eq(LibraryShelfLocation.location_code, location_code.strip().upper()),
        Eq(LibraryShelfLocation.is_active, True),
    )
    if loc is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown or inactive shelf location", status_code=422)


async def _library_for_branch(tenant_id: PydanticObjectId, branch: LibraryBranch) -> str | None:
    return branch.library_code.upper() if branch.library_code else None


async def _history(
    tenant_id: PydanticObjectId,
    *,
    copy_id: str,
    branch_code: str | None,
    event_type: str,
    note: str | None,
    metadata: dict[str, Any],
    actor_id: PydanticObjectId | None,
) -> None:
    await LibraryInventoryHistory(
        tenant_id=tenant_id,
        branch_code=branch_code,
        copy_id=copy_id,
        event_type=event_type,
        note=note,
        metadata=metadata,
        actor_id=actor_id,
    ).insert()


def _to_read(copy: LibraryCopy, admin: LibraryBookCopyRecord | None) -> CopyInventoryRead:
    return CopyInventoryRead(
        copy_id=copy.copy_id,
        book_id=copy.book_id,
        barcode=copy.barcode,
        accession_number=admin.accession_number if admin else None,
        branch_code=copy.branch_code,
        shelf_location_code=copy.shelf_location_code,
        condition=copy.condition,
        status=copy.status,
        notes=copy.notes,
        version=copy.version,
        created_at=copy.created_at,
        updated_at=copy.updated_at,
    )


async def _load_pair(tenant_id: PydanticObjectId, copy_id: str) -> tuple[LibraryCopy, LibraryBookCopyRecord]:
    admin = await LibraryBookCopyRecord.find_one(
        Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
        Eq(LibraryBookCopyRecord.copy_id, copy_id),
    )
    copy = await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.copy_id, copy_id))
    if copy is None or admin is None:
        raise AppError(code="NOT_FOUND", message="Copy not found", status_code=404)
    return copy, admin


async def _assert_version(copy: LibraryCopy, expected: int | None) -> None:
    if expected is None:
        return
    if copy.version != expected:
        raise AppError(code="CONFLICT", message="Copy was modified by another request", status_code=409)


async def register_copy(scope: AccessScope, payload: CopyRegisterRequest) -> CopyInventoryRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    branch = await _assert_branch(tenant_id, payload.branch_code)
    library_code = await _library_for_branch(tenant_id, branch)
    await require_inventory_manage(scope, branch_code=branch.branch_code, library_code=library_code)
    await _assert_catalogue(tenant_id, payload.book_id)
    await _assert_shelf(tenant_id, branch.branch_code, payload.shelf_location_code)
    barcode = normalize_barcode(payload.barcode)
    copy_id = payload.copy_id.strip().upper() if payload.copy_id else _generate_copy_id()
    if await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.copy_id, copy_id)):
        raise AppError(code="CONFLICT", message="copy_id exists", status_code=409)
    if await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.barcode, barcode)):
        raise AppError(code="CONFLICT", message="barcode exists", status_code=409)
    if await LibraryBookCopyRecord.find_one(Eq(LibraryBookCopyRecord.tenant_id, tenant_id), Eq(LibraryBookCopyRecord.copy_id, copy_id)):
        raise AppError(code="CONFLICT", message="copy_id exists", status_code=409)
    if payload.accession_number:
        acc = payload.accession_number.strip()
        if await LibraryBookCopyRecord.find_one(Eq(LibraryBookCopyRecord.tenant_id, tenant_id), Eq(LibraryBookCopyRecord.accession_number, acc)):
            raise AppError(code="CONFLICT", message="accession_number exists", status_code=409)
    shelf = payload.shelf_location_code.strip().upper() if payload.shelf_location_code else None
    copy = LibraryCopy(
        tenant_id=tenant_id,
        copy_id=copy_id,
        book_id=payload.book_id.strip(),
        barcode=barcode,
        branch_code=branch.branch_code,
        shelf_location_code=shelf,
        condition=payload.condition,
        status=payload.status,
        notes=payload.notes,
        created_by=scope.user_id,
        updated_by=scope.user_id,
    )
    await copy.insert()
    admin = LibraryBookCopyRecord(
        tenant_id=tenant_id,
        copy_id=copy_id,
        book_id=copy.book_id,
        barcode=barcode,
        accession_number=payload.accession_number.strip() if payload.accession_number else None,
        branch_code=branch.branch_code,
        shelf_location_code=shelf,
        authoritative_copy_id=copy.id,
        updated_by=scope.user_id,
    )
    await admin.insert()
    await _history(
        tenant_id,
        copy_id=copy_id,
        branch_code=branch.branch_code,
        event_type="copy_registered",
        note="Physical copy registered",
        metadata={"book_id": copy.book_id, "barcode": barcode},
        actor_id=scope.user_id,
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_inventory.register",
        module="library_inventory",
        resource_type="copy",
        resource_id=copy_id,
    )
    return _to_read(copy, admin)


async def get_copy(scope: AccessScope, copy_id: str) -> CopyInventoryRead:
    tenant_id = await require_inventory_read(scope)
    copy, admin = await _load_pair(tenant_id, copy_id.strip().upper())
    if copy.branch_code:
        branch = await LibraryBranch.find_one(Eq(LibraryBranch.tenant_id, tenant_id), Eq(LibraryBranch.branch_code, copy.branch_code))
        lib = await _library_for_branch(tenant_id, branch) if branch else None
        if lib:
            await require_inventory_read(scope, branch_code=copy.branch_code, library_code=lib)
    return _to_read(copy, admin)


async def list_copies(
    scope: AccessScope,
    pagination: Pagination,
    *,
    book_id: str | None = None,
    branch_code: str | None = None,
    status: LibraryCopyStatus | None = None,
) -> Page[CopyInventoryRead]:
    tenant_id = await require_inventory_read(scope)
    filters: dict[str, Any] = {"tenant_id": tenant_id}
    if book_id:
        filters["book_id"] = book_id.strip()
    if branch_code:
        code = _norm_branch(branch_code)
        filters["branch_code"] = code
        branch = await _assert_branch(tenant_id, code)
        lib = await _library_for_branch(tenant_id, branch)
        if lib:
            await require_inventory_read(scope, branch_code=code, library_code=lib)
    if status:
        filters["status"] = status.value
    query = LibraryCopy.find(filters).sort("copy_id")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items: list[CopyInventoryRead] = []
    for row in rows:
        admin = await LibraryBookCopyRecord.find_one(
            Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
            Eq(LibraryBookCopyRecord.copy_id, row.copy_id),
        )
        items.append(_to_read(row, admin))
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)


async def update_copy(scope: AccessScope, copy_id: str, payload: CopyUpdateRequest) -> CopyInventoryRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    copy, admin = await _load_pair(tenant_id, copy_id.strip().upper())
    branch_key = copy.branch_code or admin.branch_code
    if not branch_key:
        raise AppError(code="VALIDATION_ERROR", message="Copy has no branch assignment", status_code=422)
    branch = await _assert_branch(tenant_id, branch_key)
    lib = await _library_for_branch(tenant_id, branch)
    await require_inventory_manage(scope, branch_code=branch.branch_code, library_code=lib)
    await _assert_version(copy, payload.expected_version)
    if payload.barcode is not None:
        barcode = normalize_barcode(payload.barcode)
        other = await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.barcode, barcode))
        if other and other.copy_id != copy.copy_id:
            raise AppError(code="CONFLICT", message="barcode exists", status_code=409)
        copy.barcode = barcode
        admin.barcode = barcode
    if payload.accession_number is not None:
        acc = payload.accession_number.strip() if payload.accession_number else None
        if acc:
            other = await LibraryBookCopyRecord.find_one(Eq(LibraryBookCopyRecord.tenant_id, tenant_id), Eq(LibraryBookCopyRecord.accession_number, acc))
            if other and other.copy_id != copy.copy_id:
                raise AppError(code="CONFLICT", message="accession_number exists", status_code=409)
        admin.accession_number = acc
    if payload.shelf_location_code is not None:
        shelf = payload.shelf_location_code.strip().upper() if payload.shelf_location_code else None
        await _assert_shelf(tenant_id, copy.branch_code or branch.branch_code, shelf)
        copy.shelf_location_code = shelf
        admin.shelf_location_code = shelf
    if payload.condition is not None:
        copy.condition = payload.condition
    if payload.status is not None:
        copy.status = payload.status
    if payload.notes is not None:
        copy.notes = payload.notes
    copy.version += 1
    copy.updated_by = scope.user_id
    copy.updated_at = utcnow()
    admin.updated_by = scope.user_id
    admin.updated_at = utcnow()
    await copy.save()
    await admin.save()
    await _history(
        tenant_id,
        copy_id=copy.copy_id,
        branch_code=copy.branch_code,
        event_type="copy_updated",
        note=None,
        metadata=payload.model_dump(exclude_unset=True, mode="json"),
        actor_id=scope.user_id,
    )
    return _to_read(copy, admin)


async def transfer_copy(scope: AccessScope, copy_id: str, payload: CopyTransferRequest) -> CopyInventoryRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    copy, admin = await _load_pair(tenant_id, copy_id.strip().upper())
    from_key = copy.branch_code or admin.branch_code
    if not from_key:
        raise AppError(code="VALIDATION_ERROR", message="Copy has no source branch", status_code=422)
    from_branch = await _assert_branch(tenant_id, from_key)
    to_branch = await _assert_branch(tenant_id, payload.to_branch_code)
    from_lib = await _library_for_branch(tenant_id, from_branch)
    await require_inventory_manage(scope, branch_code=from_branch.branch_code, library_code=from_lib)
    to_lib = await _library_for_branch(tenant_id, to_branch)
    await require_inventory_manage(scope, branch_code=to_branch.branch_code, library_code=to_lib)
    await _assert_version(copy, payload.expected_version)
    assert_transferable_status(copy.status)
    if payload.shelf_location_code:
        await _assert_shelf(tenant_id, to_branch.branch_code, payload.shelf_location_code)
    shelf = payload.shelf_location_code.strip().upper() if payload.shelf_location_code else None
    prev = copy.branch_code
    copy.branch_code = to_branch.branch_code
    copy.shelf_location_code = shelf
    copy.version += 1
    copy.updated_by = scope.user_id
    copy.updated_at = utcnow()
    admin.branch_code = to_branch.branch_code
    admin.shelf_location_code = shelf
    admin.updated_by = scope.user_id
    admin.updated_at = utcnow()
    await copy.save()
    await admin.save()
    await _history(
        tenant_id,
        copy_id=copy.copy_id,
        branch_code=to_branch.branch_code,
        event_type="branch_transfer",
        note=payload.reason,
        metadata={"from_branch": prev, "to_branch": to_branch.branch_code},
        actor_id=scope.user_id,
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_inventory.transfer",
        module="library_inventory",
        resource_type="copy",
        resource_id=copy.copy_id,
        metadata={"from_branch": prev, "to_branch": to_branch.branch_code},
    )
    return _to_read(copy, admin)


async def apply_adjustment(scope: AccessScope, payload: InventoryAdjustmentRequest) -> CopyInventoryRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    copy, admin = await _load_pair(tenant_id, payload.copy_id.strip().upper())
    branch_key = copy.branch_code or admin.branch_code
    if not branch_key:
        raise AppError(code="VALIDATION_ERROR", message="Copy has no branch assignment", status_code=422)
    branch = await _assert_branch(tenant_id, branch_key)
    lib = await _library_for_branch(tenant_id, branch)
    await require_inventory_manage(scope, branch_code=branch.branch_code, library_code=lib)
    await _assert_version(copy, payload.expected_version)
    prev_status = copy.status
    prev_condition = copy.condition
    if payload.new_status is not None:
        copy.status = payload.new_status
    if payload.new_condition is not None:
        copy.condition = payload.new_condition
    copy.version += 1
    copy.updated_by = scope.user_id
    copy.updated_at = utcnow()
    await copy.save()
    adjustment_id = f"adj_{uuid4().hex[:10]}"
    await LibraryInventoryAdjustment(
        tenant_id=tenant_id,
        adjustment_id=adjustment_id,
        copy_id=copy.copy_id,
        branch_code=copy.branch_code,
        adjustment_type=payload.adjustment_type,
        previous_status=prev_status,
        new_status=copy.status,
        previous_condition=prev_condition,
        new_condition=copy.condition,
        reason=payload.reason.strip(),
        actor_id=scope.user_id,
    ).insert()
    await _history(
        tenant_id,
        copy_id=copy.copy_id,
        branch_code=copy.branch_code,
        event_type="inventory_adjustment",
        note=payload.reason,
        metadata={"adjustment_id": adjustment_id, "type": payload.adjustment_type.value},
        actor_id=scope.user_id,
    )
    await append_institution_audit(
        tenant_id,
        actor_id=scope.user_id,
        action="library_inventory.adjust",
        module="library_inventory",
        resource_type="copy",
        resource_id=copy.copy_id,
        metadata={"adjustment_id": adjustment_id},
    )
    return _to_read(copy, admin)


async def find_duplicates(scope: AccessScope) -> list[CopyDuplicateMatch]:
    tenant_id = await require_inventory_read(scope)
    collection = LibraryBookCopyRecord.get_motor_collection()
    matches: list[CopyDuplicateMatch] = []
    for field in ("barcode", "accession_number"):
        pipeline = [
            {"$match": {"tenant_id": tenant_id, field: {"$exists": True, "$ne": None}}},
            {"$group": {"_id": f"${field}", "count": {"$sum": 1}, "copy_ids": {"$push": "$copy_id"}}},
            {"$match": {"count": {"$gt": 1}}},
        ]
        async for row in collection.aggregate(pipeline):
            matches.append(CopyDuplicateMatch(field=field, value=row["_id"], copy_ids=row["copy_ids"]))
    return matches


async def list_missing_copies(scope: AccessScope, *, branch_code: str | None = None) -> list[MissingCopySummary]:
    tenant_id = await require_inventory_read(scope)
    filters: dict[str, Any] = {
        "tenant_id": tenant_id,
        "status": LibraryCopyStatus.LOST.value,
    }
    if branch_code:
        filters["branch_code"] = _norm_branch(branch_code)
    rows = await LibraryCopy.find(filters).sort("copy_id").to_list()
    return [
        MissingCopySummary(copy_id=r.copy_id, book_id=r.book_id, branch_code=r.branch_code, status=r.status)
        for r in rows
    ]


async def start_stock_verification(scope: AccessScope, payload: StockVerificationCreate) -> StockVerificationRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    branch = await _assert_branch(tenant_id, payload.branch_code)
    lib = await _library_for_branch(tenant_id, branch)
    await require_inventory_manage(scope, branch_code=branch.branch_code, library_code=lib)
    if await LibraryStockVerification.find_one(
        Eq(LibraryStockVerification.tenant_id, tenant_id),
        Eq(LibraryStockVerification.verification_id, payload.verification_id),
    ):
        raise AppError(code="CONFLICT", message="verification_id exists", status_code=409)
    expected = await LibraryCopy.find(
        {"tenant_id": tenant_id, "branch_code": branch.branch_code},
    ).count()
    doc = LibraryStockVerification(
        tenant_id=tenant_id,
        verification_id=payload.verification_id.strip(),
        branch_code=branch.branch_code,
        expected_count=expected,
        note=payload.note,
        actor_id=scope.user_id,
    )
    await doc.insert()
    return _verification_read(doc)


def _verification_read(doc: LibraryStockVerification) -> StockVerificationRead:
    return StockVerificationRead(
        verification_id=doc.verification_id,
        branch_code=doc.branch_code,
        status=doc.status,
        expected_count=doc.expected_count,
        scanned_count=doc.scanned_count,
        missing_count=doc.missing_count,
        unexpected_count=doc.unexpected_count,
        created_at=doc.created_at,
        completed_at=doc.completed_at,
    )


async def scan_stock_verification(scope: AccessScope, verification_id: str, payload: StockVerificationScan) -> StockVerificationRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    session = await LibraryStockVerification.find_one(
        Eq(LibraryStockVerification.tenant_id, tenant_id),
        Eq(LibraryStockVerification.verification_id, verification_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Verification session not found", status_code=404)
    if session.status != StockVerificationStatus.OPEN:
        raise AppError(code="CONFLICT", message="Verification session is closed", status_code=409)
    branch = await _assert_branch(tenant_id, session.branch_code)
    lib = await _library_for_branch(tenant_id, branch)
    await require_inventory_manage(scope, branch_code=branch.branch_code, library_code=lib)
    copy: LibraryCopy | None = None
    if payload.copy_id:
        copy = await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.copy_id, payload.copy_id.strip().upper()))
    elif payload.barcode:
        barcode = normalize_barcode(payload.barcode)
        copy = await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.barcode, barcode))
    else:
        raise AppError(code="VALIDATION_ERROR", message="copy_id or barcode required", status_code=422)
    if copy is None:
        raise AppError(code="NOT_FOUND", message="Copy not found", status_code=404)
    outcome = (
        StockVerificationItemOutcome.FOUND
        if copy.branch_code == session.branch_code
        else StockVerificationItemOutcome.UNEXPECTED
    )
    existing = await LibraryStockVerificationItem.find_one(
        Eq(LibraryStockVerificationItem.tenant_id, tenant_id),
        Eq(LibraryStockVerificationItem.verification_id, verification_id),
        Eq(LibraryStockVerificationItem.copy_id, copy.copy_id),
    )
    if existing is None:
        await LibraryStockVerificationItem(
            tenant_id=tenant_id,
            verification_id=verification_id,
            copy_id=copy.copy_id,
            outcome=outcome,
        ).insert()
        session.scanned_count += 1
        if outcome == StockVerificationItemOutcome.UNEXPECTED:
            session.unexpected_count += 1
        await session.save()
    return _verification_read(session)


async def complete_stock_verification(scope: AccessScope, verification_id: str) -> StockVerificationRead:
    tenant_id = scope.tenant_id
    assert tenant_id is not None
    session = await LibraryStockVerification.find_one(
        Eq(LibraryStockVerification.tenant_id, tenant_id),
        Eq(LibraryStockVerification.verification_id, verification_id),
    )
    if session is None:
        raise AppError(code="NOT_FOUND", message="Verification session not found", status_code=404)
    branch = await _assert_branch(tenant_id, session.branch_code)
    lib = await _library_for_branch(tenant_id, branch)
    await require_inventory_manage(scope, branch_code=branch.branch_code, library_code=lib)
    if session.status != StockVerificationStatus.OPEN:
        raise AppError(code="CONFLICT", message="Verification already completed", status_code=409)
    scanned_ids = {
        row.copy_id
        for row in await LibraryStockVerificationItem.find(
            Eq(LibraryStockVerificationItem.tenant_id, tenant_id),
            Eq(LibraryStockVerificationItem.verification_id, verification_id),
            Eq(LibraryStockVerificationItem.outcome, StockVerificationItemOutcome.FOUND),
        ).to_list()
    }
    branch_copies = await LibraryCopy.find({"tenant_id": tenant_id, "branch_code": session.branch_code}).to_list()
    missing = [c.copy_id for c in branch_copies if c.copy_id not in scanned_ids]
    session.missing_count = len(missing)
    session.status = StockVerificationStatus.COMPLETED
    session.completed_at = utcnow()
    await session.save()
    for copy_id in missing:
        await LibraryStockVerificationItem(
            tenant_id=tenant_id,
            verification_id=verification_id,
            copy_id=copy_id,
            outcome=StockVerificationItemOutcome.MISSING,
        ).insert()
    await _history(
        tenant_id,
        copy_id=None,
        branch_code=session.branch_code,
        event_type="stock_verification_completed",
        note=f"Missing {len(missing)} copies",
        metadata={"verification_id": verification_id, "missing_copy_ids": missing},
        actor_id=scope.user_id,
    )
    return _verification_read(session)


async def copy_inventory_history(
    scope: AccessScope,
    copy_id: str,
    pagination: Pagination,
) -> Page[InventoryHistoryRead]:
    tenant_id = await require_inventory_read(scope)
    copy_id = copy_id.strip().upper()
    if await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.copy_id, copy_id)) is None:
        raise AppError(code="NOT_FOUND", message="Copy not found", status_code=404)
    query = LibraryInventoryHistory.find(
        Eq(LibraryInventoryHistory.tenant_id, tenant_id),
        Eq(LibraryInventoryHistory.copy_id, copy_id),
    ).sort("-created_at")
    total = await query.count()
    rows = await query.skip(pagination.offset).limit(pagination.limit).to_list()
    items = [
        InventoryHistoryRead(
            event_type=r.event_type,
            branch_code=r.branch_code,
            copy_id=r.copy_id,
            note=r.note,
            metadata=dict(r.metadata or {}),
            actor_id=str(r.actor_id) if r.actor_id else None,
            created_at=r.created_at,
        )
        for r in rows
    ]
    return Page(items=items, total=total, limit=pagination.limit, offset=pagination.offset)