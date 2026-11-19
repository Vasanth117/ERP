"""Library settings and borrowing policies."""

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
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.library_admin_schemas import BookCopyCreate, CatalogueCreate
from app.modules.college_admin.library_admin_service import add_book_copy, upsert_catalogue
from app.modules.library.circulation_schemas import IssueLoanRequest
from app.modules.library.circulation_service import issue_loan, renew_loan
from app.modules.library.facility_enums import LibraryStaffRole
from app.modules.library.facility_schemas import InstitutionLibraryCreate, LibraryBranchCreate, LibraryStaffAssignmentCreate
from app.modules.library.facility_service import create_branch_facility, create_library, create_staff_assignment
from app.modules.library.library_models import LibraryCirculation
from app.modules.library.member_enums import LibraryMemberCategory
from app.modules.library.member_schemas import MemberRegisterRequest
from app.modules.library.member_service import register_member
from app.modules.library.policy_evaluation import resolve_borrowing_policy
from app.modules.library.settings_enums import LibraryPolicyStatus
from app.modules.library.settings_models import LibraryBorrowingRule
from app.modules.library.settings_schemas import BorrowingRuleCreate
from app.modules.library.settings_service import (
    activate_borrowing_rule,
    create_borrowing_rule,
    preview_effective_policy,
    retire_borrowing_rule,
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


async def _seed(suffix: str) -> tuple[AccessScope, AccessScope, User, User, str, str]:
    tenant = Tenant(name=f"Pol {suffix}", code=f"pol_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+pol+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"lib+pol+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Lib",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"stu+pol+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Stu",
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
    lib_code = f"L{suffix}".upper()[:12]
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
    await upsert_catalogue(admin_scope, CatalogueCreate(book_id=book_id, title="Policy Book", category="SCI"))
    copy_id = f"CP-{suffix}"
    await add_book_copy(admin_scope, BookCopyCreate(copy_id=copy_id, book_id=book_id, barcode=f"BC-{suffix}", branch_code=branch))
    await register_member(lib_scope, MemberRegisterRequest(member_user_id=str(student.id), member_category=LibraryMemberCategory.STUDENT))
    return admin_scope, lib_scope, librarian, student, copy_id, branch


@pytest.mark.anyio
async def test_policy_precedence_and_effective_dates(db_ready) -> None:
    suffix = uuid4().hex[:8]
    admin_scope, lib_scope, _, _, _, branch = await _seed(suffix)
    base = await create_borrowing_rule(
        lib_scope,
        BorrowingRuleCreate(branch_code=branch, loan_days=7, max_books=3, effective_from=date.today() - timedelta(days=1)),
    )
    await activate_borrowing_rule(admin_scope, base.policy_id)
    student_rule = await create_borrowing_rule(
        lib_scope,
        BorrowingRuleCreate(
            branch_code=branch,
            member_category="student",
            loan_days=21,
            max_books=10,
            effective_from=date.today(),
        ),
    )
    await activate_borrowing_rule(admin_scope, student_rule.policy_id)
    snap = await resolve_borrowing_policy(
        admin_scope.tenant_id,
        branch_code=branch,
        member_category="student",
    )
    assert snap.loan_days == 21
    retired = await LibraryBorrowingRule.find_one({"policy_id": student_rule.policy_id})
    assert retired and retired.status == LibraryPolicyStatus.ACTIVE.value
    await retire_borrowing_rule(lib_scope, student_rule.policy_id)
    snap2 = await resolve_borrowing_policy(admin_scope.tenant_id, branch_code=branch, member_category="student")
    assert snap2.loan_days == 7


@pytest.mark.anyio
async def test_loan_snapshot_preserves_rules_on_renew(db_ready) -> None:
    suffix = uuid4().hex[:8]
    admin_scope, lib_scope, _, student, copy_id, branch = await _seed(suffix)
    rule = await create_borrowing_rule(
        lib_scope,
        BorrowingRuleCreate(branch_code=branch, loan_days=5, renewal_limit=1, effective_from=date.today()),
    )
    await activate_borrowing_rule(admin_scope, rule.policy_id)
    loan = await issue_loan(lib_scope, IssueLoanRequest(member_user_id=str(student.id), copy_id=copy_id, branch_code=branch))
    circ = await LibraryCirculation.find_one({"circulation_id": loan.circulation_id})
    assert circ and circ.applied_policy_snapshot.get("loan_days") == 5
    await renew_loan(lib_scope, loan.circulation_id)
    newer = await create_borrowing_rule(
        lib_scope,
        BorrowingRuleCreate(branch_code=branch, loan_days=30, renewal_limit=5, effective_from=date.today()),
    )
    await activate_borrowing_rule(admin_scope, newer.policy_id)
    snap_after = await resolve_borrowing_policy(admin_scope.tenant_id, branch_code=branch, member_category="student")
    assert snap_after.loan_days == 30
    circ2 = await LibraryCirculation.find_one({"circulation_id": loan.circulation_id})
    assert circ2 and circ2.applied_policy_snapshot.get("loan_days") == 5
    assert circ2.renewal_count == 1


@pytest.mark.anyio
async def test_unauthorized_policy_modify(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, lib_scope, _, _, _, branch = await _seed(suffix)
    student_scope = AccessScope(
        role=Role.STUDENT,
        user_id=lib_scope.user_id,
        tenant_id=lib_scope.tenant_id,
        department_id=None,
        effective_permissions=frozenset({Permission.STUDENT_LIBRARY_READ}),
    )
    with pytest.raises(AppError) as denied:
        await create_borrowing_rule(student_scope, BorrowingRuleCreate(branch_code=branch, loan_days=3))
    assert denied.value.status_code == 403
    prev = await preview_effective_policy(lib_scope, branch_code=branch, member_category="student", resource_type="physical")
    assert prev.snapshot["loan_days"] >= 1