"""Library audit history and inventory control."""

from datetime import date
from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.library.audit_enums import LibraryAuditDomain
from app.modules.library.audit_models import LibraryAuditEvent
from app.modules.library.audit_recorder import record_library_audit
from app.modules.library.audit_service import resource_timeline, search_audit_events
from app.modules.library.report_schemas import LibraryReportFilters
from app.modules.library.report_service import get_report_snapshot
from app.modules.library.audit_schemas import LibraryAuditSearch, StockAdjustmentDecision, StockAdjustmentPropose
from app.modules.library.catalogue_schemas import CatalogueRecordCreate
from app.modules.library.catalogue_service import create_catalogue_record
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.library.facility_enums import LibraryStaffRole
from app.modules.library.facility_schemas import InstitutionLibraryCreate, LibraryBranchCreate, LibraryStaffAssignmentCreate
from app.modules.library.facility_service import create_branch_facility, create_library, create_staff_assignment
from app.modules.library.inventory_enums import InventoryAdjustmentType
from app.modules.library.inventory_schemas import CopyRegisterRequest, StockVerificationCreate, StockVerificationScan
from app.modules.library.inventory_control_service import (
    approve_stock_adjustment,
    list_discrepancies,
    propose_stock_adjustment,
    reject_stock_adjustment,
)
from app.modules.library.inventory_service import (
    complete_stock_verification,
    get_copy,
    register_copy,
    scan_stock_verification,
    start_stock_verification,
)
from app.modules.library.library_enums import LibraryCopyStatus
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


