"""Library member management tests."""

from datetime import date, timedelta
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
from app.common.time import utcnow
from app.modules.auth.models import User
from app.modules.college_admin.identity_models import InstitutionAccountStatus, InstitutionUser
from app.modules.college_admin.library_admin_schemas import LibraryBranchCreate
from app.modules.college_admin.library_admin_service import create_branch
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryFineStatus
from app.modules.library.library_models import LibraryCirculation, LibraryFine
from app.modules.library.member_enums import LibraryMemberCategory, LibraryMemberStatus
from app.modules.library.member_schemas import MemberRegisterRequest, MemberSuspendRequest, MemberUpdateRequest
from app.modules.library.member_service import (
    get_member_by_number,
    member_borrowing_summary,
    member_history,
    reactivate_member,
    register_member,
    search_members,
    suspend_member,
    update_member,
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


async def _seed(suffix: str) -> tuple[Tenant, User, AccessScope, User, AccessScope]:
    tenant = Tenant(name=f"LibMem {suffix}", code=f"lm_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+lmem+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"lib+lmem+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Librarian",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"stu+lmem+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student One",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await librarian.insert()
    await student.insert()
    admin_scope = _scope(admin, Role.COLLEGE_ADMIN)
    lib_scope = _scope(librarian, Role.LIBRARIAN)
    await create_branch(admin_scope, LibraryBranchCreate(branch_code="MAIN", name="Main"))
    await InstitutionUser(tenant_id=tenant.id, user_id=student.id, account_status=InstitutionAccountStatus.ACTIVE).insert()
    return tenant, admin, admin_scope, student, lib_scope


@pytest.mark.anyio
async def test_register_suspend_reactivate_and_history(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, admin_scope, student, lib_scope = await _seed(suffix)
    member = await register_member(
        lib_scope,
        MemberRegisterRequest(member_user_id=str(student.id), branch_code="MAIN", borrowing_limit=3),
    )
    assert member.membership_number.startswith("MEM-")
    assert member.member_category == LibraryMemberCategory.STUDENT
    assert member.borrowing_eligible is True
    assert Permission.LIBRARY_MEMBER_MANAGE in lib_scope.effective_permissions

    with pytest.raises(AppError) as dup:
        await register_member(lib_scope, MemberRegisterRequest(member_user_id=str(student.id)))
    assert dup.value.status_code == 409

    suspended = await suspend_member(lib_scope, member.membership_number, MemberSuspendRequest(reason="Policy violation"))
    assert suspended.status == LibraryMemberStatus.SUSPENDED
    assert suspended.borrowing_eligible is False

    reactivated = await reactivate_member(lib_scope, member.membership_number)
    assert reactivated.status == LibraryMemberStatus.ACTIVE
    assert reactivated.borrowing_eligible is True

    hist = await member_history(lib_scope, member.membership_number, Pagination(limit=20, offset=0))
    actions = {h.action for h in hist.items}
    assert "register" in actions
    assert "suspend" in actions
    assert "reactivate" in actions


@pytest.mark.anyio
async def test_expiry_and_update_eligibility(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, _, student, lib_scope = await _seed(suffix)
    yesterday = date.today() - timedelta(days=1)
    member = await register_member(
        lib_scope,
        MemberRegisterRequest(
            member_user_id=str(student.id),
            expires_on=yesterday,
        ),
    )
    assert member.status == LibraryMemberStatus.EXPIRED
    assert member.borrowing_eligible is False

    updated = await update_member(
        lib_scope,
        member.membership_number,
        MemberUpdateRequest(expires_on=date.today() + timedelta(days=30), eligible=True, status=LibraryMemberStatus.ACTIVE),
    )
    assert updated.status == LibraryMemberStatus.ACTIVE
    assert updated.borrowing_eligible is True


@pytest.mark.anyio
async def test_borrowing_summary_and_search(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, _, student, lib_scope = await _seed(suffix)
    member = await register_member(lib_scope, MemberRegisterRequest(member_user_id=str(student.id)))
    await LibraryCirculation(
        tenant_id=tenant.id,
        circulation_id=f"circ_{suffix}",
        student_user_id=student.id,
        book_id=f"B-{suffix}",
        copy_id=f"C-{suffix}",
        title="Book",
        issued_at=utcnow(),
        due_at=date.today() - timedelta(days=2),
        status=LibraryCirculationStatus.OVERDUE,
    ).insert()
    await LibraryFine(
        tenant_id=tenant.id,
        fine_id=f"fine_{suffix}",
        student_user_id=student.id,
        amount=10.5,
        balance=10.5,
        reason="Late",
        status=LibraryFineStatus.OPEN,
    ).insert()
    summary = await member_borrowing_summary(lib_scope, member.membership_number)
    assert summary.active_loans >= 1
    assert summary.overdue_loans >= 1
    assert summary.open_fines == 1
    assert summary.outstanding_fine_amount == 10.5

    page = await search_members(lib_scope, Pagination(limit=10, offset=0), q="Student One")
    assert page.total >= 1
    assert any(m.membership_number == member.membership_number for m in page.items)


@pytest.mark.anyio
async def test_student_forbidden_and_cross_tenant(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant_a, _, _, student_a, lib_a = await _seed(suffix)
    suffix_b = uuid4().hex[:8]
    tenant_b = Tenant(name=f"Other {suffix_b}", code=f"oth_{suffix_b}")
    await tenant_b.insert()
    student_b = User(
        email=f"stu+oth+{suffix_b}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other Student",
        role=Role.STUDENT,
        tenant_id=tenant_b.id,
    )
    await student_b.insert()
    student_scope = _scope(student_a, Role.STUDENT)
    with pytest.raises(AppError) as denied:
        await register_member(student_scope, MemberRegisterRequest(member_user_id=str(student_a.id)))
    assert denied.value.status_code == 403

    member = await register_member(lib_a, MemberRegisterRequest(member_user_id=str(student_a.id)))
    await get_member_by_number(lib_a, member.membership_number)
    lib_b = User(
        email=f"lib+oth+{suffix_b}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Other Lib",
        role=Role.LIBRARIAN,
        tenant_id=tenant_b.id,
    )
    await lib_b.insert()
    lib_b_scope = _scope(lib_b, Role.LIBRARIAN)
    with pytest.raises(AppError) as not_found:
        await get_member_by_number(lib_b_scope, member.membership_number)
    assert not_found.value.status_code == 404
    assert str(tenant_a.id) != str(tenant_b.id)