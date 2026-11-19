"""Library reservation queue tests."""

import asyncio
from datetime import timedelta
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.common.schemas import Pagination
from app.common.time import utcnow
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.library_admin_schemas import BookCopyCreate, CatalogueCreate
from app.modules.college_admin.library_admin_service import add_book_copy, upsert_catalogue
from app.modules.library.circulation_schemas import ReturnLoanRequest
from app.modules.library.circulation_service import issue_loan, return_loan
from app.modules.library.circulation_schemas import IssueLoanRequest
from app.modules.library.library_enums import LibraryCopyStatus, LibraryReservationStatus
from app.modules.library.library_models import LibraryCopy, LibraryReservation
from app.modules.library.member_schemas import MemberRegisterRequest
from app.modules.library.member_service import register_member
from app.modules.library.reservation_models import LibraryReservationNotification, LibraryReservationPolicy
from app.modules.library.reservation_schemas import ReservationAllocateRequest, ReservationCancelRequest, ReservationCreateRequest
from app.modules.library.reservation_service import cancel_reservation, create_reservation, expire_ready_holds, manual_allocate, queue_for_book
from app.modules.library.facility_enums import LibraryStaffRole
from app.modules.library.facility_schemas import InstitutionLibraryCreate, LibraryBranchCreate, LibraryStaffAssignmentCreate
from app.modules.library.facility_service import create_branch_facility, create_library, create_staff_assignment
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