async def _seed(suffix: str) -> tuple[AccessScope, AccessScope, str, str, str]:
    tenant = Tenant(name=f"Aud {suffix}", code=f"aud_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+aud+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"lib+aud+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Librarian",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await librarian.insert()
    await EmployeeRecord(
        tenant_id=tenant.id,
        user_id=librarian.id,
        employee_id=f"LIB-{suffix}",
        employment_status=FacultyEmploymentStatus.ACTIVE,
    ).insert()
    lib_scope = _scope(librarian, Role.LIBRARIAN)
    admin_scope = _scope(admin, Role.COLLEGE_ADMIN)
    lib = f"L{suffix}".upper()[:12]
    branch = "MAIN"
    await create_library(admin_scope, InstitutionLibraryCreate(library_code=lib, name="Central"))
    await create_branch_facility(admin_scope, LibraryBranchCreate(library_code=lib, branch_code=branch, name="Main"))
    await create_staff_assignment(
        admin_scope,
        LibraryStaffAssignmentCreate(
            assignment_id=f"asg_{suffix}",
            library_code=lib,
            branch_code=branch,
            employee_user_id=str(librarian.id),
            staff_role=LibraryStaffRole.CIRCULATION_DESK,
            assigned_on=date.today(),
        ),
    )
    book_id = f"B-{suffix}"
    await create_catalogue_record(lib_scope, CatalogueRecordCreate(book_id=book_id, title="Audit Book", authors=["A"]))
    return lib_scope, admin_scope, book_id, branch, suffix


@pytest.mark.anyio
async def test_record_and_search_audit_events(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, _, branch, _ = await _seed(suffix)
    tenant_id = lib_scope.tenant_id
    assert tenant_id is not None
    await record_library_audit(
        tenant_id,
        actor_id=lib_scope.user_id,
        domain=LibraryAuditDomain.CATALOGUE,
        action="library_catalogue.create",
        resource_type="book",
        resource_id="B-1",
        branch_code=branch,
        after_state={"title": "Sample"},
    )
    page = await search_audit_events(lib_scope, Pagination(limit=10, offset=0), LibraryAuditSearch(domain=LibraryAuditDomain.CATALOGUE))
    assert page.total >= 1
    assert page.items[0].branch_code == branch.upper()


@pytest.mark.anyio
async def test_verification_discrepancy_and_approval_workflow(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, admin_scope, book_id, branch, _ = await _seed(suffix)
    copy = await register_copy(
        lib_scope,
        CopyRegisterRequest(book_id=book_id, branch_code=branch, barcode=f"BC-{suffix}", copy_id=f"CPY{suffix}"),
    )
    vid = f"VER-{suffix}"
    await start_stock_verification(lib_scope, StockVerificationCreate(verification_id=vid, branch_code=branch))
    await complete_stock_verification(lib_scope, vid)
    page = await list_discrepancies(lib_scope, Pagination(limit=20, offset=0), verification_id=vid)
    assert page.total >= 1
    missing = [d for d in page.items if d.copy_id == copy.copy_id][0]
    assert missing.kind.value == "missing"
    row = await get_copy(lib_scope, copy.copy_id)
    req = await propose_stock_adjustment(
        lib_scope,
        StockAdjustmentPropose(
            copy_id=copy.copy_id,
            discrepancy_id=missing.discrepancy_id,
            adjustment_type=InventoryAdjustmentType.STATUS_CHANGE,
            proposed_status=LibraryCopyStatus.LOST,
            expected_version=row.version,
            reason="Stock audit missing copy",
        ),
    )
    with pytest.raises(AppError) as self_approve:
        await approve_stock_adjustment(lib_scope, req.request_id, StockAdjustmentDecision(decision_note="self"))
    assert self_approve.value.status_code == 403
    applied = await approve_stock_adjustment(admin_scope, req.request_id, StockAdjustmentDecision(decision_note="ok"))
    assert applied.status == "applied"
    updated = await get_copy(lib_scope, copy.copy_id)
    assert updated.status == LibraryCopyStatus.LOST
    timeline = await resource_timeline(lib_scope, "copy", copy.copy_id, Pagination(limit=50, offset=0))
    assert timeline.total >= 1


@pytest.mark.anyio
async def test_cross_tenant_audit_isolation(db_ready) -> None:
    suffix_a = uuid4().hex[:6]
    suffix_b = uuid4().hex[:6]
    lib_a, _, _, _, _ = await _seed(suffix_a)
    lib_b, _, _, _, _ = await _seed(suffix_b)
    assert lib_a.tenant_id is not None
    await record_library_audit(
        lib_a.tenant_id,
        actor_id=lib_a.user_id,
        domain=LibraryAuditDomain.INVENTORY,
        action="library_inventory.test",
        resource_type="copy",
        resource_id="X",
    )
    page = await search_audit_events(lib_b, Pagination(limit=50, offset=0), LibraryAuditSearch())
    ids = {item.event_id for item in page.items}
    foreign = await LibraryAuditEvent.find({"tenant_id": lib_a.tenant_id}).to_list()
    assert foreign
    assert foreign[0].event_id not in ids


@pytest.mark.anyio
async def test_librarian_cannot_approve_adjustment(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, admin_scope, book_id, branch, _ = await _seed(suffix)
    copy = await register_copy(
        lib_scope,
        CopyRegisterRequest(book_id=book_id, branch_code=branch, barcode=f"BC2-{suffix}", copy_id=f"CPY2{suffix}"),
    )
    row = await get_copy(lib_scope, copy.copy_id)
    req = await propose_stock_adjustment(
        lib_scope,
        StockAdjustmentPropose(
            copy_id=copy.copy_id,
            adjustment_type=InventoryAdjustmentType.WRITE_OFF,
            proposed_status=LibraryCopyStatus.LOST,
            expected_version=row.version,
            reason="Write-off proposal",
        ),
    )
    rejected = await reject_stock_adjustment(admin_scope, req.request_id, StockAdjustmentDecision(decision_note="not now"))
    assert rejected.status == "rejected"
    perms = permissions_for_role(Role.LIBRARIAN)
    assert Permission.LIBRARY_AUDIT_READ in perms
    assert Permission.LIBRARY_INVENTORY_APPROVE not in perms


@pytest.mark.anyio
async def test_stock_verification_scan_creates_audit_on_complete(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, book_id, branch, _ = await _seed(suffix)
    copy = await register_copy(
        lib_scope,
        CopyRegisterRequest(book_id=book_id, branch_code=branch, barcode=f"BC3-{suffix}", copy_id=f"CPY3{suffix}"),
    )
    vid = f"VER3-{suffix}"
    await start_stock_verification(lib_scope, StockVerificationCreate(verification_id=vid, branch_code=branch))
    await scan_stock_verification(lib_scope, vid, StockVerificationScan(copy_id=copy.copy_id))
    await complete_stock_verification(lib_scope, vid)
    page = await list_discrepancies(lib_scope, Pagination(limit=10, offset=0), verification_id=vid)
    assert page.total == 0


@pytest.mark.anyio
async def test_inventory_audit_report(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, book_id, branch, _ = await _seed(suffix)
    copy = await register_copy(
        lib_scope,
        CopyRegisterRequest(book_id=book_id, branch_code=branch, barcode=f"RPT-{suffix}", copy_id=f"CPYR{suffix}"),
    )
    vid = f"VER-RPT-{suffix}"
    await start_stock_verification(lib_scope, StockVerificationCreate(verification_id=vid, branch_code=branch))
    await complete_stock_verification(lib_scope, vid)
    snap = await get_report_snapshot(lib_scope, "inventory_audit", LibraryReportFilters(branch_code=branch))
    assert snap.row_count >= 1
    assert any(r.get("copy_id") == copy.copy_id for r in snap.rows if r.get("record_type") == "discrepancy")