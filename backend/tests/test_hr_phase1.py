"""HR staff portal phase 1 — dashboard and employee profiles."""

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.exceptions import AppError
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord, FacultyEmploymentStatus
from app.modules.college_admin.hr_admin_models import EmployeeOffboardingRecord
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.dashboard_service import get_hr_dashboard_overview, list_dashboard_employees
from app.modules.hr.employee_profile_schemas import (
    EmployeeRegister,
    EmployeeSearchQuery,
    EmploymentStatusChange,
    ProfileVerificationDecision,
)
from app.modules.hr.employee_profile_service import (
    change_employment_status,
    decide_profile_verification,
    register_employee,
    search_employees,
)
from app.modules.hr.enums import EmployeeAttendanceDayStatus, LeaveRequestStatus, ProfileVerificationStatus
from app.modules.hr.models import LeaveRequest
from app.modules.hr.operational_models import EmployeeDayAttendance
from app.common.schemas import Pagination
from app.modules.tenants.models import Department, Tenant


@pytest.fixture
async def db_ready():
    try:
        await connect_to_mongo()
    except Exception as exc:
        pytest.skip(f"MongoDB not available: {exc}")
    for model in document_models():
        await model.get_motor_collection().delete_many({})
    yield
    await close_mongo()


def _scope(user: User, role: Role) -> AccessScope:
    return AccessScope(
        role=role,
        user_id=user.id,
        tenant_id=user.tenant_id,
        department_id=None,
        effective_permissions=permissions_for_role(role),
    )


