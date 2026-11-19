"""Library administration services."""

from datetime import date, timedelta
from uuid import uuid4

from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission
from app.authorization.policy import authorize
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.schemas import Page, Pagination
from app.common.time import utcnow
from app.core.exceptions import AppError
from app.modules.college_admin.library_admin_models import (
    LibraryAcquisition,
    LibraryBookCopyRecord,
    LibraryBorrowingPolicy,
    LibraryBranch,
    LibraryCatalogueEntry,
    LibraryCirculationRecord,
    LibraryInventoryHistory,
    LibraryMembershipReference,
)
from app.modules.college_admin.library_admin_schemas import (
    AcquisitionCreate,
    BookCopyCreate,
    BorrowingPolicyUpsert,
    CatalogueCreate,
    CirculationIssue,
    CirculationReturn,
    FineDecision,
    LibraryBranchCreate,
    ReservationFulfill,
)
from app.modules.college_admin.policy import require_college_tenant_scope
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryCopyStatus, LibraryFineStatus, LibraryReservationStatus
from app.modules.library.library_models import (
    LibraryCatalogItem,
    LibraryCirculation,
    LibraryCopy,
    LibraryFine,
    LibraryReservation,
)


def _require_branch(tenant_id: PydanticObjectId, branch_code: str | None) -> None:
    if branch_code is None:
        return
    # Branch scope validated when branch exists
    pass


async def _assert_branch(tenant_id: PydanticObjectId, branch_code: str | None) -> None:
    if not branch_code:
        return
    branch = await LibraryBranch.find_one(Eq(LibraryBranch.tenant_id, tenant_id), Eq(LibraryBranch.branch_code, branch_code.upper()))
    if branch is None:
        raise AppError(code="VALIDATION_ERROR", message="Unknown library branch", status_code=422)


async def create_branch(scope: AccessScope, payload: LibraryBranchCreate) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    code = payload.branch_code.upper()
    if await LibraryBranch.find_one(Eq(LibraryBranch.tenant_id, tenant_id), Eq(LibraryBranch.branch_code, code)):
        raise AppError(code="CONFLICT", message="Branch code exists", status_code=409)
    campus_id = to_object_id(payload.campus_id, "campus_id") if payload.campus_id else None
    branch = LibraryBranch(tenant_id=tenant_id, branch_code=code, name=payload.name, campus_id=campus_id, address=payload.address)
    await branch.insert()
    return {"branch_code": code}


async def upsert_catalogue(scope: AccessScope, payload: CatalogueCreate) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    await _assert_branch(tenant_id, payload.branch_code)
    book_id = payload.book_id.strip()
    item = await LibraryCatalogItem.find_one(Eq(LibraryCatalogItem.tenant_id, tenant_id), Eq(LibraryCatalogItem.book_id, book_id))
    if item is None:
        item = LibraryCatalogItem(
            tenant_id=tenant_id,
            book_id=book_id,
            title=payload.title,
            authors=payload.authors,
            isbn=payload.isbn,
            category=payload.category,
        )
        await item.insert()
    else:
        item.title = payload.title
        item.authors = payload.authors
        item.isbn = payload.isbn
        item.category = payload.category
        item.updated_at = utcnow()
        await item.save()
    entry = await LibraryCatalogueEntry.find_one(Eq(LibraryCatalogueEntry.tenant_id, tenant_id), Eq(LibraryCatalogueEntry.book_id, book_id))
    if entry is None:
        entry = LibraryCatalogueEntry(
            tenant_id=tenant_id,
            book_id=book_id,
            branch_code=payload.branch_code.upper() if payload.branch_code else None,
            catalog_item_id=item.id,
            updated_by=scope.user_id,
        )
        await entry.insert()
    else:
        entry.branch_code = payload.branch_code.upper() if payload.branch_code else entry.branch_code
        entry.catalog_item_id = item.id
        entry.updated_by = scope.user_id
        entry.updated_at = utcnow()
        await entry.save()
    return {"book_id": book_id}


async def add_book_copy(scope: AccessScope, payload: BookCopyCreate) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    await _assert_branch(tenant_id, payload.branch_code)
    copy_id = payload.copy_id.strip()
    if await LibraryBookCopyRecord.find_one(Eq(LibraryBookCopyRecord.tenant_id, tenant_id), Eq(LibraryBookCopyRecord.copy_id, copy_id)):
        raise AppError(code="CONFLICT", message="Copy id exists", status_code=409)
    if payload.accession_number:
        if await LibraryBookCopyRecord.find_one(
            Eq(LibraryBookCopyRecord.tenant_id, tenant_id),
            Eq(LibraryBookCopyRecord.accession_number, payload.accession_number),
        ):
            raise AppError(code="CONFLICT", message="Accession number exists", status_code=409)
    copy = await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant_id), Eq(LibraryCopy.copy_id, copy_id))
    if copy is None:
        branch = payload.branch_code.upper() if payload.branch_code else None
        copy = LibraryCopy(
            tenant_id=tenant_id,
            copy_id=copy_id,
            book_id=payload.book_id,
            barcode=payload.barcode.strip().upper(),
            branch_code=branch,
        )
        await copy.insert()
    admin = LibraryBookCopyRecord(
        tenant_id=tenant_id,
        copy_id=copy_id,
        book_id=payload.book_id,
        barcode=payload.barcode,
        accession_number=payload.accession_number,
        branch_code=payload.branch_code.upper() if payload.branch_code else None,
        authoritative_copy_id=copy.id,
    )
    await admin.insert()
    await LibraryInventoryHistory(
        tenant_id=tenant_id,
        branch_code=admin.branch_code,
        copy_id=copy_id,
        event_type="copy_added",
        actor_id=scope.user_id,
    ).insert()
    return {"copy_id": copy_id}


