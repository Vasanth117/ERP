"""Book copy inventory management tests."""

from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.library.catalogue_schemas import CatalogueRecordCreate
from app.modules.library.catalogue_service import create_catalogue_record
from app.modules.library.facility_schemas import InstitutionLibraryCreate, LibraryBranchCreate
from app.modules.library.facility_service import create_branch_facility, create_library
from app.modules.library.inventory_enums import InventoryAdjustmentType
from app.modules.library.inventory_schemas import (
    CopyRegisterRequest,
    CopyTransferRequest,
    CopyUpdateRequest,
    InventoryAdjustmentRequest,
    StockVerificationCreate,
    StockVerificationScan,
)
from app.modules.library.inventory_service import (
    apply_adjustment,
    complete_stock_verification,
    get_copy,
    register_copy,
    scan_stock_verification,
    start_stock_verification,
    transfer_copy,
    update_copy,
)
from app.modules.library.inventory_validation import normalize_barcode
from app.modules.library.library_enums import LibraryCopyCondition, LibraryCopyStatus
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


async def _seed_tenant_with_book(suffix: str) -> tuple[User, AccessScope, str, str, str]:
    tenant = Tenant(name=f"Inv {suffix}", code=f"inv_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+inv+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = _scope(admin, Role.COLLEGE_ADMIN)
    lib = f"L{suffix}"
    branch_a = f"BA{suffix}"
    branch_b = f"BB{suffix}"
    await create_library(scope, InstitutionLibraryCreate(library_code=lib, name="Central"))
    await create_branch_facility(scope, LibraryBranchCreate(library_code=lib, branch_code=branch_a, name="Branch A"))
    await create_branch_facility(scope, LibraryBranchCreate(library_code=lib, branch_code=branch_b, name="Branch B"))
    book_id = f"B-{suffix}"
    await create_catalogue_record(scope, CatalogueRecordCreate(book_id=book_id, title="Physics", authors=["Author"]))
    return admin, scope, book_id, branch_a, branch_b


@pytest.mark.anyio
async def test_register_copy_and_duplicate_barcode(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, book_id, branch_a, _ = await _seed_tenant_with_book(suffix)
    barcode = normalize_barcode(f"INV-{suffix}")
    row = await register_copy(
        scope,
        CopyRegisterRequest(book_id=book_id, branch_code=branch_a, barcode=barcode, accession_number=f"ACC-{suffix}"),
    )
    assert row.copy_id.startswith("CPY-")
    assert row.barcode == barcode
    with pytest.raises(AppError) as exc:
        await register_copy(
            scope,
            CopyRegisterRequest(book_id=book_id, branch_code=branch_a, barcode=barcode),
        )
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_invalid_catalogue_reference(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, _, branch_a, _ = await _seed_tenant_with_book(suffix)
    with pytest.raises(AppError) as exc:
        await register_copy(
            scope,
            CopyRegisterRequest(book_id="NO-SUCH", branch_code=branch_a, barcode=f"X-{suffix}12"),
        )
    assert exc.value.status_code == 422


@pytest.mark.anyio
async def test_transfer_and_concurrent_version(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, book_id, branch_a, branch_b = await _seed_tenant_with_book(suffix)
    created = await register_copy(
        scope,
        CopyRegisterRequest(book_id=book_id, branch_code=branch_a, barcode=f"TR-{suffix}1234"),
    )
    transferred = await transfer_copy(
        scope,
        created.copy_id,
        CopyTransferRequest(to_branch_code=branch_b, reason="Rebalance", expected_version=created.version),
    )
    assert transferred.branch_code == branch_b.upper()
    with pytest.raises(AppError) as exc:
        await update_copy(
            scope,
            created.copy_id,
            CopyUpdateRequest(condition=LibraryCopyCondition.FAIR, expected_version=created.version),
        )
    assert exc.value.status_code == 409


@pytest.mark.anyio
async def test_adjustment_status_change(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, book_id, branch_a, _ = await _seed_tenant_with_book(suffix)
    created = await register_copy(
        scope,
        CopyRegisterRequest(book_id=book_id, branch_code=branch_a, barcode=f"ADJ-{suffix}1234"),
    )
    updated = await apply_adjustment(
        scope,
        InventoryAdjustmentRequest(
            copy_id=created.copy_id,
            adjustment_type=InventoryAdjustmentType.STATUS_CHANGE,
            new_status=LibraryCopyStatus.DAMAGED,
            reason="Cover torn",
            expected_version=created.version,
        ),
    )
    assert updated.status == LibraryCopyStatus.DAMAGED


@pytest.mark.anyio
async def test_stock_verification(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope, book_id, branch_a, _ = await _seed_tenant_with_book(suffix)
    copy_a = await register_copy(
        scope,
        CopyRegisterRequest(book_id=book_id, branch_code=branch_a, barcode=f"V1-{suffix}1234"),
    )
    await register_copy(
        scope,
        CopyRegisterRequest(book_id=book_id, branch_code=branch_a, barcode=f"V2-{suffix}5678"),
    )
    session = await start_stock_verification(
        scope,
        StockVerificationCreate(verification_id=f"ver_{suffix}", branch_code=branch_a),
    )
    assert session.expected_count == 2
    scanned = await scan_stock_verification(scope, session.verification_id, StockVerificationScan(copy_id=copy_a.copy_id))
    assert scanned.scanned_count == 1
    done = await complete_stock_verification(scope, session.verification_id)
    assert done.missing_count == 1
    assert done.status.value == "completed"


@pytest.mark.anyio
async def test_cross_tenant_isolation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, scope_a, book_id, branch_a, _ = await _seed_tenant_with_book(suffix)
    created = await register_copy(
        scope_a,
        CopyRegisterRequest(book_id=book_id, branch_code=branch_a, barcode=f"ISO-{suffix}1234"),
    )
    tenant_b = Tenant(name=f"B {suffix}", code=f"b_{suffix}")
    await tenant_b.insert()
    admin_b = User(
        email=f"admin+b+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="B",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant_b.id,
    )
    await admin_b.insert()
    with pytest.raises(AppError) as exc:
        await get_copy(_scope(admin_b, Role.COLLEGE_ADMIN), created.copy_id)
    assert exc.value.status_code == 404