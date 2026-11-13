"""College Admin phase 6 — HR and library administration."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import Permission, permissions_for_role
from app.common.access import AccessScope
from app.common.ids import to_object_id
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.redis import close_redis, connect_redis
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.hr_admin_schemas import LeaveDecision, LeavePolicyUpsert, OnboardingCreate, PayrollConfigUpsert
from app.modules.college_admin.hr_admin_service import (
    decide_leave,
    start_onboarding,
    upsert_leave_policy,
    upsert_payroll_config,
)
from app.modules.college_admin.library_admin_models import LibraryBookCopyRecord
from app.modules.college_admin.library_admin_schemas import BookCopyCreate, CatalogueCreate, CirculationIssue, CirculationReturn, LibraryBranchCreate
from app.modules.college_admin.library_admin_service import (
    add_book_copy,
    create_branch,
    issue_book,
    return_book,
    set_membership,
    upsert_catalogue,
)
from app.modules.hr.enums import LeaveRequestStatus
from app.modules.hr.models import LeaveRequest
from app.modules.library.library_enums import LibraryCopyStatus
from app.modules.library.library_models import LibraryCopy
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


async def _seed_admin(suffix: str) -> tuple[Tenant, User, AccessScope]:
    tenant = Tenant(name=f"College P6 {suffix}", code=f"p6_{suffix}")
    await tenant.insert()
    user = User(
        email=f"admin+p6+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="College Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await user.insert()
    scope = AccessScope(
        role=Role.COLLEGE_ADMIN,
        user_id=user.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.COLLEGE_ADMIN),
    )
    return tenant, user, scope


@pytest.mark.anyio
async def test_onboarding_and_leave_approval(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    employee_user = User(
        email=f"emp+p6+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Employee",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await employee_user.insert()
    await EmployeeRecord(tenant_id=tenant.id, user_id=employee_user.id, employee_id=f"E-{suffix}").insert()
    await upsert_leave_policy(scope, LeavePolicyUpsert(leave_type="casual", annual_quota_days=12))
    await start_onboarding(scope, OnboardingCreate(user_id=str(employee_user.id), checklist=[{"item": "ID card", "done": False}]))
    leave = LeaveRequest(
        tenant_id=tenant.id,
        employee_user_id=employee_user.id,
        leave_type="casual",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=1),
        reason="Personal",
        status=LeaveRequestStatus.SUBMITTED,
    )
    await leave.insert()
    result = await decide_leave(
        scope,
        LeaveDecision(leave_request_id=str(leave.id), decision=LeaveRequestStatus.APPROVED, note="Approved"),
    )
    assert result["decision"] == "approved"
    refreshed = await LeaveRequest.get(leave.id)
    assert refreshed is not None
    assert refreshed.status == LeaveRequestStatus.APPROVED


@pytest.mark.anyio
async def test_payroll_config_hides_confidential(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, _, scope = await _seed_admin(suffix)
    read = await upsert_payroll_config(
        scope,
        PayrollConfigUpsert(config_id=f"pay_{suffix}", label="Monthly payroll"),
        confidential_config={"salary_bands": [{"grade": "A", "amount": 99999}]},
    )
    assert read.config_id == f"pay_{suffix}"
    dumped = read.model_dump()
    assert "salary" not in str(dumped).lower() or "99999" not in str(dumped)


@pytest.mark.anyio
async def test_library_circulation_and_duplicate_accession(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, scope = await _seed_admin(suffix)
    branch = f"BR-{suffix}"
    await create_branch(scope, LibraryBranchCreate(branch_code=branch, name="Main Library"))
    book_id = f"BOOK-{suffix}"
    await upsert_catalogue(scope, CatalogueCreate(book_id=book_id, title="Algorithms", authors=["CLRS"], branch_code=branch))
    copy_id = f"COPY-{suffix}"
    acc = f"ACC-{suffix}"
    await add_book_copy(
        scope,
        BookCopyCreate(copy_id=copy_id, book_id=book_id, barcode=f"BC-{suffix}", accession_number=acc, branch_code=branch),
    )
    with pytest.raises(AppError) as dup:
        await add_book_copy(
            scope,
            BookCopyCreate(copy_id=f"COPY2-{suffix}", book_id=book_id, barcode=f"BC2-{suffix}", accession_number=acc, branch_code=branch),
        )
    assert dup.value.status_code == 409
    student = User(
        email=f"libstu+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Library Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    await set_membership(scope, str(student.id), branch_code=branch, eligible=True)
    issued = await issue_book(
        scope,
        CirculationIssue(student_user_id=str(student.id), copy_id=copy_id, branch_code=branch),
    )
    copy = await LibraryCopy.find_one(Eq(LibraryCopy.tenant_id, tenant.id), Eq(LibraryCopy.copy_id, copy_id))
    assert copy is not None
    assert copy.status == LibraryCopyStatus.ISSUED
    ret = await return_book(scope, CirculationReturn(circulation_id=issued["circulation_id"]))
    assert ret["status"] == "returned"
    admin_copy = await LibraryBookCopyRecord.find_one(Eq(LibraryBookCopyRecord.tenant_id, tenant.id), Eq(LibraryBookCopyRecord.copy_id, copy_id))
    assert admin_copy is not None


@pytest.mark.anyio
async def test_hr_permission_denied(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant, _, _ = await _seed_admin(suffix)
    faculty = User(
        email=f"hrdeny+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Faculty",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await faculty.insert()
    scope = AccessScope(
        role=Role.FACULTY,
        user_id=faculty.id,
        tenant_id=tenant.id,
        department_id=None,
        effective_permissions=permissions_for_role(Role.FACULTY),
    )
    with pytest.raises(AppError) as exc:
        await upsert_leave_policy(scope, LeavePolicyUpsert(leave_type="casual", annual_quota_days=10))
    assert exc.value.status_code == 403
    assert Permission.HR_ADMIN_MANAGE not in scope.effective_permissions