async def upsert_borrowing_policy(scope: AccessScope, payload: BorrowingPolicyUpsert) -> dict:
    from app.modules.library.settings_service import college_admin_upsert_borrowing_policy

    return await college_admin_upsert_borrowing_policy(scope, payload)


async def set_membership(scope: AccessScope, member_user_id: str, *, branch_code: str | None, eligible: bool) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    tenant_id = require_college_tenant_scope(scope)
    await _assert_branch(tenant_id, branch_code)
    uid = to_object_id(member_user_id, "member_user_id")
    doc = await LibraryMembershipReference.find_one(Eq(LibraryMembershipReference.tenant_id, tenant_id), Eq(LibraryMembershipReference.member_user_id, uid))
    if doc is None:
        from uuid import uuid4

        doc = LibraryMembershipReference(
            tenant_id=tenant_id,
            membership_number=f"MEM-{uuid4().hex[:10].upper()}",
            member_user_id=uid,
            branch_code=branch_code.upper() if branch_code else None,
            eligible=eligible,
            updated_by=scope.user_id,
        )
        await doc.insert()
    else:
        doc.branch_code = branch_code.upper() if branch_code else doc.branch_code
        doc.eligible = eligible
        doc.updated_by = scope.user_id
        doc.updated_at = utcnow()
        await doc.save()
    return {"member_user_id": member_user_id, "eligible": eligible, "membership_number": doc.membership_number}


async def issue_book(scope: AccessScope, payload: CirculationIssue) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    from app.modules.library.circulation_schemas import IssueLoanRequest
    from app.modules.library.circulation_service import issue_loan

    result = await issue_loan(
        scope,
        IssueLoanRequest(
            member_user_id=payload.student_user_id,
            copy_id=payload.copy_id,
            branch_code=payload.branch_code,
        ),
    )
    return {"circulation_id": result.circulation_id, "due_at": result.due_at.isoformat()}


async def return_book(scope: AccessScope, payload: CirculationReturn) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    from app.modules.library.circulation_schemas import ReturnLoanRequest
    from app.modules.library.circulation_service import return_loan

    result = await return_loan(scope, payload.circulation_id, ReturnLoanRequest())
    return {"circulation_id": result.circulation_id, "status": result.status.value}


async def list_circulation(scope: AccessScope, pagination: Pagination, *, branch_code: str | None = None) -> Page[dict]:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    from app.modules.library.circulation_service import search_loans

    page = await search_loans(scope, pagination, branch_code=branch_code)
    return Page(
        items=[
            {
                "circulation_id": r.circulation_id,
                "book_id": r.book_id,
                "copy_id": r.copy_id,
                "status": r.status.value,
                "due_at": r.due_at.isoformat(),
            }
            for r in page.items
        ],
        total=page.total,
        limit=page.limit,
        offset=page.offset,
    )


async def fulfill_reservation(scope: AccessScope, payload: ReservationFulfill) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    from app.modules.library.reservation_service import fulfill_reservation_record

    result = await fulfill_reservation_record(scope, payload.reservation_id)
    return {"reservation_id": result.reservation_id, "status": result.status.value}


async def decide_fine(scope: AccessScope, payload: FineDecision) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    from app.modules.library.fine_service import college_admin_decide_fine

    return await college_admin_decide_fine(scope, payload.fine_id, payload.decision, payload.note)


async def create_acquisition(scope: AccessScope, payload: AcquisitionCreate) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    from app.modules.library.acquisition_enums import LibraryAcquisitionType
    from app.modules.library.acquisition_schemas import AcquisitionCreateRequest
    from app.modules.library.acquisition_service import create_acquisition as create_library_acquisition

    title = payload.metadata.get("title") if payload.metadata else None
    if not title:
        title = payload.book_id or "Library acquisition"
    result = await create_library_acquisition(
        scope,
        AcquisitionCreateRequest(
            acquisition_id=payload.acquisition_id,
            request_type=LibraryAcquisitionType.PURCHASE,
            title=str(title),
            book_id=payload.book_id,
            branch_code=payload.branch_code,
            quantity=payload.quantity,
        ),
    )
    if payload.vendor:
        tenant_id = require_college_tenant_scope(scope)
        doc = await LibraryAcquisition.find_one(
            Eq(LibraryAcquisition.tenant_id, tenant_id),
            Eq(LibraryAcquisition.acquisition_id, result.acquisition_id),
        )
        if doc:
            doc.vendor = payload.vendor
            doc.status = "ordered"
            await doc.save()
    return {"acquisition_id": result.acquisition_id, "status": result.status}


async def add_digital_resource(scope: AccessScope, *, resource_id: str, title: str, url: str | None) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_MANAGE)
    from app.modules.library.digital_service import college_admin_add_digital_resource

    return await college_admin_add_digital_resource(scope, resource_id=resource_id, title=title, url=url)


async def library_report(scope: AccessScope, *, branch_code: str | None = None) -> dict:
    authorize(scope, Permission.LIBRARY_ADMIN_READ)
    from app.modules.library.report_service import library_legacy_summary

    return await library_legacy_summary(scope, branch_code=branch_code)
