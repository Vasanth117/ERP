"""Library dashboard — metrics, filters, authorization."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import InstitutionAccountStatus, InstitutionUser
from app.common.time import utcnow
from app.modules.college_admin.library_admin_models import LibraryAcquisition
from app.modules.college_admin.library_admin_schemas import BookCopyCreate, CatalogueCreate, LibraryBranchCreate
from app.modules.college_admin.library_admin_service import add_book_copy, create_branch, set_membership, upsert_catalogue
from app.modules.library.dashboard_service import get_catalogue_stats, get_copy_stats, get_library_dashboard_overview, get_member_stats
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryCopyStatus, LibraryFineStatus, LibraryReservationStatus
from app.modules.library.library_models import (
    LibraryCirculation,
    LibraryCopy,
    LibraryDigitalResource,
    LibraryFine,
    LibraryReservation,
)
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


async def _seed_library(suffix: str) -> tuple[Tenant, User, AccessScope, User]:
    tenant = Tenant(name=f"LibDash {suffix}", code=f"libd_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+libdash+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"librarian+libdash+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Head Librarian",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"student+libdash+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student Member",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await librarian.insert()
    await student.insert()
    admin_scope = _scope(admin, Role.COLLEGE_ADMIN)
    await create_branch(admin_scope, LibraryBranchCreate(branch_code="MAIN", name="Main Library"))
    await upsert_catalogue(
        admin_scope,
        CatalogueCreate(book_id=f"B-{suffix}", title="Algorithms", category="CS", authors=["Knuth"]),
    )
    await add_book_copy(
        admin_scope,
        BookCopyCreate(copy_id=f"C-{suffix}-1", book_id=f"B-{suffix}", barcode=f"BC-{suffix}-1", branch_code="MAIN"),
    )
    await add_book_copy(
        admin_scope,
        BookCopyCreate(copy_id=f"C-{suffix}-2", book_id=f"B-{suffix}", barcode=f"BC-{suffix}-2", branch_code="MAIN"),
    )
    copy_two = await LibraryCopy.find_one({"copy_id": f"C-{suffix}-2"})
    assert copy_two is not None
    copy_two.status = LibraryCopyStatus.ISSUED
    await copy_two.save()
    await set_membership(admin_scope, str(student.id), branch_code="MAIN", eligible=True)
    await InstitutionUser(tenant_id=tenant.id, user_id=student.id, account_status=InstitutionAccountStatus.ACTIVE).insert()
    await LibraryReservation(
        tenant_id=tenant.id,
        reservation_id=f"res_{suffix}",
        student_user_id=student.id,
        book_id=f"B-{suffix}",
        title="Algorithms",
        status=LibraryReservationStatus.QUEUED,
    ).insert()
    await LibraryFine(
        tenant_id=tenant.id,
        fine_id=f"fine_{suffix}",
        student_user_id=student.id,
        amount=25.0,
        reason="Late",
        status=LibraryFineStatus.OPEN,
    ).insert()
    await LibraryDigitalResource(tenant_id=tenant.id, resource_id=f"d_{suffix}", title="E-Book", published=True).insert()
    await LibraryAcquisition(
        tenant_id=tenant.id,
        acquisition_id=f"acq_{suffix}",
        branch_code="MAIN",
        status="ordered",
        quantity=2,
    ).insert()
    await LibraryCirculation(
        tenant_id=tenant.id,
        circulation_id=f"circ_{suffix}",
        student_user_id=student.id,
        book_id=f"B-{suffix}",
        copy_id=f"C-{suffix}-2",
        title="Algorithms",
        issued_at=utcnow(),
        due_at=date.today() - timedelta(days=2),
        status=LibraryCirculationStatus.ACTIVE,
    ).insert()
    return tenant, librarian, _scope(librarian, Role.LIBRARIAN), student


@pytest.mark.anyio
async def test_library_dashboard_overview_metrics(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, librarian, scope, _ = await _seed_library(suffix)
    overview = await get_library_dashboard_overview(scope, librarian, branch_code="MAIN")
    assert overview.catalogue.total_titles == 1
    assert overview.copies.total_copies == 2
    assert overview.copies.available == 1
    assert overview.copies.issued == 1
    assert overview.copies.overdue_loans == 1
    assert overview.members.total == 1
    assert overview.members.active == 1
    assert overview.pending_reservations == 1
    assert overview.outstanding_fines.open_count == 1
    assert overview.outstanding_fines.total_amount == 25.0
    assert overview.digital.total == 1
    assert overview.acquisitions.pending_procurement_count >= 1
    assert any(a.code == "overdue_loans" for a in overview.alerts)


@pytest.mark.anyio
async def test_branch_filter_unknown_rejected(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, librarian, scope, _ = await _seed_library(suffix)
    with pytest.raises(AppError) as exc:
        await get_copy_stats(scope, branch_code="NOPE")
    assert exc.value.status_code == 422


@pytest.mark.anyio
async def test_empty_branch_inventory(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"LibEmpty {suffix}", code=f"libe_{suffix}")
    await tenant.insert()
    librarian = User(
        email=f"librarian+empty+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Librarian",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    await librarian.insert()
    scope = _scope(librarian, Role.LIBRARIAN)
    admin = User(
        email=f"admin+empty+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    admin_scope = _scope(admin, Role.COLLEGE_ADMIN)
    await create_branch(admin_scope, LibraryBranchCreate(branch_code="EMPTY", name="Empty Branch"))
    stats = await get_copy_stats(scope, branch_code="EMPTY")
    assert stats.total_copies == 0


@pytest.mark.anyio
async def test_student_cannot_access_dashboard(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, _, student = await _seed_library(suffix)
    student_scope = _scope(student, Role.STUDENT)
    with pytest.raises(AppError) as exc:
        await get_library_dashboard_overview(student_scope, student)
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_cross_tenant_isolation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant_a, librarian_a, scope_a, _ = await _seed_library(suffix)
    tenant_b = Tenant(name=f"Other {suffix}", code=f"other_{suffix}")
    await tenant_b.insert()
    librarian_b = User(
        email=f"librarian-b+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other Librarian",
        role=Role.LIBRARIAN,
        tenant_id=tenant_b.id,
    )
    await librarian_b.insert()
    scope_b = _scope(librarian_b, Role.LIBRARIAN)
    stats_a = await get_catalogue_stats(scope_a)
    stats_b = await get_catalogue_stats(scope_b)
    assert stats_a.total_titles == 1
    assert stats_b.total_titles == 0
    assert str(tenant_a.id) != str(tenant_b.id)


@pytest.mark.anyio
async def test_college_admin_library_read_can_use_dashboard(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"LibAdmin {suffix}", code=f"libadm_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+libadm+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = _scope(admin, Role.COLLEGE_ADMIN)
    assert Permission.LIBRARY_ADMIN_READ in scope.effective_permissions
    members = await get_member_stats(scope)
    assert members.total == 0


@pytest.mark.anyio
async def test_member_suspended_count(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"LibSusp {suffix}", code=f"libsusp_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+susp+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"student+susp+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"librarian+susp+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Librarian",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await student.insert()
    await librarian.insert()
    admin_scope = _scope(admin, Role.COLLEGE_ADMIN)
    lib_scope = _scope(librarian, Role.LIBRARIAN)
    await set_membership(admin_scope, str(student.id), branch_code=None, eligible=True)
    await InstitutionUser(tenant_id=tenant.id, user_id=student.id, account_status=InstitutionAccountStatus.SUSPENDED).insert()
    stats = await get_member_stats(lib_scope)
    assert stats.suspended == 1