"""Library acquisition and procurement tests."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.finance_ext_schemas import PurchaseOrderCreate, PurchaseRequestApprove, PurchaseRequestCreate, VendorUpsert
from app.modules.college_admin.finance_ext_service import approve_purchase_request, create_purchase_order, create_purchase_request, upsert_vendor
from app.modules.library.acquisition_enums import LibraryAcquisitionType
from app.modules.library.acquisition_schemas import (
    AcquisitionApprovalDecision,
    AcquisitionCreateRequest,
    CatalogueLinkRequest,
    ProcurementSyncRequest,
    QuotationCreateRequest,
    ReceiptRecordRequest,
)
from app.modules.library.acquisition_service import (
    add_quotation,
    create_acquisition,
    decide_acquisition_approval,
    record_receipt,
    select_quotation,
    submit_acquisition,
    sync_procurement_refs,
    link_catalogue,
    request_inventory_registration,
)
from app.modules.library.catalogue_service import create_catalogue_record
from app.modules.library.catalogue_schemas import CatalogueRecordCreate
from app.modules.tenants.models import Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    try:
        await connect_redis()
    except Exception:
        pass
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_redis()
    await close_mongo()


def _scope(user: User, role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )


async def _seed(suffix: str) -> tuple[AccessScope, AccessScope, User, User, str]:
    tenant = Tenant(name=f"Acq {suffix}", code=f"acq_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+acq+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"lib+acq+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Lib",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await librarian.insert()
    return _scope(admin, Role.COLLEGE_ADMIN), _scope(librarian, Role.LIBRARIAN), admin, librarian, suffix


@pytest.mark.anyio
async def test_acquisition_approval_and_duplicate(db_ready) -> None:
    suffix = uuid4().hex[:8]
    admin_scope, lib_scope, _, _, _ = await _seed(suffix)
    created = await create_acquisition(
        lib_scope,
        AcquisitionCreateRequest(title="New Atlas", request_type=LibraryAcquisitionType.SUGGESTION, quantity=2),
    )
    await submit_acquisition(lib_scope, created.acquisition_id)
    with pytest.raises(AppError) as self_appr:
        await decide_acquisition_approval(lib_scope, created.acquisition_id, AcquisitionApprovalDecision(approved=True))
    assert self_appr.value.status_code == 403
    approved = await decide_acquisition_approval(admin_scope, created.acquisition_id, AcquisitionApprovalDecision(approved=True))
    assert approved.approval_status == "approved"
    with pytest.raises(AppError) as dup:
        await create_acquisition(lib_scope, AcquisitionCreateRequest(acquisition_id=created.acquisition_id, title="Dup"))
    assert dup.value.status_code == 409


@pytest.mark.anyio
async def test_quotation_receive_partial_and_catalogue(db_ready) -> None:
    suffix = uuid4().hex[:8]
    admin_scope, lib_scope, admin, _, _ = await _seed(suffix)
    vid = f"ven_{suffix}"
    await upsert_vendor(admin_scope, admin, VendorUpsert(vendor_id=vid, name="Books Co"))
    acq = await create_acquisition(
        lib_scope,
        AcquisitionCreateRequest(title="Database Systems", vendor_id=vid, quantity=5),
    )
    await submit_acquisition(lib_scope, acq.acquisition_id)
    await decide_acquisition_approval(admin_scope, acq.acquisition_id, AcquisitionApprovalDecision(approved=True))
    q = await add_quotation(lib_scope, acq.acquisition_id, QuotationCreateRequest(vendor_id=vid, amount=1200))
    selected = await select_quotation(lib_scope, acq.acquisition_id, q["quotation_id"])
    assert selected.status == "ordered"
    partial = await record_receipt(lib_scope, acq.acquisition_id, ReceiptRecordRequest(quantity=3))
    assert partial.status == "partial_received"
    assert partial.quantity_received == 3
    with pytest.raises(AppError) as over:
        await record_receipt(lib_scope, acq.acquisition_id, ReceiptRecordRequest(quantity=3))
    assert over.value.status_code == 422
    final = await record_receipt(lib_scope, acq.acquisition_id, ReceiptRecordRequest(quantity=2))
    assert final.status == "received"
    book_id = f"B-{suffix}"
    await create_catalogue_record(lib_scope, CatalogueRecordCreate(book_id=book_id, title="Database Systems", authors=["Author"]))
    linked = await link_catalogue(lib_scope, acq.acquisition_id, CatalogueLinkRequest(book_id=book_id))
    assert linked.book_id == book_id
    reg = await request_inventory_registration(lib_scope, acq.acquisition_id)
    assert reg["registration_id"]


@pytest.mark.anyio
async def test_procurement_link_and_unauthorized(db_ready) -> None:
    suffix = uuid4().hex[:8]
    admin_scope, lib_scope, admin, _, _ = await _seed(suffix)
    vid = f"ven_{suffix}"
    await upsert_vendor(admin_scope, admin, VendorUpsert(vendor_id=vid, name="Vendor"))
    acq = await create_acquisition(lib_scope, AcquisitionCreateRequest(title="Procurement Book", vendor_id=vid))
    await submit_acquisition(lib_scope, acq.acquisition_id)
    await decide_acquisition_approval(admin_scope, acq.acquisition_id, AcquisitionApprovalDecision(approved=True))
    rid = f"pr_{suffix}"
    await create_purchase_request(
        admin_scope,
        admin,
        PurchaseRequestCreate(request_id=rid, description="Library books", estimated_amount=500, vendor_id=vid, submit=True),
    )
    await approve_purchase_request(admin_scope, admin, rid, PurchaseRequestApprove(approved=True))
    oid = f"po_{suffix}"
    await create_purchase_order(admin_scope, admin, PurchaseOrderCreate(order_id=oid, request_id=rid, vendor_id=vid, total_amount=480))
    with pytest.raises(AppError) as denied:
        await sync_procurement_refs(lib_scope, acq.acquisition_id, ProcurementSyncRequest(purchase_request_id=rid, purchase_order_id=oid))
    assert denied.value.status_code == 403
    linked = await sync_procurement_refs(
        admin_scope,
        acq.acquisition_id,
        ProcurementSyncRequest(purchase_request_id=rid, purchase_order_id=oid),
    )
    assert linked.purchase_order_id == oid