"""Library reports and analytics tests."""

import base64
from datetime import date, datetime, timedelta, timezone
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
from app.modules.library.facility_enums import LibraryStaffRole
from app.modules.library.facility_schemas import InstitutionLibraryCreate, LibraryBranchCreate, LibraryStaffAssignmentCreate
from app.modules.library.facility_service import create_branch_facility, create_library, create_staff_assignment
from app.modules.library.circulation_enums import ReturnDisposition
from app.modules.library.circulation_schemas import IssueLoanRequest, ReturnLoanRequest
from app.modules.library.circulation_service import issue_loan, return_loan
from app.modules.library.library_enums import LibraryCirculationStatus, LibraryCopyStatus, LibraryFineStatus
from app.modules.library.library_models import LibraryCirculation, LibraryCopy, LibraryFine
from app.modules.library.member_schemas import MemberRegisterRequest
from app.modules.library.member_service import register_member
from app.modules.library.member_enums import LibraryMemberCategory
from app.modules.library.report_schemas import LibraryReportFilters, LibraryReportGenerateBody
from app.modules.library.report_service import (
    download_report_export,
    generate_report_export,
    get_report_snapshot,
    list_report_catalog,
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
    tenant = Tenant(name=f"Rep {suffix}", code=f"rep_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+rep+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"lib+rep+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Lib",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    student = User(
        email=f"stu+rep+{suffix}@example.com",
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
    await upsert_catalogue(admin_scope, CatalogueCreate(book_id=book_id, title="Report Book", category="Science"))
    copy_id = f"CP-{suffix}"
    await add_book_copy(
        admin_scope,
        BookCopyCreate(copy_id=copy_id, book_id=book_id, barcode=f"BC-{suffix}", branch_code=branch),
    )
    await register_member(lib_scope, MemberRegisterRequest(member_user_id=str(student.id), member_category=LibraryMemberCategory.STUDENT))
    loan = await issue_loan(lib_scope, IssueLoanRequest(member_user_id=str(student.id), copy_id=copy_id))
    await LibraryFine(
        tenant_id=tenant.id,
        fine_id=f"fine_{suffix}",
        student_user_id=student.id,
        amount=100,
        balance=100,
        reason="Test",
        status=LibraryFineStatus.OPEN,
    ).insert()
    overdue_circ = LibraryCirculation(
        tenant_id=tenant.id,
        circulation_id=f"od_{suffix}",
        student_user_id=student.id,
        book_id=book_id,
        copy_id=copy_id + "X",
        title="Overdue",
        branch_code="MAIN",
        issued_at=datetime.now(timezone.utc) - timedelta(days=20),
        due_at=date.today() - timedelta(days=5),
        status=LibraryCirculationStatus.OVERDUE,
    )
    await overdue_circ.insert()
    return admin_scope, lib_scope, librarian, student, book_id, loan.circulation_id


@pytest.mark.anyio
async def test_overview_and_popular_books_accuracy(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, lib_scope, _, _, book_id, _ = await _seed(suffix)
    overview = await get_report_snapshot(lib_scope, "overview", LibraryReportFilters())
    assert overview.totals["total_copies"] >= 1
    popular = await get_report_snapshot(
        lib_scope,
        "popular_books",
        LibraryReportFilters(date_from=date.today() - timedelta(days=1), date_to=date.today()),
    )
    assert popular.row_count >= 1
    assert any(r.get("book_id") == book_id for r in popular.rows)


@pytest.mark.anyio
async def test_branch_filter_and_overdue(db_ready) -> None:
    suffix = uuid4().hex[:8]
    _, lib_scope, _, _, _, _ = await _seed(suffix)
    overdue = await get_report_snapshot(lib_scope, "overdue_books", LibraryReportFilters())
    assert overdue.totals["overdue_count"] >= 1
    with pytest.raises(AppError) as bad_branch:
        await get_report_snapshot(lib_scope, "overdue_books", LibraryReportFilters(branch_code="NOPE"))
    assert bad_branch.value.status_code == 422


@pytest.mark.anyio
async def test_finance_report_unauthorized_and_csv_export(db_ready) -> None:
    suffix = uuid4().hex[:8]
    admin_scope, lib_scope, librarian, _, _, _ = await _seed(suffix)
    from app.authorization.permissions import Permission

    limited = AccessScope(
        role=Role.LIBRARIAN,
        user_id=librarian.id,
        tenant_id=librarian.tenant_id,
        department_id=None,
        effective_permissions=frozenset({Permission.LIBRARY_REPORT_READ}),
    )
    with pytest.raises(AppError) as denied:
        await get_report_snapshot(limited, "fine_summary", LibraryReportFilters())
    assert denied.value.status_code == 403
    admin_data = await get_report_snapshot(admin_scope, "fine_summary", LibraryReportFilters())
    assert admin_data.row_count >= 0
    catalog = await list_report_catalog(limited)
    assert not any(c.report_type == "fine_summary" for c in catalog)
    job = await generate_report_export(
        lib_scope,
        librarian,
        LibraryReportGenerateBody(
            report_type="circulation_history",
            filters=LibraryReportFilters(),
            output_format="csv",
            idempotency_key=f"idem_{suffix}",
        ),
    )
    assert job.status == "completed"
    assert job.has_download
    dl = await download_report_export(lib_scope, librarian, job.job_id)
    assert dl.content_base64
    assert base64.b64decode(dl.content_base64).decode("utf-8").startswith("circulation_id")