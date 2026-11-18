"""Library & branch facility management tests."""

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
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.library.facility_enums import LibraryLocationLevel, LibraryStaffRole
from app.modules.library.facility_models import DayOperatingHours, OperatingSession
from app.modules.library.facility_schemas import (
    InstitutionLibraryCreate,
    LibraryBranchCreate,
    LibraryHolidayCreate,
    LibrarySectionCreate,
    LibraryShelfLocationCreate,
    LibraryStaffAssignmentCreate,
    OperatingHoursUpsert,
)
from app.modules.library.facility_service import (
    create_branch_facility,
    create_holiday,
    create_library,
    create_section,
    create_shelf_location,
    create_staff_assignment,
    get_library,
    list_configuration_history,
    upsert_operating_hours,
)
from app.modules.library.facility_validation import validate_operating_days
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


@pytest.mark.anyio
async def test_library_and_branch_lifecycle(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"LibFac {suffix}", code=f"lf_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+lf+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = _scope(admin, Role.COLLEGE_ADMIN)
    lib = await create_library(
        scope,
        InstitutionLibraryCreate(library_code=f"LIB{suffix}", name="Central Library"),
    )
    assert lib.library_code == f"LIB{suffix}".upper()
    branch = await create_branch_facility(
        scope,
        LibraryBranchCreate(library_code=lib.library_code, branch_code=f"BR{suffix}", name="Reading Hall"),
    )
    assert branch.library_code == lib.library_code
    with pytest.raises(AppError) as exc:
        await create_branch_facility(
            scope,
            LibraryBranchCreate(library_code=lib.library_code, branch_code=f"BR{suffix}", name="Duplicate"),
        )
    assert exc.value.status_code == 409
    history = await list_configuration_history(scope, Pagination(limit=20, offset=0))
    assert history.total >= 2


@pytest.mark.anyio
async def test_operating_hours_validation(db_ready) -> None:
    with pytest.raises(AppError):
        validate_operating_days(
            [
                DayOperatingHours(
                    weekday=0,
                    sessions=[OperatingSession(opens_at="10:00", closes_at="09:00")],
                )
            ]
        )
    with pytest.raises(AppError):
        validate_operating_days(
            [
                DayOperatingHours(
                    weekday=1,
                    sessions=[
                        OperatingSession(opens_at="09:00", closes_at="12:00"),
                        OperatingSession(opens_at="11:00", closes_at="15:00"),
                    ],
                )
            ]
        )


@pytest.mark.anyio
async def test_operating_hours_upsert_and_holiday(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"LibOH {suffix}", code=f"loh_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+oh+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    scope = _scope(admin, Role.COLLEGE_ADMIN)
    lib_code = f"L{suffix}"
    await create_library(scope, InstitutionLibraryCreate(library_code=lib_code, name="Main"))
    await create_branch_facility(
        scope,
        LibraryBranchCreate(library_code=lib_code, branch_code=f"B{suffix}", name="Branch A"),
    )
    hours = await upsert_operating_hours(
        scope,
        OperatingHoursUpsert(
            library_code=lib_code,
            branch_code=f"B{suffix}",
            days=[DayOperatingHours(weekday=0, sessions=[OperatingSession(opens_at="09:00", closes_at="17:00")])],
        ),
    )
    assert len(hours.days) == 1
    start = date.today()
    await create_holiday(
        scope,
        LibraryHolidayCreate(
            holiday_id=f"h_{suffix}",
            library_code=lib_code,
            branch_code=f"B{suffix}",
            start_date=start,
            end_date=start + timedelta(days=1),
            reason="Maintenance",
        ),
    )
    with pytest.raises(AppError) as exc:
        await create_holiday(
            scope,
            LibraryHolidayCreate(
                holiday_id=f"h_{suffix}",
                library_code=lib_code,
                start_date=start + timedelta(days=3),
                end_date=start,
                reason="Invalid",
            ),
        )
    assert exc.value.status_code == 422


@pytest.mark.anyio
async def test_staff_section_and_shelf_location(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"LibLoc {suffix}", code=f"ll_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+loc+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    employee_user = User(
        email=f"emp+loc+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Employee",
        role=Role.FACULTY,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await employee_user.insert()
    await EmployeeRecord(
        tenant_id=tenant.id,
        user_id=employee_user.id,
        employee_id=f"E-{suffix}",
        employment_status=FacultyEmploymentStatus.ACTIVE,
    ).insert()
    scope = _scope(admin, Role.COLLEGE_ADMIN)
    lib = f"L{suffix}"
    branch = f"B{suffix}"
    await create_library(scope, InstitutionLibraryCreate(library_code=lib, name="Central"))
    await create_branch_facility(
        scope,
        LibraryBranchCreate(library_code=lib, branch_code=branch, name="Main"),
    )
    await create_staff_assignment(
        scope,
        LibraryStaffAssignmentCreate(
            assignment_id=f"a_{suffix}",
            employee_user_id=str(employee_user.id),
            library_code=lib,
            branch_code=branch,
            staff_role=LibraryStaffRole.LIBRARIAN,
            assigned_on=date.today(),
        ),
    )
    floor = await create_shelf_location(
        scope,
        LibraryShelfLocationCreate(
            branch_code=branch,
            location_code="F1",
            level=LibraryLocationLevel.FLOOR,
            name="First Floor",
        ),
    )
    assert floor.location_code == "F1"
    with pytest.raises(AppError) as exc:
        await create_shelf_location(
            scope,
            LibraryShelfLocationCreate(
                branch_code=branch,
                location_code="S1",
                parent_location_code="F1",
                level=LibraryLocationLevel.SHELF,
                name="Invalid skip",
            ),
        )
    assert exc.value.status_code == 422
    await create_section(
        scope,
        LibrarySectionCreate(branch_code=branch, section_code="SC-FIC", name="Fiction"),
    )


@pytest.mark.anyio
async def test_librarian_branch_scoped_access(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant = Tenant(name=f"LibScope {suffix}", code=f"lsc_{suffix}")
    await tenant.insert()
    admin = User(
        email=f"admin+sc+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant.id,
    )
    librarian = User(
        email=f"lib+sc+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Librarian",
        role=Role.LIBRARIAN,
        tenant_id=tenant.id,
    )
    await admin.insert()
    await librarian.insert()
    admin_scope = _scope(admin, Role.COLLEGE_ADMIN)
    lib_scope = _scope(librarian, Role.LIBRARIAN)
    lib = f"L{suffix}"
    await create_library(admin_scope, InstitutionLibraryCreate(library_code=lib, name="Central"))
    with pytest.raises(AppError) as exc:
        await get_library(lib_scope, lib)
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_cross_tenant_isolation(db_ready) -> None:
    suffix = uuid4().hex[:8]
    tenant_a = Tenant(name=f"A {suffix}", code=f"a_{suffix}")
    tenant_b = Tenant(name=f"B {suffix}", code=f"b_{suffix}")
    await tenant_a.insert()
    await tenant_b.insert()
    admin_a = User(
        email=f"admin+a+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin A",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant_a.id,
    )
    admin_b = User(
        email=f"admin+b+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Admin B",
        role=Role.COLLEGE_ADMIN,
        tenant_id=tenant_b.id,
    )
    await admin_a.insert()
    await admin_b.insert()
    lib_code = f"LA{suffix}"
    await create_library(_scope(admin_a, Role.COLLEGE_ADMIN), InstitutionLibraryCreate(library_code=lib_code, name="A Library"))
    with pytest.raises(AppError) as exc:
        await get_library(_scope(admin_b, Role.COLLEGE_ADMIN), lib_code)
    assert exc.value.status_code == 404