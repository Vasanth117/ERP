"""Library circulation issue, return, renew."""

import asyncio
from datetime import date, timedelta
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
from app.modules.college_admin.library_admin_models import LibraryBorrowingPolicy
from app.modules.college_admin.library_admin_schemas import BookCopyCreate, CatalogueCreate
from app.modules.college_admin.library_admin_service import add_book_copy, upsert_catalogue
from app.modules.library.facility_enums import LibraryStaffRole
from app.modules.library.facility_schemas import InstitutionLibraryCreate, LibraryBranchCreate, LibraryStaffAssignmentCreate
from app.modules.library.facility_service import create_branch_facility, create_library, create_staff_assignment
from app.modules.library.circulation_enums import ReturnDisposition
from app.modules.library.circulation_schemas import IssueLoanRequest, ReturnLoanRequest
from app.modules.library.circulation_service import get_loan, issue_loan, renew_loan, return_loan
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryCopyStatus
from app.modules.library.library_models import LibraryCopy
from app.modules.library.member_schemas import MemberRegisterRequest
from app.modules.library.member_service import get_member_by_user, register_member, suspend_member
from app.modules.library.member_schemas import MemberSuspendRequest
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.tenants.models import Tenant
from app.modules.auth.models import User


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


async def _seed_circulation(
    suffix: str, *, max_books: int = 5
) -> tuple[AccessScope, AccessScope, User, str, str, str]:
    tenant = Tenant(name=f"Circ {suffix}", code=f"circ_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+circ+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"lib+circ+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Librarian",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"stu+circ+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await librarian.insert()
    await student.insert()
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
    await create_branch_facility(
        admin_scope,
        LibraryBranchCreate(library_code=lib_code, branch_code=branch, name="Main"),
    )
    await create_staff_assignment(
        admin_scope,
        LibraryStaffAssignmentCreate(
            assignment_id=f"asg_{suffix}",
            library_code=lib_code,
            branch_code=branch,
            employee_user_id=str(librarian.id),
            staff_role=LibraryStaffRole.CIRCULATION_DESK,
            assigned_on=date.today(),
        ),
    )
    book_id = f"B-{suffix}"
    await upsert_catalogue(admin_scope, CatalogueCreate(book_id=book_id, title="Physics", category="SCI"))
    copy_a = f"C-{suffix}-A"
    copy_b = f"C-{suffix}-B"
    await add_book_copy(
        admin_scope,
        BookCopyCreate(copy_id=copy_a, book_id=book_id, barcode=f"BC-{suffix}-A", branch_code=branch),
    )
    await add_book_copy(
        admin_scope,
        BookCopyCreate(copy_id=copy_b, book_id=book_id, barcode=f"BC-{suffix}-B", branch_code=branch),
    )
    await LibraryBorrowingPolicy(
        tenant_id=tenant.id,
        branch_code=branch,
        max_books=max_books,
        loan_days=7,
        renewal_limit=1,
    ).insert()
    await register_member(lib_scope, MemberRegisterRequest(member_user_id=str(student.id), branch_code=branch))
    return lib_scope, admin_scope, student, copy_a, copy_b, branch


@pytest.mark.anyio
async def test_issue_return_renew_cycle(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, student, copy_a, _, branch = await _seed_circulation(suffix)
    loan = await issue_loan(
        lib_scope,
        IssueLoanRequest(member_user_id=str(student.id), copy_id=copy_a, branch_code=branch),
    )
    assert loan.status == LibraryCirculationStatus.ACTIVE
    assert loan.due_at >= date.today()
    copy = await LibraryCopy.find_one({"copy_id": copy_a})
    assert copy is not None
    assert copy.status == LibraryCopyStatus.ISSUED

    renewed = await renew_loan(lib_scope, loan.circulation_id)
    assert renewed.renewal_count == 1
    assert renewed.due_at >= loan.due_at

    returned = await return_loan(lib_scope, loan.circulation_id, ReturnLoanRequest())
    assert returned.status == LibraryCirculationStatus.RETURNED
    copy = await LibraryCopy.find_one({"copy_id": copy_a})
    assert copy is not None
    assert copy.status == LibraryCopyStatus.AVAILABLE


@pytest.mark.anyio
async def test_ineligible_member_and_borrow_limit(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, student, copy_a, copy_b, branch = await _seed_circulation(suffix, max_books=1)
    first = await issue_loan(lib_scope, IssueLoanRequest(member_user_id=str(student.id), copy_id=copy_a, branch_code=branch))
    assert first.circulation_id
    with pytest.raises(AppError) as limit_exc:
        await issue_loan(lib_scope, IssueLoanRequest(member_user_id=str(student.id), copy_id=copy_b, branch_code=branch))
    assert limit_exc.value.status_code == 409

    lib_scope2, _, student2, copy_a2, _, branch2 = await _seed_circulation(uuid4().hex[:8], max_books=5)
    mem = await get_member_by_user(lib_scope2, str(student2.id))
    await suspend_member(lib_scope2, mem.membership_number, MemberSuspendRequest(reason="Suspended"))
    with pytest.raises(AppError) as susp:
        await issue_loan(lib_scope2, IssueLoanRequest(member_user_id=str(student2.id), copy_id=copy_a2, branch_code=branch2))
    assert susp.value.status_code == 403


@pytest.mark.anyio
async def test_concurrent_issue_same_copy(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, student, copy_a, _, branch = await _seed_circulation(suffix)
    student_b = User(
        email=f"stu2+circ+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student Two",
        role=Role.STUDENT,
        tenant_id=student.tenant_id,
    )
    await student_b.insert()
    await register_member(lib_scope, MemberRegisterRequest(member_user_id=str(student_b.id), branch_code=branch))

    async def _try_issue(uid: str):
        try:
            return await issue_loan(
                lib_scope,
                IssueLoanRequest(member_user_id=uid, copy_id=copy_a, branch_code=branch),
            )
        except AppError as exc:
            return exc

    outcomes = await asyncio.gather(_try_issue(str(student.id)), _try_issue(str(student_b.id)))
    successes = [o for o in outcomes if not isinstance(o, AppError)]
    conflicts = [o for o in outcomes if isinstance(o, AppError)]
    assert len(successes) == 1
    assert len(conflicts) == 1
    assert conflicts[0].status_code == 409


@pytest.mark.anyio
async def test_return_damaged_and_overdue_status(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, student, copy_a, _, branch = await _seed_circulation(suffix)
    loan = await issue_loan(
        lib_scope,
        IssueLoanRequest(member_user_id=str(student.id), copy_id=copy_a, branch_code=branch),
    )
    from app.modules.library.library_models import LibraryCirculation

    circ = await LibraryCirculation.find_one({"circulation_id": loan.circulation_id})
    assert circ is not None
    circ.due_at = date.today() - timedelta(days=3)
    await circ.save()
    refreshed = await get_loan(lib_scope, loan.circulation_id)
    assert refreshed.status == LibraryCirculationStatus.OVERDUE

    await return_loan(
        lib_scope,
        loan.circulation_id,
        ReturnLoanRequest(disposition=ReturnDisposition.DAMAGED),
    )
    copy = await LibraryCopy.find_one({"copy_id": copy_a})
    assert copy is not None
    assert copy.status == LibraryCopyStatus.DAMAGED


@pytest.mark.anyio
async def test_student_forbidden(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, student, copy_a, _, branch = await _seed_circulation(suffix)
    student_scope = _scope(student, Role.STUDENT)
    with pytest.raises(AppError) as denied:
        await issue_loan(
            student_scope,
            IssueLoanRequest(member_user_id=str(student.id), copy_id=copy_a, branch_code=branch),
        )
    assert denied.value.status_code == 403