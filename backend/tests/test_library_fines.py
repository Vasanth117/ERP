"""Library fines, finance verification and approvals."""

from datetime import date, timedelta
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
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.library_admin_schemas import BookCopyCreate, CatalogueCreate
from app.modules.college_admin.library_admin_service import add_book_copy, upsert_catalogue
from app.modules.finance.finance_enums import PaymentTransactionStatus
from app.modules.finance.finance_models import PaymentTransaction
from app.modules.library.circulation_enums import ReturnDisposition
from app.modules.library.circulation_schemas import IssueLoanRequest, ReturnLoanRequest
from app.modules.library.circulation_service import issue_loan, return_loan
from app.modules.library.fine_calculation import overdue_fine_amount
from app.modules.library.fine_enums import LibraryFineApprovalType
from app.modules.library.fine_schemas import FineApprovalDecision, FinePaymentVerifyRequest, FinePolicyUpsert, FineWaiverRequest
from app.modules.library.fine_service import (
    create_finance_demand,
    decide_approval,
    get_fine,
    request_waiver,
    upsert_fine_policy,
    verify_fine_payment,
)
from app.modules.library.library_enums import LibraryFineStatus
from app.modules.library.library_models import LibraryFine
from app.modules.library.member_schemas import MemberRegisterRequest
from app.modules.library.member_service import register_member
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


async def _seed_fines(suffix: str) -> tuple[AccessScope, AccessScope, User, str, str]:
    tenant = Tenant(name=f"Fine {suffix}", code=f"fine_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+fine+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"lib+fine+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Librarian",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"stu+fine+{suffix}@example.com",
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
    await create_branch_facility(admin_scope, LibraryBranchCreate(library_code=lib_code, branch_code=branch, name="Main"))
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
    copy_id = f"C-{suffix}"
    await upsert_catalogue(admin_scope, CatalogueCreate(book_id=book_id, title="Book", category="SCI"))
    await add_book_copy(admin_scope, BookCopyCreate(copy_id=copy_id, book_id=book_id, barcode=f"BC-{suffix}", branch_code=branch))
    await register_member(lib_scope, MemberRegisterRequest(member_user_id=str(student.id), branch_code=branch))
    await upsert_fine_policy(lib_scope, FinePolicyUpsert(branch_code=branch, fine_per_day=10, grace_days=0, lost_book_charge=250))
    return admin_scope, lib_scope, student, copy_id, branch


@pytest.mark.anyio
async def test_overdue_calculation_on_return(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, lib_scope, student, copy_id, branch = await _seed_fines(suffix)
    loan = await issue_loan(lib_scope, IssueLoanRequest(member_user_id=str(student.id), copy_id=copy_id, branch_code=branch))
    from app.modules.library.library_models import LibraryCirculation

    circ = await LibraryCirculation.find_one({"circulation_id": loan.circulation_id})
    assert circ is not None
    circ.due_at = date.today() - timedelta(days=3)
    await circ.save()
    days, amt = overdue_fine_amount(due_at=circ.due_at, fine_per_day=10, grace_days=0)
    assert days == 3
    assert amt == 30
    await return_loan(lib_scope, loan.circulation_id, ReturnLoanRequest())
    fines = await LibraryFine.find({"circulation_id": loan.circulation_id, "fine_type": "overdue"}).to_list()
    assert len(fines) == 1
    assert fines[0].amount >= 0


@pytest.mark.anyio
async def test_verified_payment_and_failed(db_ready) -> None:
    suffix = uuid4().hex[:8]
    admin_scope, lib_scope, student, copy_id, branch = await _seed_fines(suffix)
    fine_id = f"fine_{suffix}"
    await LibraryFine(
        tenant_id=student.tenant_id,
        fine_id=fine_id,
        student_user_id=student.id,
        amount=50,
        balance=50,
        reason="Test",
        status=LibraryFineStatus.OPEN,
        branch_code=branch,
    ).insert()
    with_demand = await create_finance_demand(lib_scope, fine_id)
    assert with_demand.demand_id
    await PaymentTransaction(
        tenant_id=student.tenant_id,
        student_user_id=student.id,
        transaction_id=f"pay_{suffix}",
        idempotency_key=f"idem_{suffix}",
        demand_id=with_demand.demand_id,
        amount=50,
        status=PaymentTransactionStatus.SUCCESS,
        webhook_verified=True,
    ).insert()
    paid = await verify_fine_payment(lib_scope, fine_id, FinePaymentVerifyRequest(transaction_id=f"pay_{suffix}"))
    assert paid.status == LibraryFineStatus.PAID
    with pytest.raises(AppError) as fail:
        await verify_fine_payment(
            lib_scope,
            fine_id,
            FinePaymentVerifyRequest(transaction_id=f"pay_fail_{suffix}"),
        )
    assert fail.value.status_code in (404, 409)


@pytest.mark.anyio
async def test_waiver_separation_of_duties(db_ready) -> None:
    suffix = uuid4().hex[:8]
    admin_scope, lib_scope, student, _, branch = await _seed_fines(suffix)
    fine_id = f"fine_w_{suffix}"
    await LibraryFine(
        tenant_id=student.tenant_id,
        fine_id=fine_id,
        student_user_id=student.id,
        amount=20,
        balance=20,
        reason="Test",
        status=LibraryFineStatus.OPEN,
        branch_code=branch,
    ).insert()
    await request_waiver(
        lib_scope,
        fine_id,
        FineWaiverRequest(reason="Compassionate"),
        approval_type=LibraryFineApprovalType.WAIVER,
    )
    with pytest.raises(AppError) as self_appr:
        await decide_approval(lib_scope, fine_id, FineApprovalDecision(approved=True))
    assert self_appr.value.status_code == 403
    approved = await decide_approval(admin_scope, fine_id, FineApprovalDecision(approved=True, note="ok"))
    assert approved.status == LibraryFineStatus.WAIVED


@pytest.mark.anyio
async def test_lost_return_creates_damage_fine(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, lib_scope, student, copy_id, branch = await _seed_fines(suffix)
    loan = await issue_loan(lib_scope, IssueLoanRequest(member_user_id=str(student.id), copy_id=copy_id, branch_code=branch))
    await return_loan(lib_scope, loan.circulation_id, ReturnLoanRequest(disposition=ReturnDisposition.LOST))
    fine = await LibraryFine.find_one({"circulation_id": loan.circulation_id, "fine_type": "lost"})
    assert fine is not None
    assert fine.amount == 250


@pytest.mark.anyio
async def test_cross_tenant_isolation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    lib_scope, _, _, _, _ = await _seed_fines(suffix)
    other = Tenant(name=f"O {suffix}", code=f"o_{suffix}")
    await other.insert()
    lib_b = User(
        email=f"libb+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="L2",
        role=Role.LIBRARIAN,
        tenant_id=other.id,
    )
    await lib_b.insert()
    with pytest.raises(AppError):
        await get_fine(_scope(lib_b, Role.LIBRARIAN), f"fine_{suffix}")