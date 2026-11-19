"""HR staff portal phase 5 — attendance schedules and salary structure."""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from beanie.odm.operators.find.comparison import Eq

from app.authorization.permissions import permissions_for_role
from app.common.access import AccessScope
from app.common.roles import Role
from app.core.database import close_mongo, connect_to_mongo, document_models
from app.core.security import hash_password
from app.modules.auth.models import User
from app.modules.college_admin.faculty_admin_models import EmployeeRecord
from app.modules.college_admin.models import InstitutionCampus
from app.modules.hr.attendance_schedule_schemas import (
    AttendanceCorrectionCreate,
    AttendanceCorrectionReview,
    AttendanceEventIngest,
    MonthlyAttendanceAction,
    RosterAssign,
    ShiftUpsert,
    WorkScheduleUpsert,
)
from app.modules.hr.attendance_schedule_service import (
    approve_shift_swap,
    assign_roster,
    ingest_attendance_event,
    lock_monthly_attendance,
    request_shift_swap,
    review_attendance_correction,
    submit_attendance_correction,
    upsert_shift,
    upsert_work_schedule,
)
from app.modules.hr.employee_profile_schemas import EmployeeRegister
from app.modules.hr.employee_profile_service import register_employee
from app.modules.hr.enums import (
    EmployeeAttendanceDayStatus,
    HrAttendanceEventSource,
    HrAttendanceEventType,
    HrSalaryComponentCategory,
    HrSalaryCalcType,
)
from app.modules.hr.salary_calculation import calculate_structure
from app.modules.hr.salary_structure_schemas import SalaryAssignmentCreate, SalaryComponentUpsert, SalaryRevisionCreate, SalaryTemplateUpsert
from app.modules.hr.salary_structure_service import (
    activate_salary_assignment,
    create_salary_assignment,
    create_salary_revision,
    review_salary_revision,
    upsert_salary_component,
    upsert_salary_template,
)
from app.modules.hr.salary_structure_schemas import SalaryRevisionReview
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


async def _seed(suffix: str):
    tenant = Tenant(name=f"HR5 {suffix}", code=f"hr5_{suffix}")
    await tenant.insert()
    dept = Department(tenant_id=tenant.id, name="Admin", code=f"ADM-{suffix}")
    await dept.insert()
    campus = InstitutionCampus(tenant_id=tenant.id, campus_code=f"C{suffix}", name="Main", is_main=True)
    await campus.insert()
    hr_user = User(
        email=f"hr5+{suffix}@example.com",
        hashed_password=hash_password("password1234567890"),
        full_name="HR Staff",
        role=Role.HR_STAFF,
        tenant_id=tenant.id,
    )
    await hr_user.insert()
    scope = _scope(hr_user, Role.HR_STAFF)
    profile = await register_employee(
        scope,
        EmployeeRegister(
            employee_code=f"EMP-{suffix}",
            first_name="Tina",
            last_name="Rao",
            official_email=f"tina.{suffix}@example.com",
            password="password1234567890",
            mobile_number="9000000010",
            joining_date=date.today() - timedelta(days=90),
            employee_category="administrative",
            employment_type="full_time",
            department_id=str(dept.id),
            designation="Coordinator",
            campus_id=str(campus.id),
        ),
    )
    employee = await EmployeeRecord.find_one(Eq(EmployeeRecord.employee_id, profile.employee_code))
    assert employee is not None
    return tenant, scope, employee, dept