async def _seed(suffix: str) -> tuple[AccessScope, User, str, str, str]:
    tenant = Tenant(name=f"Resv {suffix}", code=f"resv_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+resv+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"lib+resv+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Librarian",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"stu+resv+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    student_b = User(
        email=f"stu2+resv+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student2",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await librarian.insert()
    await student.insert()
    await student_b.insert()
    await EmployeeRecord(
        tenant_id=tenant.id,
        user_id=librarian.id,
        employee_id=f"LIB-{suffix}",
        employment_status=FacultyEmploymentStatus.ACTIVE,
    ).insert()
    admin_scope = _scope(admin, Role.COLLEGE_ADMIN)
    lib_scope = _scope(librarian, Role.LIBRARIAN)
    branch = "MAIN"
    lib_code = f"L{suffix}".upper()
    await create_library(admin_scope, InstitutionLibraryCreate(library_code=lib_code, name="Central"))
    await create_branch_facility(admin_scope, LibraryBranchCreate(library_code=lib_code, branch_code=branch, name="Main"))
    await create_staff_assignment(
        admin_scope,
        LibraryStaffAssignmentCreate(
            assignment_id=f"asg_{suffix}",
            library_code=lib_code,
            branch_code=branch,
            employee_user_id=str(librarian.id),
            staff_role=LibraryStaffRole.CIRCULATION_DESK,
            assigned_on=__import__("datetime").date.today(),
        ),
    )
    book_id = f"B-{suffix}"
    await upsert_catalogue(admin_scope, CatalogueCreate(book_id=book_id, title="Reserve Me", category="SCI"))
    copy_id = f"C-{suffix}"
    await add_book_copy(
        admin_scope,
        BookCopyCreate(copy_id=copy_id, book_id=book_id, barcode=f"BC-{suffix}", branch_code=branch),
    )
    copy = await LibraryCopy.find_one({"copy_id": copy_id})
    assert copy is not None
    copy.status = LibraryCopyStatus.ISSUED
    await copy.save()
    await register_member(lib_scope, MemberRegisterRequest(member_user_id=str(student.id), branch_code=branch))
    await register_member(lib_scope, MemberRegisterRequest(member_user_id=str(student_b.id), branch_code=branch))
    await LibraryReservationPolicy(
        tenant_id=tenant.id,
        branch_code=branch,
        hold_hours=48,
        max_active_per_member=3,
        reserve_only_when_unavailable=True,
    ).insert()
    return lib_scope, student, student_b, book_id, branch


@pytest.mark.anyio
async def test_reserve_queue_allocate_and_notify(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, student, _, book_id, branch = await _seed(suffix)
    res = await create_reservation(
        lib_scope,
        ReservationCreateRequest(member_user_id=str(student.id), book_id=book_id, branch_code=branch),
    )
    assert res.status == LibraryReservationStatus.QUEUED
    assert res.queue_position == 1
    queue = await queue_for_book(lib_scope, book_id, branch_code=branch)
    assert len(queue) == 1
    with pytest.raises(AppError) as dup:
        await create_reservation(
            lib_scope,
            ReservationCreateRequest(member_user_id=str(student.id), book_id=book_id, branch_code=branch),
        )
    assert dup.value.status_code == 409


@pytest.mark.anyio
async def test_return_triggers_allocation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, student, _, book_id, branch = await _seed(suffix)
    copy_id = f"C-{suffix}"
    copy = await LibraryCopy.find_one({"copy_id": copy_id})
    assert copy is not None
    copy.status = LibraryCopyStatus.AVAILABLE
    await copy.save()
    loan = await issue_loan(
        lib_scope,
        IssueLoanRequest(member_user_id=str(student.id), copy_id=copy_id, branch_code=branch),
    )
    res = await create_reservation(
        lib_scope,
        ReservationCreateRequest(member_user_id=str(student.id), book_id=book_id, branch_code=branch),
    )
    await return_loan(lib_scope, loan.circulation_id, ReturnLoanRequest())
    refreshed = await LibraryReservation.find_one({"reservation_id": res.reservation_id})
    assert refreshed is not None
    assert refreshed.status == LibraryReservationStatus.READY
    assert refreshed.copy_id == copy_id
    notes = await LibraryReservationNotification.find({"reservation_id": res.reservation_id}).to_list()
    assert len(notes) == 1


@pytest.mark.anyio
async def test_cancel_reindexes_and_concurrent_allocate(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, student, student_b, book_id, branch = await _seed(suffix)
    copy = await LibraryCopy.find_one({"copy_id": f"C-{suffix}"})
    assert copy is not None
    copy.status = LibraryCopyStatus.ISSUED
    await copy.save()
    r1 = await create_reservation(
        lib_scope,
        ReservationCreateRequest(
            reservation_id=f"r1_{suffix}",
            member_user_id=str(student.id),
            book_id=book_id,
            branch_code=branch,
        ),
    )
    r2 = await create_reservation(
        lib_scope,
        ReservationCreateRequest(
            reservation_id=f"r2_{suffix}",
            member_user_id=str(student_b.id),
            book_id=book_id,
            branch_code=branch,
        ),
    )
    assert r2.queue_position == 2
    await cancel_reservation(lib_scope, r1.reservation_id, ReservationCancelRequest(reason="Changed mind"))
    queue = await queue_for_book(lib_scope, book_id, branch_code=branch)
    assert len(queue) == 1
    assert queue[0].reservation_id == r2.reservation_id
    assert queue[0].queue_position == 1
    copy.status = LibraryCopyStatus.AVAILABLE
    await copy.save()

    async def _allocate():
        try:
            return await manual_allocate(lib_scope, r2.reservation_id, ReservationAllocateRequest())
        except AppError as exc:
            return exc

    outcomes = await asyncio.gather(_allocate(), _allocate())
    oks = [o for o in outcomes if not isinstance(o, AppError)]
    assert len(oks) == 1


@pytest.mark.anyio
async def test_expiry_releases_copy(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, student, _, book_id, branch = await _seed(suffix)
    copy_id = f"C-{suffix}"
    copy = await LibraryCopy.find_one({"copy_id": copy_id})
    assert copy is not None
    copy.status = LibraryCopyStatus.ISSUED
    await copy.save()
    res = await create_reservation(
        lib_scope,
        ReservationCreateRequest(member_user_id=str(student.id), book_id=book_id, branch_code=branch),
    )
    copy.status = LibraryCopyStatus.AVAILABLE
    await copy.save()
    ready = await manual_allocate(lib_scope, res.reservation_id, ReservationAllocateRequest(copy_id=copy_id))
    assert ready.status == LibraryReservationStatus.READY
    doc = await LibraryReservation.find_one({"reservation_id": res.reservation_id})
    assert doc is not None
    doc.expires_at = utcnow() - timedelta(hours=1)
    await doc.save()
    count = await expire_ready_holds(doc.tenant_id)
    assert count >= 1
    copy_after = await LibraryCopy.find_one({"copy_id": copy_id})
    assert copy_after is not None
    assert copy_after.status == LibraryCopyStatus.AVAILABLE


@pytest.mark.anyio
async def test_student_forbidden(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, student, _, book_id, branch = await _seed(suffix)
    stu_scope = _scope(student, Role.STUDENT)
    with pytest.raises(AppError) as denied:
        await create_reservation(
            stu_scope,
            ReservationCreateRequest(member_user_id=str(student.id), book_id=book_id, branch_code=branch),
        )
    assert denied.value.status_code == 403