async def _seed_hr(suffix: str) -> tuple[Tenant, User, AccessScope, Department, InstitutionCampus]:
    tenant = Tenant(name=f"HR {suffix}", code=f"hr_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="Human Resources", code=f"HR-{suffix}")
    await dept.insert()
    campus = InstitutionCampus(tenant_id=tenant.id, campus_code=f"MAIN{suffix}", name="Main Campus", is_main=True)
    await campus.insert()
    hr_user = User(
        email=f"hrstaff+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Staff",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await hr_user.insert()
    return tenant, hr_user, _scope(hr_user, Role.HR_STAFF), dept, campus


@pytest.mark.asyncio
async def test_register_employee_and_dashboard(db_ready):
    suffix = uuid4().hex[:8]
    tenant, hr_user, scope, dept, campus = await _seed_hr(suffix)
    payload = EmployeeRegister(
        employee_code=f"EMP-{suffix}",
        first_name="Ravi",
        last_name="Kumar",
        official_email=f"ravi.{suffix}@example.com",
        password="password1234567890",
        mobile_number="9876543210",
        joining_date=date.today(),
        employee_category="administrative",
        employment_type="full_time",
        employment_status=FacultyEmploymentStatus.PROBATION,
        department_id=str(dept.id),
        designation="HR Executive",
        campus_id=str(campus.id),
        current_address={
            "line1": "12 College Road",
            "city": "Chennai",
            "state": "Tamil Nadu",
            "country": "India",
            "postal_code": "600001",
        },
        addresses_same=True,
        emergency_contact={
            "name": "Priya Kumar",
            "relationship": "spouse",
            "primary_phone": "9876500000",
        },
        probation_end_date=date.today() + timedelta(days=180),
    )
    profile = await register_employee(scope, payload)
    assert profile.employee_code == f"EMP-{suffix}"
    assert profile.profile_verification_status.value == "pending_verification"
    overview = await get_hr_dashboard_overview(scope, hr_user)
    assert overview.employees.total >= 1
    assert overview.employees.probation >= 1
    page = await list_dashboard_employees(scope, "probation", Pagination(limit=20, offset=0))
    assert page.total >= 1
    assert page.items[0].employee_code == f"EMP-{suffix}"


@pytest.mark.asyncio
async def test_status_change_requires_offboarding(db_ready):
    suffix = uuid4().hex[:8]
    _, _, scope, dept, campus = await _seed_hr(suffix)
    profile = await register_employee(
        scope,
        EmployeeRegister(
            employee_code=f"EMP2-{suffix}",
            first_name="Anita",
            last_name="Shah",
            official_email=f"anita.{suffix}@example.com",
            password="password1234567890",
            mobile_number="9123456780",
            joining_date=date.today() - timedelta(days=30),
            employee_category="administrative",
            employment_type="full_time",
            department_id=str(dept.id),
            designation="Clerk",
            campus_id=str(campus.id),
        ),
    )
    with pytest.raises(AppError) as exc:
        await change_employment_status(
            scope,
            profile.profile_id,
            EmploymentStatusChange(new_status=FacultyEmploymentStatus.TERMINATED, reason="Policy violation"),
        )
    assert exc.value.status_code == 422
    employee = await EmployeeRecord.find_one({"employee_id": f"EMP2-{suffix}"})
    assert employee is not None
    await EmployeeOffboardingRecord(
        tenant_id=employee.tenant_id,
        user_id=employee.user_id,
        reason="Contract ended",
        last_working_date=date.today(),
    ).insert()
    updated = await change_employment_status(
        scope,
        profile.profile_id,
        EmploymentStatusChange(new_status=FacultyEmploymentStatus.TERMINATED, reason="Contract ended"),
    )
    assert updated.employment.employment_status == FacultyEmploymentStatus.TERMINATED


@pytest.mark.asyncio
async def test_attendance_metric_and_leave_counts(db_ready):
    suffix = uuid4().hex[:8]
    tenant, hr_user, scope, dept, campus = await _seed_hr(suffix)
    profile = await register_employee(
        scope,
        EmployeeRegister(
            employee_code=f"EMP3-{suffix}",
            first_name="Vikram",
            last_name="Nair",
            official_email=f"vikram.{suffix}@example.com",
            password="password1234567890",
            mobile_number="9000000001",
            joining_date=date.today(),
            employee_category="administrative",
            employment_type="full_time",
            department_id=str(dept.id),
            designation="Assistant",
            campus_id=str(campus.id),
        ),
    )
    employee = await EmployeeRecord.get(profile.employee_record_id)
    assert employee is not None
    await EmployeeDayAttendance(
        tenant_id=tenant.id,
        employee_user_id=employee.user_id,
        attendance_date=date.today(),
        status=EmployeeAttendanceDayStatus.PRESENT,
        department_id=dept.id,
        campus_id=campus.id,
    ).insert()
    await LeaveRequest(
        tenant_id=tenant.id,
        employee_user_id=employee.user_id,
        leave_type="casual",
        start_date=date.today() + timedelta(days=3),
        end_date=date.today() + timedelta(days=4),
        reason="Personal",
        status=LeaveRequestStatus.SUBMITTED,
    ).insert()
    overview = await get_hr_dashboard_overview(scope, hr_user)
    assert overview.attendance.present_today >= 1
    assert overview.leave.pending >= 1
    present_page = await list_dashboard_employees(scope, "present_today", Pagination(limit=20, offset=0))
    assert present_page.total >= 1


@pytest.mark.asyncio
async def test_forbidden_for_student(db_ready):
    suffix = uuid4().hex[:8]
    tenant, hr_user, scope, dept, _campus = await _seed_hr(suffix)
    student = User(
        email=f"student+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="Student",
        role=Role.STUDENT,
        tenant_id=tenant.id,
    )
    await student.insert()
    student_scope = _scope(student, Role.STUDENT)
    with pytest.raises(AppError):
        await get_hr_dashboard_overview(student_scope, student)
    await register_employee(
        scope,
        EmployeeRegister(
            employee_code=f"EMP4-{suffix}",
            first_name="Meera",
            last_name="Iyer",
            official_email=f"meera.{suffix}@example.com",
            password="password1234567890",
            mobile_number="9000000002",
            joining_date=date.today(),
            employee_category="administrative",
            employment_type="full_time",
            department_id=str(dept.id),
            designation="Officer",
        ),
    )
    with pytest.raises(AppError):
        await search_employees(student_scope, EmployeeSearchQuery(name="Meera"), Pagination(limit=10, offset=0))