@pytest.mark.asyncio
async def test_attendance_overnight_shift_and_idempotent_events(db_ready):
    suffix = uuid4().hex[:8]
    _, scope, employee, _ = await _seed(suffix)
    await upsert_work_schedule(
        scope,
        WorkScheduleUpsert(
            schedule_code=f"STD-{suffix}",
            title="Standard",
            start_time=time(9, 0),
            end_time=time(18, 0),
            effective_from=date.today() - timedelta(days=30),
        ),
    )
    night = await upsert_shift(
        scope,
        ShiftUpsert(
            shift_code=f"NIGHT-{suffix}",
            title="Night",
            start_time=time(22, 0),
            end_time=time(6, 0),
            crosses_midnight=True,
            expected_hours=8,
        ),
    )
    work_day = date.today()
    roster = await assign_roster(
        scope,
        RosterAssign(
            employee_user_id=str(employee.user_id),
            shift_id=night.id,
            roster_date=work_day,
        ),
    )
    check_in = datetime.combine(work_day, time(22, 5), tzinfo=timezone.utc)
    check_out = datetime.combine(work_day + timedelta(days=1), time(6, 0), tzinfo=timezone.utc)
    record = await ingest_attendance_event(
        scope,
        AttendanceEventIngest(
            employee_user_id=str(employee.user_id),
            event_type=HrAttendanceEventType.CHECK_IN,
            event_at=check_in,
            source=HrAttendanceEventSource.MANUAL_HR,
            idempotency_key=f"evt:in:{suffix}",
        ),
    )
    dup = await ingest_attendance_event(
        scope,
        AttendanceEventIngest(
            employee_user_id=str(employee.user_id),
            event_type=HrAttendanceEventType.CHECK_IN,
            event_at=check_in,
            source=HrAttendanceEventSource.MANUAL_HR,
            idempotency_key=f"evt:in:{suffix}",
        ),
    )
    assert dup.id == record.id
    await ingest_attendance_event(
        scope,
        AttendanceEventIngest(
            employee_user_id=str(employee.user_id),
            event_type=HrAttendanceEventType.CHECK_OUT,
            event_at=check_out,
            source=HrAttendanceEventSource.MANUAL_HR,
            idempotency_key=f"evt:out:{suffix}",
        ),
    )
    corr = await submit_attendance_correction(
        scope,
        AttendanceCorrectionCreate(
            employee_user_id=str(employee.user_id),
            attendance_date=work_day,
            requested_status=EmployeeAttendanceDayStatus.PRESENT,
            reason="Forgot checkout approval",
        ),
    )
    await review_attendance_correction(scope, corr["correction_id"], AttendanceCorrectionReview(decision="manager_approve"))
    await review_attendance_correction(scope, corr["correction_id"], AttendanceCorrectionReview(decision="hr_approve", note="OK"))
    lock = await lock_monthly_attendance(scope, MonthlyAttendanceAction(period_year=work_day.year, period_month=work_day.month))
    assert lock["locked_records"] >= 1
    from app.modules.hr.attendance_schedule_schemas import ShiftSwapCreate

    swap = await request_shift_swap(scope, ShiftSwapCreate(from_assignment_id=roster.id, to_employee_user_id=str(scope.user_id), reason="Cover"))
    await approve_shift_swap(scope, swap["swap_request_id"])


@pytest.mark.asyncio
async def test_salary_decimal_revision(db_ready):
    suffix = uuid4().hex[:8]
    _, scope, employee, _ = await _seed(suffix)
    await upsert_salary_component(
        scope,
        SalaryComponentUpsert(
            component_code="basic",
            name="Basic Salary",
            category=HrSalaryComponentCategory.EARNING,
            calc_type=HrSalaryCalcType.FIXED,
            effective_from=date.today(),
        ),
    )
    template = await upsert_salary_template(
        scope,
        SalaryTemplateUpsert(
            template_code=f"TPL-{suffix}",
            title="Admin Template",
            template_kind="administrative",
            component_lines=[
                {"component_code": "basic", "category": "earning", "calc_type": "fixed"},
                {"component_code": "hra", "category": "earning", "calc_type": "percentage", "percentage_of": "basic", "percentage": "40"},
                {"component_code": "pf", "category": "deduction", "calc_type": "percentage", "percentage_of": "basic", "percentage": "12", "statutory_ref": "provident_fund"},
            ],
        ),
    )
    calc = calculate_structure(
        component_defs=[
            {"component_code": "basic", "category": "earning", "calc_type": "fixed"},
            {"component_code": "hra", "category": "earning", "calc_type": "percentage", "percentage_of": "basic", "percentage": "40"},
            {"component_code": "pf", "category": "deduction", "calc_type": "percentage", "percentage_of": "basic", "percentage": "12"},
        ],
        amounts={"basic": "50000.00"},
    )
    assert Decimal(calc["gross_salary"]) == Decimal("70000.00")
    assignment = await create_salary_assignment(
        scope,
        SalaryAssignmentCreate(
            employee_user_id=str(employee.user_id),
            template_id=template.id,
            component_amounts={"basic": "50000.00"},
            effective_from=date.today(),
        ),
    )
    from app.modules.hr.salary_structure_service import submit_salary_assignment

    pending = await submit_salary_assignment(scope, assignment.id)
    assert pending.status.value == "pending_approval"
    activated = await activate_salary_assignment(scope, assignment.id)
    assert activated.status.value == "active"
    revision = await create_salary_revision(
        scope,
        SalaryRevisionCreate(
            employee_user_id=str(employee.user_id),
            revision_type="annual_increment",
            reason="Annual increment",
            proposed_component_amounts={"basic": "55000.00"},
            effective_from=date.today() + timedelta(days=30),
            template_id=template.id,
        ),
    )
    done = await review_salary_revision(scope, revision.id, SalaryRevisionReview(decision="approve"))
    assert done.status.value == "applied"